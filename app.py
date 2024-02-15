from logging import log
from flask import Flask, config, logging, make_response, render_template
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField
from wtforms.validators import DataRequired, ValidationError
from flask_wtf.file import FileField, MultipleFileField, FileRequired, FileAllowed
from werkzeug.utils import secure_filename
import os

from flask import redirect, request, session
import asyncio
from utils import FileMaxSizeMB

# import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from wtforms import SelectField

from ms_authn import access_token

# from models import User, SubmitRecord, ChunkedFile
from datetime import datetime
from flask_migrate import Migrate

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
    __tablename__ = 'chunked_file'
    id = db.Column(db.Integer, primary_key=True)
    # dz fields
    dzuuid = db.Column(db.String(100), nullable=False) # unique ID per upload file
    dzchunkindex = db.Column(db.Integer, nullable=False) # the chunk number of the current upload
    dzchunksize = db.Column(db.Integer, nullable=False)
    dztotalfilesize = db.Column(db.Integer, nullable=False)
    dztotalchunkcount = db.Column(db.Integer, nullable=False)
    dzchunkbyteoffset = db.Column(db.Integer, nullable=False) # The place in the file this chunk starts
    # file fields
    chunkpath = db.Column(db.String(100), nullable=False)
    # others
    date_uploaded = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # foreign key
    file_upload_id = db.Column(db.Integer, db.ForeignKey("file_upload.id"), nullable=False)
    
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
    date_uploaded = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
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
    status = db.Column(db.String(100), nullable=False)
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # each submit record has one submitter
    submitter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    submitter = db.relationship("User", backref="submitter")
    # each submit record has many file uploads
    file_uploads = db.relationship("FileUpload", backref="submit_record")

    def __repr__(self):
        return f"SubmitRecord('{self.date_submitted}', '{self.status}')"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    division = db.Column(db.String(100), nullable=False)
    # autogenerated
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # each user has one or more submit records
    submit_records = db.relationship("SubmitRecord", backref="user")

    def __repr__(self):
        return f"User('{self.employee_id}', '{self.full_name}', '{self.division}')"


"""Flask routes
"""


@app.route("/", methods=["GET"])
def show_upload_form():
    page_content = {"title": ""}
    return render_template("upload.html", form=EntryForm(), page_content=page_content)


@app.route("/upload", methods=["POST"])
def handle_upload():
    dzfile = request.files.get("file")
    filename: str = secure_filename(dzfile.filename)
    dzuuid: str = secure_filename(request.form.get("dzuuid"))
    dzchunkindex: int = int(request.form.get("dzchunkindex"))
    dztotalchunkcount: int = int(request.form.get("dztotalchunkcount"))
    dzchunkbyteoffset: int = int(request.form.get("dzchunkbyteoffset"))
    submit_id: str = secure_filename(request.form.get("submit_id"))

    # form data
    ma_nhan_vien = secure_filename(request.form.get("ma_nhan_vien"))
    ho_ten = secure_filename(request.form.get("ho_ten"))
    don_vi = secure_filename(request.form.get("don_vi"))
    recaptcha = request.form.get("g-recaptcha-response")

    # # validate recaptcha
    # if not recaptcha:
    #     return "Recaptcha validation failed", 400
    
    # Utils
    def reassemble_file(filename, dztotalchunkcount):
        # Reassemble the file from the chunks
        with open(
            os.path.join(app.config["UPLOAD_FOLDER"], filename), "wb"
        ) as output_file:
            for i in range(dztotalchunkcount):
                chunk_path = os.path.join(
                    app.config["UPLOAD_FOLDER"], f"{filename}.part{i}"
                )
                with open(chunk_path, "rb") as chunk_file:
                    output_file.write(chunk_file.read())
                os.remove(chunk_path)  # Delete the chunk

    try:
        submit_dir = os.path.join(
            app.config["UPLOAD_FOLDER"], f"{ma_nhan_vien}-{don_vi}-{ho_ten}"
        )
        os.makedirs(submit_dir, exist_ok=True)

        # Upon first request, create a new submit record, and a new user if not exists
        user = User.query.filter_by(employee_id=ma_nhan_vien).first()
        if user is None:
            user = User(employee_id=ma_nhan_vien, full_name=ho_ten, division=don_vi)
            db.session.add(user)
        
        # Check if this is the first chunk
        file_upload = FileUpload.query.filter_by(filename=filename).first()
        if file_upload is None:
            # This is the first chunk, create a new FileUpload
            upload_filepath: str = os.path.join(app.config["UPLOAD_FOLDER"], submit_dir)
            file_upload = FileUpload(filename=filename, total_chunks=dztotalchunkcount, filepath=upload_filepath)
            db.session.add(file_upload)
        else:
            # This is not the first chunk, update the chunks_received count
            file_upload.chunks_received += 1

        # Save the chunk to the server
        
        chunk_path = os.path.join(submit_dir, f"{filename}.part{dzchunkindex}")
        dzfile.save(chunk_path)

        # Save the chunk metadata to the database
        chunked_file = ChunkedFile(
            dzuuid=dzuuid,
            dzchunkindex=dzchunkindex,
            dztotalfilesize=dzfile.content_length,
            dztotalchunkcount=dztotalchunkcount,
            dzchunkbyteoffset=dzchunkbyteoffset,
            chunkpath=chunk_path,
            file_upload=file_upload,  # Directly associate the ChunkedFile with the FileUpload
        )
        db.session.add(chunked_file)

        # Check if all chunks have been uploaded
        if file_upload.chunks_received == dztotalchunkcount:
            # All chunks have been uploaded, reassemble the file
            reassemble_file(filename, dztotalchunkcount)
            # Update the file upload status
            file_upload.upload_completed = True
            # Create a new submit record
            submit_record = SubmitRecord(submitter_id=ma_nhan_vien, status="Pending")
            # add submit_record_id to file_upload
            file_upload.submit_record_id = submit_record.id

            db.session.add(submit_record)

        db.session.commit()  # Commit the session once, at the end
        # Redirect to the success page
        make_response(("Chunk upload successful", 200))
        return redirect("/success")

    except Exception as e:
        log.error(e)
        return make_response(("Failed to save chunk", 500))

# /success route
@app.route("/success")
def success():
    return render_template("success.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
