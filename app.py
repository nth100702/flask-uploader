_D='Unauthorized'
_C='127.0.0.1'
_B='GET'
_A=True
import base64
from flask import Flask,make_response,render_template,g,request,session
from flask_wtf import FlaskForm,RecaptchaField
from wtforms import StringField,SelectField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_migrate import Migrate
from ms_auth_delegated import init_msal_app,get_auth_code_flow,get_auth_response,get_token
import os,logging
from datetime import datetime
from flask_minify import Minify
confidential_client_app=init_msal_app()
auth_code_flow,auth_url=get_auth_code_flow(confidential_client_app)
app=Flask(__name__)
app.config.from_object('config.Config')
log=app.logger
logging.basicConfig(filename='app.log',level=logging.INFO)
db=SQLAlchemy(app)
migrate=Migrate(app,db)
'\nflask_session will try to create a new instance of slqalchemy (aka. session interface) => error\nSolution: Pass the db instance to flask_session to use the existing db instance instead\n'
app.config['SESSION_TYPE']='filesystem'
'\nBy default, flask_session does NOT encrypt session data\n    If you want to encrypt them, you need to implement yourself by manipulating flask_session SessionInterface => Unnecessary complexity...\n'
Session(app)
auth_response=get_auth_response(auth_url)
minify=Minify(app=app,html=_A,js=_A,cssless=_A)
@app.before_request
def prepare_request():g.nonce=base64.b64encode(os.urandom(32)).decode('utf-8')
@app.after_request
def secure_flask(response):A=response;A.headers['Content-Security-Policy']=f"default-src 'self'; img-src 'self' data: https://www.gemadept.com.vn/img/nav/logo.png; script-src 'self' 'nonce-{g.nonce}' https://www.gstatic.com/recaptcha/releases/yiNW3R9jkyLVP5-EEZLDzUtA/recaptcha__en.js https://www.google.com/recaptcha/api.js https://cdnjs.cloudflare.com/ajax/libs/flowbite/2.2.1/flowbite.min.js https://cdnjs.cloudflare.com/ajax/libs/dropzone/5.9.3/min/dropzone.min.js https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js; style-src 'self' https://cdnjs.cloudflare.com/ajax/libs/dropzone/5.9.3/dropzone.min.css https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css; frame-src 'self' https://www.google.com;";A.headers['X-Content-Type-Options']='nosniff';A.headers['X-Frame-Options']='SAMEORIGIN';A.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains';A.set_cookie('username','flask',secure=_A,httponly=_A,samesite='Lax');A.set_cookie('snakes','3',max_age=600);return A
@app.route('/auth',methods=[_B])
def auth():
        D='msgraph_access_token';C='Authorization code not found';B='msgraph_auth_response'
        if request.remote_addr!=_C:return _D,401
        session.clear();"\n    # session.clear() => clear client session & simple server session\n        we're using sqlalchemy to store session data, hence we need to clear the db record instead\n    "
        if request.args.get('code')is not None:A=request.args;session[B]=A
        else:log.error(C);return make_response(({'error':'auth_error','error_description':C},400))
        A=session.get(B);E=get_token(confidential_client_app,auth_code_flow,A);session[D]=E;return make_response(({'auth_response':session.get(B),'access_token':session.get(D)},200))
@app.route('/',methods=[_B])
def show_upload_form():
        class A(FlaskForm):ma_nhan_vien=StringField('Mã nhân viên',validators=[DataRequired()]);ho_ten=StringField('Họ tên',validators=[DataRequired()]);don_vi=SelectField('Đơn vị',choices=[('GMDHO','Gemadept HO'),('GML','Gemalink')],validators=[DataRequired()]);recaptcha=RecaptchaField()
        return render_template('upload.html',form=A(),nonce=g.nonce)
@app.route('/recaptcha',methods=[_B])
def return_recaptchakey():
        if request.remote_addr!=_C:log.error(f"Unauthorized request to /recaptcha from {request.remote_addr}");return _D,401
        return make_response((app.config['RECAPTCHA_PRIVATE_KEY'],200))
