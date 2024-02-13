from flask import Flask, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
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

# app starts here
app = Flask(__name__)
# enable debug mode
app.debug = True
app.config["SECRET_KEY"] = "dev"
app.config["UPLOADED_FILES_DEST"] = "./uploads"

# connects app to the database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# class EntryForm(FlaskForm):
#     ma_nhan_vien = StringField("Mã nhân viên", validators=[DataRequired()])
#     ho_ten = StringField("Họ tên", validators=[DataRequired()])
#     don_vi = SelectField("Đơn vị", choices=[("GMDHO", "Gemadept HO"), ("GML", "Gemalink")], validators=[DataRequired()])

# / route for GET request
@app.route("/", methods=["GET"])
def show_upload_form():
    # form = EntryForm()
    return render_template("upload.html")

# /upload route for POST request
@app.route("/upload", methods=["POST"])
def handle_upload():
    # print common data payload of request
    print(request.form)
    # print request.files
    print(request.files)
    print(request.get)
    # files = request.files.get("file")
    return


# /success route
@app.route("/success")
def success():
    return render_template("success.html")

if __name__ == "__main__":
    app.run(debug=True)
