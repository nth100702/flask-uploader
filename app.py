from logging import log
from flask import Flask, config, logging, make_response, render_template
from flask_wtf import FlaskForm, RecaptchaField
import requests
from wtforms import StringField
from wtforms.validators import DataRequired, ValidationError
from flask_wtf.file import FileField, MultipleFileField, FileRequired, FileAllowed
from werkzeug.utils import secure_filename
import os

from flask import redirect, request, session

# import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from wtforms import SelectField

from ms_authn import access_token

# from models import User, SubmitRecord, ChunkedFile
from datetime import datetime
from flask_migrate import Migrate


from msal import ConfidentialClientApplication

# msal_config = {
#     "auth": {
#         "tenantId": "52251bad-a823-403e-aaa4-6c40a9fd624b",
#         "userId": "43b76bad-50b0-43e2-9dec-fe4f639bf486",
#         "clientId": "61a8ce14-21ce-4e70-9384-74b4e5984a35",
#         "authority": "https://login.microsoftonline.com/52251bad-a823-403e-aaa4-6c40a9fd624b",
#         "clientSecret": "qt88Q~BkzY9UBc7CUXfLoeJEcUjz3efhoOkP5djC",
#         "redirectUri": "http://localhost:5000/auth"
#     },
#     "cache": {
#         "cacheLocation": "localStorage",
#         "storeAuthStateInCookie": True
#     }
# }

ms_graph_config = {
    "user": {
        "businessPhones": [],
        "displayName": "MediaMod",
        "givenName": "Media",
        "mail": "mediamod@gemadept.com.vn",
        "preferredLanguage": "en-US",
        "surname": "Mod",
        "userPrincipalName": "mediamod@gemadept.com.vn",
        "id": "fee2b48b-f942-40a7-9e8a-54d78dbd8397",
    }
    # msgraph_config = {
    #     "apiUrl": "https://graph.microsoft.com/v1.0",
    #     "scopes": ["https://graph.microsoft.com/.default"]
}
# GMD credentials
APPLICATION_ID = "61a8ce14-21ce-4e70-9384-74b4e5984a35"
CLIENT_SECRET = "qt88Q~BkzY9UBc7CUXfLoeJEcUjz3efhoOkP5djC"
SCOPES = ["https://graph.microsoft.com/.default"]
TENTANT_ID = "52251bad-a823-403e-aaa4-6c40a9fd624b"
REDIRECT_URI = "http://localhost:5000/auth"
user_id = "43b76bad-50b0-43e2-9dec-fe4f639bf486"
authority = f"https://login.microsoftonline.com/{TENTANT_ID}"

# Init MSAL.ConfidentialClientApplication
confidential_client_app = ConfidentialClientApplication(
    APPLICATION_ID,
    authority=authority,
    client_credential=CLIENT_SECRET,
)

auth_code_flow = confidential_client_app.initiate_auth_code_flow(
    scopes=SCOPES, redirect_uri=REDIRECT_URI
)
auth_url = auth_code_flow["auth_uri"]
# open auth_url in browser
import webbrowser

webbrowser.open(auth_url)
# redirect user to auth_url to give permission consent

# open auth_url in browser


# app starts here
app = Flask(__name__)
# loads configuration from config.py
app.config.from_object("config.Config")
# set up flask logging
log = app.logger
db = SQLAlchemy(app)
# connects app to the database
migrate = Migrate(app, db)

"""Flask-WFT web form
"""


class EntryForm(FlaskForm):
    ma_nhan_vien = StringField("Mã nhân viên", validators=[DataRequired()])
    ho_ten = StringField("Họ tên", validators=[DataRequired()])
    don_vi = SelectField(
        "Đơn vị",
        choices=[("GMDHO", "Gemadept HO"), ("GML", "Gemalink")],
        validators=[DataRequired()],
    )
    recaptcha = RecaptchaField()


"""SqlAlchemy database models
"""


class ChunkedFile(db.Model):
    __tablename__ = "chunked_file"
    id = db.Column(db.Integer, primary_key=True)
    # dz fields
    dzuuid = db.Column(db.String(100), nullable=False)  # unique ID per upload file
    dzchunkindex = db.Column(
        db.Integer, nullable=False
    )  # the chunk number of the current upload
    dzchunksize = db.Column(db.Integer, nullable=False)
    dztotalfilesize = db.Column(db.Integer, nullable=False)
    dztotalchunkcount = db.Column(db.Integer, nullable=False)
    dzchunkbyteoffset = db.Column(
        db.Integer, nullable=False
    )  # The place in the file this chunk starts
    # file fields
    chunkpath = db.Column(db.String(100), nullable=False)
    # others
    date_uploaded = db.Column(db.DateTime, nullable=False, default=datetime.now())

    # foreign key
    file_upload_id = db.Column(
        db.Integer, db.ForeignKey("file_upload.id"), nullable=False
    )

    def __repr__(self):
        return f"ChunkedFile('{self.filename}', '{self.date_uploaded}')"


