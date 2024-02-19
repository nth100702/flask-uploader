import base64
from flask import Flask, make_response, render_template, g, request, session
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_migrate import Migrate

# from flask_migrate import Migrate
from ms_auth_delegated import (
    init_msal_app,
    get_auth_code_flow,
    get_auth_response,
    get_token,
)

import os, logging
# import requests
from datetime import datetime

# setup msal
confidential_client_app = init_msal_app()
auth_code_flow, auth_url = get_auth_code_flow(confidential_client_app)

# app starts here
app = Flask(__name__)
# loads configuration from config.py
app.config.from_object("config.Config")
# set up flask logging
# TO-do: setup logging, https://flask.palletsprojects.com/en/2.3.x/logging/
# log to file for audit trail
log = app.logger
logging.basicConfig(filename="app.log", level=logging.INFO)

# setup sqlalchemy
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# setup flask-session, also refers to config.py for session settings
"""
flask_session will try to create a new instance of slqalchemy (aka. session interface) => error
Solution: Pass the db instance to flask_session to use the existing db instance instead
"""
app.config["SESSION_TYPE"] = "filesystem"  # always aim for simplicity...

"""
By default, flask_session does NOT encrypt session data
    If you want to encrypt them, you need to implement yourself by manipulating flask_session SessionInterface => Unnecessary complexity...
"""
Session(
    app
)  # after this init, flask session now becomes server-side (uses session as usual)
# from helper import clear_session
# clear_session() # clear session on each app start
# continue setup msal
auth_response = get_auth_response(auth_url)  # redirects to /auth

# setup security headers
@app.before_request
def prepare_request():
    g.nonce = base64.b64encode(os.urandom(32)).decode("utf-8")

@app.after_request
def secure_flask(response):
    response.headers['Content-Security-Policy'] = f"default-src 'self'; img-src 'self' data: https://www.gemadept.com.vn/img/nav/logo.png; script-src 'self' 'nonce-{g.nonce}' https://www.gstatic.com/recaptcha/releases/yiNW3R9jkyLVP5-EEZLDzUtA/recaptcha__en.js https://www.google.com/recaptcha/api.js https://cdnjs.cloudflare.com/ajax/libs/flowbite/2.2.1/flowbite.min.js https://cdnjs.cloudflare.com/ajax/libs/dropzone/5.9.3/min/dropzone.min.js https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js; style-src 'self' https://cdnjs.cloudflare.com/ajax/libs/dropzone/5.9.3/dropzone.min.css https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css; frame-src 'self' https://www.google.com;"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.set_cookie('username', 'flask', secure=True, httponly=True, samesite='Lax')
    # cookie expires after 10 minutes
    response.set_cookie('snakes', '3', max_age=600)
    return response

# /auth
# The point of msgraph auth => get access_token
@app.route("/auth", methods=["GET"])
def auth():
    # Check if the request is coming from localhost
    if (
        request.remote_addr != "127.0.0.1"
    ):  # noted that if you're using a reverse proxy, the remote_addr will be the proxy server's IP; best practice would be configure nginx to check if a request is coming from localhost
        return "Unauthorized", 401
    # clear session on each request to /auth => acquire new one
    session.clear()
    """
    # session.clear() => clear client session & simple server session
        we're using sqlalchemy to store session data, hence we need to clear the db record instead
    """
    # if auth_response is None, get it from the request args
    if request.args.get("code") is not None:
        # webbrowser.open(auth_url)
        auth_response = request.args
        # save auth_response to flask session
        session["msgraph_auth_response"] = auth_response
    else:
        # log
        log.error("Authorization code not found")
        # response with auth error
        return make_response(
            (
                {
                    "error": "auth_error",
                    "error_description": "Authorization code not found",
                },
                400,
            )
        )

    # acquire token by auth code flow
    auth_response = session.get("msgraph_auth_response")
    # acquire token by auth code flow
    access_token = get_token(confidential_client_app, auth_code_flow, auth_response)
    # save access_token to flask session
    session["msgraph_access_token"] = access_token
    # return auth_response & access_token as a response
    return make_response(
        (
            {
                "auth_response": session.get("msgraph_auth_response"),
                "access_token": session.get("msgraph_access_token"),
            },
            200,
        )
    )


