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

# app starts here
app = Flask(__name__)
# enable debug mode
app.debug = True
app.config["SECRET_KEY"] = "dev"
app.config["DATA_DIR"] = "./uploads"
app.config['ALLOWED_EXTENSIONS'] = {'doc', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
# set up flask logging
log = app.logger

# connects app to the database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

app.config['RECAPTCHA_USE_SSL'] = False
app.config['RECAPTCHA_PUBLIC_KEY'] = '6Le1GXMpAAAAAI5Cz79kkAGSjY_pT5y6WXuwGSOV'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6Le1GXMpAAAAANq6l6JNnMcbb_y5ONMNhqLuGpo7'
app.config['RECAPTCHA_OPTIONS'] = {'theme': 'white'}

class EntryForm(FlaskForm):
    ma_nhan_vien = StringField("Mã nhân viên", validators=[DataRequired()])
    ho_ten = StringField("Họ tên", validators=[DataRequired()])
    don_vi = SelectField("Đơn vị", choices=[("GMDHO", "Gemadept HO"), ("GML", "Gemalink")], validators=[DataRequired()])
    recaptcha = RecaptchaField()

# / route for GET request
@app.route("/", methods=["GET"])
def show_upload_form():
    page_content = { "title": "" }
    return render_template("upload.html", form=EntryForm(), page_content=page_content)

# /upload route for POST request
@app.route("/upload", methods=["POST"])
def handle_upload():
    # handle chunked files from client
    file = request.files['file']
    print('file', file)
    save_path = os.path.join(app.config['DATA_DIR'], secure_filename(file.filename))
    current_chunk = int(request.form['dzchunkindex'])
    # If the file already exists it's ok if we are appending to it,
    # but not if it's new file that would overwrite the existing one
    if os.path.exists(save_path) and current_chunk == 0:
        # 400 and 500s will tell dropzone that an error occurred and show an error
        return make_response(('File already exists', 400))
    try:
        with open(save_path, 'ab') as f:
            f.seek(int(request.form['dzchunkbyteoffset']))
            f.write(file.stream.read())
    except OSError:
        # log.exception will include the traceback so we can see what's wrong 
        log.exception('Could not write to file')
        return make_response(("Not sure why,"
                              " but we couldn't write the file to disk", 500))
    total_chunks = int(request.form['dztotalchunkcount'])
    if current_chunk + 1 == total_chunks:
        # This was the last chunk, the file should be complete and the size we expect
        if os.path.getsize(save_path) != int(request.form['dztotalfilesize']):
            log.error(f"File {file.filename} was completed, "
                      f"but has a size mismatch."
                      f"Was {os.path.getsize(save_path)} but we"
                      f" expected {request.form['dztotalfilesize']} ")
            return make_response(('Size mismatch', 500))
        else:
            log.info(f'File {file.filename} has been uploaded successfully')
    else:
        log.debug(f'Chunk {current_chunk + 1} of {total_chunks} '
                  f'for file {file.filename} complete')
    return make_response(("Chunk upload successful", 200))



# /success route
@app.route("/success")
def success():
    return render_template("success.html")

if __name__ == "__main__":
    app.run(debug=True)