class FileUpload(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    filepath = db.Column(db.String(100), nullable=False)
    # keep track of chunks
    total_chunks = db.Column(db.Integer, nullable=False)
    chunks_received = db.Column(db.Integer, default=0)
    upload_completed = db.Column(db.Boolean, default=False)
    # timestamp
    date_uploaded = db.Column(db.DateTime, nullable=False, default=datetime.now())

    # a file upload has many chunked files
    chunked_files = db.relationship("ChunkedFile", backref="file_upload")

    # each file upload belongs to a submit record
    submit_record_id = db.Column(
        db.Integer, db.ForeignKey("submit_record.id"), nullable=False
    )

    def __repr__(self):
        return f"FileUpload('{self.filename}', '{self.date_uploaded}')"


class SubmitRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submit_id_frontend = db.Column(db.String(100), nullable=False)
    all_files_uploaded = db.Column(db.Boolean, default=False)
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.now())
    # each submit record has one submitter
    submitter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # each submit record has many file uploads
    file_uploads = db.relationship("FileUpload", backref="submit_record")

    def __repr__(self):
        return f"SubmitRecord('{self.date_submitted}', '{self.all_files_uploaded}')"


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    division = db.Column(db.String(100), nullable=False)
    # autogenerated
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now())

    # each user has one or more submit records
    submit_records = db.relationship("SubmitRecord", backref="user")

    def __repr__(self):
        return f"User('{self.employee_id}', '{self.full_name}', '{self.division}')"


"""Flask routes
"""
# /auth
@app.route("/auth", methods=["GET"])
def auth():
    auth_response = request.args
    # acquire token by auth code flow
    result = confidential_client_app.acquire_token_by_auth_code_flow(
        auth_code_flow=auth_code_flow, auth_response=auth_response, scopes=SCOPES
    )
    print("result", result)
    access_token = result["access_token"]
    print("access_token", access_token)
    session["msgraph_access_token"] = access_token
    # print flask session
    print("flask session", session.get("msgraph_access_token"))
    # print("access_token", access_token)
    return redirect("/")

@app.route("/", methods=["GET"])
def show_upload_form():
    page_content = {"title": ""}
    return render_template("upload.html", form=EntryForm(), page_content=page_content)

@app.route("/upload", methods=["POST"])
def handle_upload():
    dzfile = request.files.get("file")
    print("dzfile", dzfile)
    filename: str = secure_filename(dzfile.filename)
    dzuuid: str = secure_filename(request.form.get("dzuuid"))
    dzchunkindex: int = int(request.form.get("dzchunkindex"))
    dzchunksize: int = int(request.form.get("dzchunksize"))
    dztotalchunkcount: int = int(request.form.get("dztotalchunkcount"))
    dztotalfilesize: int = int(request.form.get("dztotalfilesize"))
    dzchunkbyteoffset: int = int(request.form.get("dzchunkbyteoffset"))
    submit_id_frontend: str = request.form.get("submit_id")
    # print("submit_id_frontend", submit_id_frontend)

    # form data
    ma_nhan_vien = secure_filename(request.form.get("ma_nhan_vien"))
    ho_ten = secure_filename(request.form.get("ho_ten"))
    don_vi = secure_filename(request.form.get("don_vi"))

    # # validate recaptcha
    def verify_recaptcha(response):
        data = {"secret": app.config["RECAPTCHA_PRIVATE_KEY"], "response": response}
        r = requests.post("https://www.google.com/recaptcha/api/siteverify", data=data)
        result = r.json()
        print("result", result)
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
    print('access token from /upload', access_token)
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

    def upload_smallfile_to_onedrive(file_path, file_name):
        GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
        access_token = session.get("msgraph_access_token")
        print("access_token", access_token)
        user_id = "43b76bad-50b0-43e2-9dec-fe4f639bf486"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        onedrive_folder_data = {
            "createdDateTime": "2024-02-07T02:41:10Z",
            "eTag": "\"{0E451124-1D58-4399-8B0C-E93622F58CFC},1\"",
            "id": "01E26M3MJECFCQ4WA5TFBYWDHJGYRPLDH4",
            "lastModifiedDateTime": "2024-02-07T02:41:10Z",
            "name": "GMD Thi Ảnh Đẹp 2024",
            "webUrl": "https://gmdcorp-my.sharepoint.com/personal/mediamod_gemadept_com_vn/Documents/GMD%20Thi%20%E1%BA%A2nh%20%C4%90%E1%BA%B9p%202024",
            "cTag": "\"c:{0E451124-1D58-4399-8B0C-E93622F58CFC},0\"",
            "size": 0,
            "createdBy": {
                "user": {
                    "email": "mediamod@gemadept.com.vn",
                    "id": "fee2b48b-f942-40a7-9e8a-54d78dbd8397",
                    "displayName": "MediaMod"
                }
            },
            "lastModifiedBy": {
                "user": {
                    "email": "mediamod@gemadept.com.vn",
                    "id": "fee2b48b-f942-40a7-9e8a-54d78dbd8397",
                    "displayName": "MediaMod"
                }
            },
            "parentReference": {
                "driveType": "business",
                "driveId": "b!BSMpwLx6u0q_b-Nt-1W-O7tis30oT8lEvvD4tylYPZ1oPotOMoVXT5wqC5MaOvrI",
                "id": "01E26M3MN6Y2GOVW7725BZO354PWSELRRZ",
                "name": "Documents",
                "path": "/drive/root:",
                "siteId": "c0292305-7abc-4abb-bf6f-e36dfb55be3b"
            },
            "fileSystemInfo": {
                "createdDateTime": "2024-02-07T02:41:10Z",
                "lastModifiedDateTime": "2024-02-07T02:41:10Z"
            },
            "folder": {
                "childCount": 0
            }
        },
        with open(file_path, "rb") as upload:
            media_content = upload.read()
        response = requests.put(
            f"{GRAPH_API_ENDPOINT}/users/fee2b48b-f942-40a7-9e8a-54d78dbd8397/drive/items/01E26M3MJECFCQ4WA5TFBYWDHJGYRPLDH4:/{file_name}:/content",
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
