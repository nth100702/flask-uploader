import os

class Config(object):
    # Flask
    SECRET_KEY = 'SECRET'
    # FLASK_ENV & DEBUG => only read from env var, defined here won't work
    """
    Solution: Define FLASK_ENV and DEBUG in .env file
    then use python-dotenv to load the .env file
    """
    # FLASK_ENV = "development" 
    # DEBUG = True # debug mode
    # Database
    basedir = os.path.abspath(os.path.dirname(__file__))
    # Create database if it doesn't exist
    if not os.path.exists(os.path.join(basedir, 'database.db')):
        with open(os.path.join(basedir, 'database.db'), 'w') as f:
            pass
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

    # Session security
    # SESSION_COOKIE_SECURE = True
    # SESSION_COOKIE_HTTPONLY = True
    # SESSION_COOKIE_SAMESITE = 'Strict' # 'Strict' means no cross-site cookies
    # PERMANENT_SESSION_LIFETIME = 3600 * 24 * 7  # 7 days
