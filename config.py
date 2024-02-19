_B='uploads'
_A='database.db'
import os
class Config:
        SECRET_KEY='@FYzFGL1pk5265_jCb3ti+wq16SUR4Oo!ARIuXXzAIgvw=';'\n    Solution: Define FLASK_ENV and DEBUG in .env file\n    then use python-dotenv to load the .env file\n    ';basedir=os.path.abspath(os.path.dirname(__file__))
        if not os.path.exists(os.path.join(basedir,_A)):
                with open(os.path.join(basedir,_A),'w')as f:0
        SQLALCHEMY_DATABASE_URI='sqlite:///'+os.path.join(basedir,_A);SQLALCHEMY_TRACK_MODIFICATIONS=False
        if not os.path.exists(os.path.join(basedir,_B)):os.mkdir(os.path.join(basedir,_B))
        UPLOAD_FOLDER=_B;ALLOWED_EXTENSIONS={'doc','pdf','png','jpg','jpeg','gif'};RECAPTCHA_USE_SSL=False;RECAPTCHA_PUBLIC_KEY='6Le1GXMpAAAAAI5Cz79kkAGSjY_pT5y6WXuwGSOV';RECAPTCHA_PRIVATE_KEY='6Le1GXMpAAAAANq6l6JNnMcbb_y5ONMNhqLuGpo7';RECAPTCHA_OPTIONS={'theme':'white'};SESSION_COOKIE_SECURE=True;SESSION_COOKIE_HTTPONLY=True;SESSION_COOKIE_SAMESITE='Lax'