@app.route("/", methods=["GET"])
def show_upload_form():
    class EntryForm(FlaskForm):
        ma_nhan_vien = StringField("Mã nhân viên", validators=[DataRequired()])
        ho_ten = StringField("Họ tên", validators=[DataRequired()])
        don_vi = SelectField(
            "Đơn vị",
            choices=[("GMDHO", "Gemadept HO"), ("GML", "Gemalink")],
            validators=[DataRequired()],
        )
        recaptcha = RecaptchaField()

    return render_template("upload.html", form=EntryForm(), nonce=g.nonce)


@app.route("/recaptcha", methods=["GET"])
def return_recaptchakey():
    # Check if the request is coming from localhost
    if (
        request.remote_addr != "127.0.0.1"
    ):  # noted that if you're using a reverse proxy, the remote_addr will be the proxy server's IP; best practice would be configure nginx to check if a request is coming from localhost
        # log
        log.error(f"Unauthorized request to /recaptcha from {request.remote_addr}")
        return "Unauthorized", 401
    return make_response((app.config["RECAPTCHA_PRIVATE_KEY"], 200))


@app.route("/upload", methods=["POST"])
def handle_upload():
    # form data, dz
    dzfile = request.files.get("file")
    filename: str = secure_filename(dzfile.filename)
    dzuuid: str = secure_filename(request.form.get("dzuuid"))
    dzchunkindex: int = int(request.form.get("dzchunkindex"))
    dzchunksize: int = int(request.form.get("dzchunksize"))
    dztotalchunkcount: int = int(request.form.get("dztotalchunkcount"))
    dztotalfilesize: int = int(request.form.get("dztotalfilesize"))
    dzchunkbyteoffset: int = int(request.form.get("dzchunkbyteoffset"))
    submit_id_frontend: str = request.form.get("submit_id")
    # form data, inputs
    ma_nhan_vien = secure_filename(request.form.get("ma_nhan_vien"))
    ho_ten = secure_filename(request.form.get("ho_ten"))
    don_vi = secure_filename(request.form.get("don_vi"))

    """
    Flask DEV server is SYNCHRONOUS in nature
        Avoid using async operations in flask dev server => use a production server instead (gunicorn, uwsgi, etc.)
    Also it's not recommended to use asyncio in flask, as it's not designed to be used with asyncio
    """

    """
    You should validate the recaptcha response on the client side before proceeding with the file upload
        reCAPTCHA v2 tokens expire after 2 minutes. If your file upload takes longer than this, the token will be invalid by the time it's verified.
            as a result, some large files MAY NEVER BE UPLOADED due to this time limit...
    """

    """
    To avoid flask session inconsistency (each request => !same session...) => Use server-side session
        Default: flask's native session -> client-side only (web cookies)
    To use server-side session (e.g. for storing access_token), install flask-session
        Implement server-side session (data stored in server's memory via a traditional database: sql / cache db: redis, memcached)
    """
    # print("getting access token from /upload", session.get("msgraph_access_token"))
    # # Get msgraph_access_token, if not found, perform auth code flow again
    # access_token = session.get("msgraph_access_token")
    # print('access token from /upload', access_token)
    # if access_token is None:
    #     return redirect("/auth")

    from helper import (
        get_user,
        get_submit_record,
        get_file_upload,
        is_first_chunk,
        add_chunked_file,
        file_exist_check,
        save_chunk,
        reassemble_file
    )

    try:

        def prepare_submit_dir(ma_nhan_vien, don_vi, ho_ten):
            submit_dir = os.path.join(
                app.config["UPLOAD_FOLDER"],
                f"{ma_nhan_vien}-{don_vi}-{ho_ten}-{datetime.now().strftime(r'%y%m%d')}",
            )
            os.makedirs(submit_dir, exist_ok=True)
            # make temp dir to save chunks
            os.makedirs(os.path.join(submit_dir, "temp"), exist_ok=True)
            return submit_dir

        submit_dir = prepare_submit_dir(ma_nhan_vien, don_vi, ho_ten)
        user = get_user(
            {"employee_id": ma_nhan_vien, "full_name": ho_ten, "division": don_vi}
        )
        submit_record = get_submit_record(
            {"submit_id_frontend": submit_id_frontend, "submitter_id": user.id}
        )
        file_upload_query = {
            "filename": filename,
            "filepath": submit_dir,
            "total_chunks": dztotalchunkcount,
            "submit_record_id": submit_record.id,
        }

        file_upload = None  # Define and assign a default value
        # Check if this is the first chunk
        if is_first_chunk(dzuuid=dzuuid):
            # if true, check if the file_upload exists, create if not (then return the committed value)
            file_upload = get_file_upload(file_upload_query, new=True)
        else:
            # if false, get the file_upload from the database
            file_upload = get_file_upload(file_upload_query)

        """
        Save chunk (each chunk content is a dzfile in each request payload)
            chunks are located in submit_dir/temp
                temp dir will be removed once file is reassembled
            each chunk is named as {filename}_{dzchunkindex}.part
        """
        filename_noextension = os.path.splitext(filename)[0]
        chunk_filename = f"{filename_noextension}_{dzchunkindex}.part"
        # create temp dir
        temp_dir = os.path.join(submit_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        chunk_path = os.path.join(temp_dir, chunk_filename)
        """
        Before saving the chunk, better to check if it's already saved
            If chunk is already saved
                Return a success response, skip to the next chunk
            Else: continue processing the chunk
        """
        if file_exist_check(temp_dir, chunk_filename):
            log.info(f"Chunk already saved: {chunk_filename}")
            return make_response("Chunk already saved", 200)
        # First save the chunk to the server, then save the chunk metadata to the database
        # TO-DO: add retry mechanism to save_chunk, also handler for mising chunks etc.
        save_chunk(dzfile, chunk_path)
        # Save the chunk metadata to the database
        add_chunked_file(
            dzuuid=dzuuid,
            dzchunkindex=dzchunkindex,
            dzchunksize=dzchunksize,
            dztotalfilesize=dztotalfilesize,
            dztotalchunkcount=dztotalchunkcount,
            dzchunkbyteoffset=dzchunkbyteoffset,
            chunkpath=chunk_path,
            file_upload=file_upload,  # Directly associate the ChunkedFile with the FileUpload
        )
        # get current chunk count & increment the chunks received
        file_upload.chunks_received += 1

        # After saving the chunk, check if all chunks have been uploaded
        if file_upload.chunks_received == dztotalchunkcount:
            # All chunks have been uploaded, reassemble the file
            if reassemble_file(
                submit_dir=submit_dir,
                filename=filename,
                dztotalchunkcount=dztotalchunkcount,
            ):
                # update db
                file_upload.file_reassembled = True
                # keep track how many files are associated with a submit record
                submit_record.files_received += 1

        # Commit the session once, at the end
        # after all files are received, commit the session; uploading to OneDrive will be handled in a separate route
        db.session.commit()
        # Render success page & end the user's session
        return make_response(render_template("success.html"), 200)
    except Exception as e:
        # log.error(e)
        # write all errors to log
        log.error(f"Error occurred in /upload: {str(e)}")
        if FileExistsError:
            return make_response((str(e), 409))
        # if error includes this string, it's a client error
        if "Xác thực reCAPTCHA thất bại" in str(e):
            return make_response((str(e), 400))
        return make_response(
            (
                "Uh oh, lỗi server. Xin thử lại hoặc liên hệ IT tập đoàn để được hỗ trợ",
                500,
            )
        )


"""
Precepts: Separation of concerns
    2 key roles of this app: accepting file uploads from the frontend & uploading files to OneDrive via MSGraph API
Idea: Configure flask to run a scheduled task to upload files to OneDrive (once every hour)
    - This way, the frontend will not be blocked by the file upload process
    - The frontend will only be responsible for sending files to the server
    - The server will be responsible for uploading files to OneDrive
"""


@app.route("/onedrive", methods=["POST"])
def handle_onedrive_upload():
    # Upload the file to OneDrive
    # upload_smallfile_to_onedrive(
    #     file_path=os.path.join(submit_dir, filename),
    #     file_name=filename,
    #     msgraph_access_token=session.get("msgraph_access_token"),
    # )
    # Update the file upload status
    # file_upload.upload_completed = True
    # Update the submit record status
    # submit_record.all_files_uploaded = True
    return ""


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
