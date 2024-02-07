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

# Filepaths
# os.path.join("uploads", "photos")
# os.path.join("uploads", "video")
# resolve path to thianhdep_submissions.csv in ./data/thianhdep_submissions.csv
data_filepath = os.path.join("data", "thianhdep_submissions.csv")
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
            FileAllowed(["jpg", "png", "zip"]),
            FileMaxSizeMB(1),
            # FileRequired(),
        ],
    )  # FileMaxSizeMB(5), FileRequired()
    video = FileField(
        "Video", validators=[FileAllowed(["mp4"]), FileMaxSizeMB(500)]
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

# Error handling
# display error message to user as an html element
"""
for each submit, check if the employee_id exists in the csv file
if exists, check if photos and video are the same as the previous ones
if not, append the new photos and video to the existing record
if same, do nothing
if not, create a new record
"""


# Check form_data input
def submit_handler(form_data):
    employee_id = form_data["employee_id"]
    full_name = form_data["full_name"]
    department = form_data["department"]
    company = form_data["company"]
    # photos = form_data['photos']
    # video = form_data['video']
    # generate timestamp for each submission
    created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(data_filepath, "a", newline="") as file:
        writer = csv.writer(file)
        # write new record (row) to csv file
        writer.writerow([employee_id, full_name, department, company, created])


@app.route("/", methods=["GET", "POST"])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        submit_handler(form.data)
    return render_template("upload.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)
