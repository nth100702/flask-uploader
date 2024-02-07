from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from flask_wtf.file import FileField, MultipleFileField, FileRequired, FileAllowed
from werkzeug.utils import secure_filename
import os
import csv
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa
import logging
from datetime import datetime
from flask import redirect, request, session
import asyncio

# Filepaths
# os.path.join("uploads", "photos")
# os.path.join("uploads", "video")
# resolve path to thianhdep_submissions.csv in ./data/thianhdep_submissions.csv
data_filepath = os.path.join("data", "thianhdep_submissions.csv")
media_filepath = os.path.join("uploads")
# print(data_filepath)


def FileMaxSizeMB(max_size: int):
    def _file_max_size(form: FlaskForm, field):
        if field.data:
            for file in field.data:
                file_size = len(file.read())
                if file_size > max_size * 1024 * 1024:
                    raise ValidationError(f"File size must be less than {max_size}MB")
                file.seek(0)  # Reset file position to the beginning

    return _file_max_size


class UploadForm(FlaskForm):
    employee_id = StringField("Employee ID", validators=[DataRequired()])
    full_name = StringField("Full Name", validators=[DataRequired()])
    department = StringField("Department", validators=[DataRequired()])
    company = StringField("Company", validators=[DataRequired()])
    photos = MultipleFileField(
        "Photos",
        validators=[
            FileAllowed(["jpg", "jpeg", "png", "gif"]),
            FileMaxSizeMB(50),
            FileRequired(),
        ],
    )  # FileMaxSizeMB(5), FileRequired()
    video = FileField(
        "Video",
        validators=[
            FileAllowed(["mp4", "mov", "avi", "wmv", "flv", "mkv"]),
            FileMaxSizeMB(500),
        ],
    )  # FileMaxSizeMB(500)
    submit = SubmitField(label="Submit")


# private_key = rsa.generate_private_key(
#     public_exponent=65537,
#     key_size=2048,
# )

# public_key = private_key.public_key()

# symmetric_key = Fernet.generate_key()
# cipher_suite = Fernet(symmetric_key)

# app starts here
app = Flask(__name__)
# Set up logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Set up the secret key to encrypt the session
app.config["SECRET_KEY"] = "your_secret_key"
app.config["UPLOADED_FILES_DEST"] = "./uploads"

# handle media file uploads
async def handle_media_files(employee_id, full_name, photos, video):
    # generate timestamp: `YYMMDDHHmmss`
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    # generate directory name: `uploads/employee_id_timestamp`
    dirname = f"{employee_id}_{full_name}"
    # create directory if not exists
    media_submission = os.path.join(media_filepath, dirname)
    os.makedirs(media_submission, exist_ok=True)
    # handle photos, write to media_submission
    if photos is not None:
        await asyncio.gather(
            *(save_file(photo, media_submission, timestamp) for photo in photos)
        )
    # handle video
    if video is not None:
        # save video to media_submission with this format: `{timestamp}_{filename}`
        await save_file(video, media_submission, timestamp)


async def save_file(file, media_submission, timestamp):
    if file is not None and file.filename != "":
        filename = f"{timestamp}_{secure_filename(file.filename)}"
        file.save(os.path.join(media_submission, filename))


# Error handling
# display error message to user as an html element
"""
for each submit, create a new record in the csv file
    only latest records are valid
"""


# Check form_data input
async def submit_handler(form_data: dict):
    employee_id = form_data["employee_id"]
    full_name = form_data["full_name"]
    department = form_data["department"]
    company = form_data["company"]
    photos = form_data["photos"]
    video = form_data["video"]
    # generate timestamp for each submission
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("photos", photos)

    with open(data_filepath, "a", newline="") as file:
        writer = csv.writer(file)
        # write new record (row) to csv file
        writer.writerow([employee_id, full_name, department, company, created])

    # handle media files
    await handle_media_files(employee_id, full_name, photos, video)


"""Notes:
Current behavior: When the user uploads a file different from the allowed file types, pressing Submit will do nothing
    Expected behavior: An error message should be displayed to the user
"""


@app.route("/", methods=["GET", "POST"])
def upload_file():
    form = UploadForm()
    notif = session.pop("notif", None)
    # Since / route is both GET and POST, we need to handle each case separately
    if request.method == "POST":
        if form.validate_on_submit():
            # print('data_filepath', data_filepath)
            # print('form.data', form.data)
            asyncio.run(submit_handler(form.data))
            return redirect("/success")  # Redirect to success.html
        # error handling
        else:
            session["notif"] = form.errors
    return render_template("upload.html", form=form, notif=notif)


# /success route
@app.route("/success")
def success():
    return render_template("success.html")


if __name__ == "__main__":
    app.run(debug=True)
