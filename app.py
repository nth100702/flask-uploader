from flask import Flask, make_response, render_template, redirect, request, session
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, SelectField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
from ms_auth_delegated import (
    init_msal_app,
    get_auth_code_flow,
    get_auth_response,
    get_token,
)
import os
import requests
from datetime import datetime

# setup msal
confidential_client_app = init_msal_app()
auth_code_flow, auth_url = get_auth_code_flow(confidential_client_app)

# app starts here
app = Flask(__name__)
# loads configuration from config.py
app.config.from_object("config.Config")
# set up flask logging
log = app.logger

# setup sqlalchemy
db = SQLAlchemy(app)
# migrate = Migrate(app, db)

# continue setup msal
auth_response = get_auth_response(auth_url)  # redirects to /auth

# TO-DO: Setup logging => log to file for audit trail

# /auth
# The point of msgraph auth => get access_token
@app.route("/auth", methods=["GET"])
def auth():
    # Check if the request is coming from localhost
    if (
        request.remote_addr != "127.0.0.1"
    ):  # noted that if you're using a reverse proxy, the remote_addr will be the proxy server's IP; best practice would be configure nginx to check if a request is coming from localhost
        return "Unauthorized", 401
    # if auth_response is None, get it from the request args
    if (
        session.get("msgraph_auth_response") is None
        and request.args.get("code") is not None
    ):
        # webbrowser.open(auth_url)
        auth_response = request.args
        # save auth_response to flask session
        session["msgraph_auth_response"] = auth_response

    # check if access_token is saved in flask session
    if (
        session.get("msgraph_access_token") is not None
        and session.get("msgraph_auth_response") is not None
    ):
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
    # else acquire token by auth code flow
    auth_response = session.get("msgraph_auth_response")
    # acquire token by auth code flow
    access_token = get_token(confidential_client_app, auth_code_flow, auth_response)
    # save access_token to flask session
    session["msgraph_access_token"] = access_token
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

    return render_template("upload.html", form=EntryForm())


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

    # # validate recaptcha
    def verify_recaptcha(response):
        data = {"secret": app.config["RECAPTCHA_PRIVATE_KEY"], "response": response}
        r = requests.post("https://www.google.com/recaptcha/api/siteverify", data=data)
        result = r.json()
        # print("result", result)
        if result.get("success"):
            return True
        else:
            return False

    recaptcha_response = request.form.get("g-recaptcha-response")
    if not verify_recaptcha(recaptcha_response):
        raise Exception(
            "Xác thực reCAPTCHA thất bại, vui lòng thử lại.", 400
        )  # Return a client error with status code 400

    # Get msgraph_access_token, if not found, perform auth code flow again
    access_token = session.get("msgraph_access_token")
    # print('access token from /upload', access_token)
    if access_token is None:
        return redirect("/auth")

    # Utils
    def reassemble_file(submit_dir, filename, dztotalchunkcount):
        # Reassemble the file from the chunks
        with open(os.path.join(submit_dir, filename), "wb") as output_file:
            for i in range(dztotalchunkcount):
                chunk_path = os.path.join(submit_dir, f"{filename}.part{i}")
                with open(chunk_path, "rb") as chunk_file:
                    output_file.write(chunk_file.read())
                os.remove(chunk_path)  # Delete the chunk

    def get_user(query: dict):
        user = User.query.filter_by(**query).first()
        if user is None:
            user = User(**query)
            db.session.add(user)
            db.session.commit()
            user = User.query.filter_by(**query).first()
        return user

    def get_submit_record(query: dict):
        submit_record = SubmitRecord.query.filter_by(**query).first()
        if submit_record is None:
            submit_record = SubmitRecord(**query)
            db.session.add(submit_record)
            db.session.commit()
            submit_record = SubmitRecord.query.filter_by(**query).first()
        return submit_record

    def get_file_upload(query: dict):
        try:
            file_upload = FileUpload.query.filter_by(**query).first()
            if file_upload is None:
                file_upload = FileUpload(**query)
                db.session.add(file_upload)
                db.session.commit()
                file_upload = FileUpload.query.filter_by(**query).first()
            return file_upload
        except Exception as e:
            # Handle the exception here
            print(f"Error occurred in get_file_upload: {str(e)}")
            return None

    def get_first_chunk(dzuuid):
        first_chunk = ChunkedFile.query.filter_by(dzuuid=dzuuid, dzchunksize=0).first()
        return first_chunk

    def upload_smallfile_to_onedrive(local_submit_dir: str, file_name: str):
        # prep inputs
        GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
        access_token = session.get("msgraph_access_token")
        print("access_token", access_token)
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        onedrive_data_fyi = (
            {
                "createdDateTime": "2024-02-07T02:41:10Z",
                "eTag": '"{0E451124-1D58-4399-8B0C-E93622F58CFC},1"',
                "id": "01E26M3MJECFCQ4WA5TFBYWDHJGYRPLDH4",
                "lastModifiedDateTime": "2024-02-07T02:41:10Z",
                "name": "GMD Thi Ảnh Đẹp 2024",
                "webUrl": "https://gmdcorp-my.sharepoint.com/personal/mediamod_gemadept_com_vn/Documents/GMD%20Thi%20%E1%BA%A2nh%20%C4%90%E1%BA%B9p%202024",
                "cTag": '"c:{0E451124-1D58-4399-8B0C-E93622F58CFC},0"',
                "size": 0,
                "createdBy": {
                    "user": {
                        "email": "mediamod@gemadept.com.vn",
                        "id": "fee2b48b-f942-40a7-9e8a-54d78dbd8397",
                        "displayName": "MediaMod",
                    }
                },
                "lastModifiedBy": {
                    "user": {
                        "email": "mediamod@gemadept.com.vn",
                        "id": "fee2b48b-f942-40a7-9e8a-54d78dbd8397",
                        "displayName": "MediaMod",
                    }
                },
                "parentReference": {
                    "driveType": "business",
                    "driveId": "b!BSMpwLx6u0q_b-Nt-1W-O7tis30oT8lEvvD4tylYPZ1oPotOMoVXT5wqC5MaOvrI",
                    "id": "01E26M3MN6Y2GOVW7725BZO354PWSELRRZ",
                    "name": "Documents",
                    "path": "/drive/root:",
                    "siteId": "c0292305-7abc-4abb-bf6f-e36dfb55be3b",
                },
                "fileSystemInfo": {
                    "createdDateTime": "2024-02-07T02:41:10Z",
                    "lastModifiedDateTime": "2024-02-07T02:41:10Z",
                },
                "folder": {"childCount": 0},
            },
        )
        onedrive_target_folder_id = (
            "01E26M3MJECFCQ4WA5TFBYWDHJGYRPLDH4"  # "Thi Anh Dep 2024"
        )
        onedrive_target_user_id = "fee2b48b-f942-40a7-9e8a-54d78dbd8397"  # MediaMod
        ONEDRIVE_API_ENDPOINT = f"{GRAPH_API_ENDPOINT}/users/{onedrive_target_user_id}/drive/items/{onedrive_target_folder_id}"
        # first check if folder exists, if not create it; onedrive_submit_dir = local_submit_dir
        onedrive_submit_dir = local_submit_dir
        res = requests.get(ONEDRIVE_API_ENDPOINT, headers=headers)
        print("res, get all drive items", res.json())

        with open(onedrive_submit_dir, "rb") as upload:
            media_content = upload.read()
        response = requests.put(
            f"{GRAPH_API_ENDPOINT}/users/{onedrive_target_user_id}/drive/items/{onedrive_target_folder_id}:/{file_name}:/content",
            headers=headers,
            data=media_content,
        )
        print("uploading to onedrive", response.json())
        # check if the file has been uploaded to OneDrive
        if response.status_code == 200:
            return True
        else:
            return False

    # upload large file to OneDrive

    try:
        submit_dir = os.path.join(
            app.config["UPLOAD_FOLDER"],
            f"{ma_nhan_vien}-{don_vi}-{ho_ten}-{datetime.now().strftime(r'%y%m%d')}",
        )
        os.makedirs(submit_dir, exist_ok=True)

        # Upon every request, check if the user & submit record exists in the database
        user = get_user(
            {"employee_id": ma_nhan_vien, "full_name": ho_ten, "division": don_vi}
        )
        # print("user", user)

        submit_record = get_submit_record(
            {"submit_id_frontend": submit_id_frontend, "submitter_id": user.id}
        )
        # print("submit_record", submit_record)
        # return

        file_upload_query = {
            "filename": filename,
            "filename": filename,
            "filepath": submit_dir,
            "total_chunks": dztotalchunkcount,
            "submit_record_id": submit_record.id,
        }
        # Check if this is the first chunk
        first_chunk = get_first_chunk(dzuuid=dzuuid)
        # print("first_chunk", first_chunk)
        # return
        if first_chunk is None:
            # This is the first chunk, check if the file upload exists
            # if not create a new UploadFile before saving the chunk
            get_file_upload(file_upload_query)

        # Get the file upload
        file_upload = get_file_upload(file_upload_query)
        # print("file_upload by direct query", file_upload)

        # Before saving the chunk, check if the FILE already exists
        if os.path.exists(os.path.join(submit_dir, filename)):
            raise FileExistsError(
                "Whoops! File đã tồn tại, vui lòng thử lại với file khác"
            )
        else:
            # First save the chunk to the server, then save the chunk metadata to the database
            chunk_path = os.path.join(submit_dir, f"{filename}.part{dzchunkindex}")
            dzfile.save(chunk_path)
            chunked_file = ChunkedFile(
                dzuuid=dzuuid,
                dzchunkindex=dzchunkindex,
                dzchunksize=dzchunksize,
                dztotalfilesize=dztotalfilesize,
                dztotalchunkcount=dztotalchunkcount,
                dzchunkbyteoffset=dzchunkbyteoffset,
                chunkpath=chunk_path,
                file_upload=file_upload,  # Directly associate the ChunkedFile with the FileUpload
            )
            db.session.add(chunked_file)
            # get current chunk count & increment the chunks received
            file_upload.chunks_received += 1

            # After saving the chunk, check if all chunks have been uploaded
            if file_upload.chunks_received == dztotalchunkcount:
                # All chunks have been uploaded, reassemble the file
                reassemble_file(
                    submit_dir=submit_dir,
                    filename=filename,
                    dztotalchunkcount=dztotalchunkcount,
                )
                # Upload the file to OneDrive
                upload_smallfile_to_onedrive(
                    file_path=os.path.join(submit_dir, filename),
                    file_name=filename,
                )
                # Update the file upload status
                file_upload.upload_completed = True
                # Update the submit record status
                submit_record.all_files_uploaded = True

            # Commit the session once, at the end
            db.session.commit()
            # Redirect to the success page
            return make_response(("Woohoo! File đã upload thành công!", 200))
        # return redirect("/success")

    except Exception as e:
        # log.error(e)
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


# /success route
@app.route("/success")
def success():
    return render_template("success.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