@app.route('/upload',methods=['POST'])
def handle_upload():
        R='temp';H=request.files.get('file');D=secure_filename(H.filename);I=secure_filename(request.form.get('dzuuid'));J=int(request.form.get('dzchunkindex'));S=int(request.form.get('dzchunksize'));B=int(request.form.get('dztotalchunkcount'));T=int(request.form.get('dztotalfilesize'));U=int(request.form.get('dzchunkbyteoffset'));V=request.form.get('submit_id');K=secure_filename(request.form.get('ma_nhan_vien'));L=secure_filename(request.form.get('ho_ten'));M=secure_filename(request.form.get('don_vi'));"\n    Flask DEV server is SYNCHRONOUS in nature\n        Avoid using async operations in flask dev server => use a production server instead (gunicorn, uwsgi, etc.)\n    Also it's not recommended to use asyncio in flask, as it's not designed to be used with asyncio\n    ";"\n    You should validate the recaptcha response on the client side before proceeding with the file upload\n        reCAPTCHA v2 tokens expire after 2 minutes. If your file upload takes longer than this, the token will be invalid by the time it's verified.\n            as a result, some large files MAY NEVER BE UPLOADED due to this time limit...\n    ";"\n    To avoid flask session inconsistency (each request => !same session...) => Use server-side session\n        Default: flask's native session -> client-side only (web cookies)\n    To use server-side session (e.g. for storing access_token), install flask-session\n        Implement server-side session (data stored in server's memory via a traditional database: sql / cache db: redis, memcached)\n    ";from helper import get_user as W,get_submit_record as X,get_file_upload as N,is_first_chunk as Y,add_chunked_file as Z,file_exist_check as a,save_chunk as b,reassemble_file as c
        try:
                def d(ma_nhan_vien,don_vi,ho_ten):A=os.path.join(app.config['UPLOAD_FOLDER'],f"{ma_nhan_vien}-{don_vi}-{ho_ten}-{datetime.now().strftime('%y%m%d')}");os.makedirs(A,exist_ok=_A);os.makedirs(os.path.join(A,R),exist_ok=_A);return A
                E=d(K,M,L);e=W({'employee_id':K,'full_name':L,'division':M});O=X({'submit_id_frontend':V,'submitter_id':e.id});P={'filename':D,'filepath':E,'total_chunks':B,'submit_record_id':O.id};A=None
                if Y(dzuuid=I):A=N(P,new=_A)
                else:A=N(P)
                '\n        Save chunk (each chunk content is a dzfile in each request payload)\n            chunks are located in submit_dir/temp\n                temp dir will be removed once file is reassembled\n            each chunk is named as {filename}_{dzchunkindex}.part\n        ';f=os.path.splitext(D)[0];F=f"{f}_{J}.part";G=os.path.join(E,R);os.makedirs(G,exist_ok=_A);Q=os.path.join(G,F);"\n        Before saving the chunk, better to check if it's already saved\n            If chunk is already saved\n                Return a success response, skip to the next chunk\n            Else: continue processing the chunk\n        "
                if a(G,F):log.info(f"Chunk already saved: {F}");return make_response('Chunk already saved',200)
                b(H,Q);Z(dzuuid=I,dzchunkindex=J,dzchunksize=S,dztotalfilesize=T,dztotalchunkcount=B,dzchunkbyteoffset=U,chunkpath=Q,file_upload=A);A.chunks_received+=1      
                if A.chunks_received==B:
                        if c(submit_dir=E,filename=D,dztotalchunkcount=B):A.file_reassembled=_A;O.files_received+=1
                db.session.commit();return make_response(render_template('success.html'),200)
        except Exception as C:
                log.error(f"Error occurred in /upload: {str(C)}")
                if FileExistsError:return make_response((str(C),409))
                if'Xác thực reCAPTCHA thất bại'in str(C):return make_response((str(C),400))
                return make_response(('Uh oh, lỗi server. Xin thử lại hoặc liên hệ IT tập đoàn để được hỗ trợ',500))
'\nPrecepts: Separation of concerns\n    2 key roles of this app: accepting file uploads from the frontend & uploading files to OneDrive via MSGraph API\nIdea: Configure flask to run a scheduled task to upload files to OneDrive (once every hour)\n    - This way, the frontend will not be blocked by the file upload process\n    - The frontend will only be responsible for sending files to the server\n    - The server will be responsible for uploading files to OneDrive\n'
@app.route('/onedrive',methods=['POST'])
def handle_onedrive_upload():return''
if __name__=='__main__':
        with app.app_context():db.create_all()
        app.run(debug=_A)