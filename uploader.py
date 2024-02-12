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
from utils import FileMaxSizeMB

# Filepaths
# os.path.join("uploads", "photos")
# os.path.join("uploads", "video")
# resolve path to thianhdep_submissions.csv in ./data/thianhdep_submissions.csv
data_filepath = os.path.join("data", "thianhdep_submissions.csv")


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
    description = FileField("Description", validators=[FileAllowed(["txt", "docx", "pdf"])])
    submit = SubmitField(label="Submit")


# private_key = rsa.generate_private_key(
#     public_exponent=65537,
#     key_size=2048,
# )

# public_key = private_key.public_key()

# symmetric_key = Fernet.generate_key()
# cipher_suite = Fernet(symmetric_key)

def increment(counter_filepath: str):
        with open(counter_filepath, 'r+') as f:
            counter = f.read()
            print('counter', counter)
            counter = int(counter) if counter else 0
            counter += 1
            f.seek(0)
            f.write(str(counter))
            f.truncate()
        return str(counter)

# get the current counter value
def get_counter(counter_filepath: str):
    with open(counter_filepath, 'r') as f:
        counter = f.read()
        return counter

# app starts here
app = Flask(__name__)
# Set up logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Set up the secret key to encrypt the session
app.config["SECRET_KEY"] = "your_secret_key"
app.config["UPLOADED_FILES_DEST"] = "./uploads"

# handle media file uploads
async def handle_media_files(submission_id, employee_id, full_name, photos, video, description):
    # generate directory name: `uploads/employee_id_timestamp`
    dirname = f"{employee_id}_{full_name}"
    os.makedirs(os.path.join("uploads", dirname), exist_ok=True)
    # generate timestamp: `YYMMDDHHmmss`
    timestamp = datetime.now().strftime("%y%m%d%H%M%S")

    # handle photos, write to media_submission
    if photos is not None:
        await asyncio.gather(
            *(save_file(photo, dirname, timestamp, submission_id) for photo in photos)
        )
    # handle video
    if video is not None:
        # save video to media_submission with this format: `{timestamp}_{filename}`
        await save_file(video, dirname, timestamp, submission_id)

    # handle description
    if description is not None:
        await save_file(description, dirname, timestamp, submission_id)


async def save_file(file, dirname: str, timestamp: str, submission_id: str):
    try:
        if file is not None and file.filename != "":
            filename = f"{timestamp}_{secure_filename(file.filename)}"
            filepath = os.path.join(os.path.join("uploads", dirname), filename)
            created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            media_id = increment(os.path.join("data", "media_counter.txt"))

            # counter.increment_counter('media_counter')
            # media_id = counter.get_counter('media_counter')

            # append a new record to media_mapping.csv
            with open("data/media_mapping.csv", "a", newline="") as f:
                writer = csv.writer(f)
                # media_id,dirname,filename,created,filepath,submission_id
                writer.writerow([media_id, dirname, filename, created, filepath, submission_id])
            # return filepath to the saved file
            
            # save file
            file.save(filepath)

            return filepath

            
    except Exception as e:
        print(f"Error saving file: {str(e)}")
        return None

# Error handling
# display error message to user as an html element
"""
for each submit, create a new record in the csv file
    only latest records are valid
"""


# Check form_data input
async def submit_handler(form_data: dict):
    # Sanitize input with secure_filename for all string fields
    employee_id = secure_filename(form_data["employee_id"])
    full_name = secure_filename(form_data["full_name"]) 
    department = secure_filename(form_data["department"])    
    company = secure_filename(form_data["company"])            
    photos = form_data["photos"]
    video = form_data["video"]
    description = form_data["description"]
    # generate timestamp for each submission
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    submission_id = increment(os.path.join("data", "submission_counter.txt"))

    # counter.increment_counter('submission_counter')
    # submission_id = counter.get_counter('submission_counter')


    # handle media files
    await handle_media_files(submission_id, employee_id, full_name, photos, video, description)

    with open(data_filepath, "a", newline="") as file:
        writer = csv.writer(file)
        # write new record (row) to csv file
        writer.writerow([submission_id, employee_id, full_name, department, company, created])



"""Notes:
Current behavior: When the user uploads a file different from the allowed file types, pressing Submit will do nothing
    Expected behavior: An error message should be displayed to the user
"""


# / route for GET request
@app.route("/", methods=["GET"])
def show_upload_form():
    form = UploadForm()
    notif = session.pop("notif", None)
    return render_template("upload.html", form=form, notif=notif)

# /upload route for POST request
@app.route("/upload", methods=["POST"])
def handle_upload():
    form = UploadForm()
    if form.validate_on_submit():
        asyncio.run(submit_handler(form.data))
        return redirect("/success")  # Redirect to success.html
    else:
        session["notif"] = form.errors
        return redirect("/")  # Redirect back to the upload form


# /success route
@app.route("/success")
def success():
    return render_template("success.html")


if __name__ == "__main__":
    app.run(debug=True)
