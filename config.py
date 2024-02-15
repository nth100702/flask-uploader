import os

class Config(object):
    # Flask
    SECRET_KEY = 'SECRET'
    DEBUG = True
    # Database
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'database.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploader
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'doc', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

    # Recaptcha
    RECAPTCHA_USE_SSL = False
    RECAPTCHA_PUBLIC_KEY = '6Le1GXMpAAAAAI5Cz79kkAGSjY_pT5y6WXuwGSOV'
    RECAPTCHA_PRIVATE_KEY = '6Le1GXMpAAAAANq6l6JNnMcbb_y5ONMNhqLuGpo7'
    RECAPTCHA_OPTIONS = {'theme': 'white'}