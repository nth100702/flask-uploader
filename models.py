_B=True
_A=False
from datetime import datetime
import pytz
from app import db,app
'SqlAlchemy database models\n'
def now():return datetime.now(tz=pytz.timezone('Asia/Ho_Chi_Minh'))
class ChunkedFile(db.Model):
        __tablename__='chunked_file';id=db.Column(db.Integer,primary_key=_B);dzuuid=db.Column(db.String(100),nullable=_A);dzchunkindex=db.Column(db.Integer,nullable=_A);dzchunksize=db.Column(db.Integer,nullable=_A);dztotalfilesize=db.Column(db.Integer,nullable=_A);dztotalchunkcount=db.Column(db.Integer,nullable=_A);dzchunkbyteoffset=db.Column(db.Integer,nullable=_A);chunkpath=db.Column(db.String(100),nullable=_A);created_at=db.Column(db.DateTime,nullable=_A,default=now());file_upload_id=db.Column(db.Integer,db.ForeignKey('file_upload.id'),nullable=_A)
        def __repr__(A):return f"ChunkedFile('{A.dzuuid}', '{A.created_at}')"
class FileUpload(db.Model):
        id=db.Column(db.Integer,primary_key=_B);filename=db.Column(db.String(100),nullable=_A);filepath=db.Column(db.String(100),nullable=_A);total_chunks=db.Column(db.Integer,nullable=_A);chunks_received=db.Column(db.Integer,default=0);file_reassembled=db.Column(db.Boolean,default=_A);upload_completed=db.Column(db.Boolean,default=_A);created_at=db.Column(db.DateTime,nullable=_A,default=now());uploaded_at=db.Column(db.DateTime,nullable=_A,default=now());chunked_files=db.relationship('ChunkedFile',backref='file_upload');submit_record_id=db.Column(db.Integer,db.ForeignKey('submit_record.id'),nullable=_A)
        def __repr__(A):return f"FileUpload('{A.filename}', '{A.uploaded_at}')"        
class SubmitRecord(db.Model):
        id=db.Column(db.Integer,primary_key=_B);submit_id_frontend=db.Column(db.String(100),nullable=_A);files_received=db.Column(db.Integer,nullable=_A,default=0);files_uploaded=db.Column(db.Integer,nullable=_A,default=0);all_files_uploaded=db.Column(db.Boolean,default=_A);created_at=db.Column(db.DateTime,nullable=_A,default=now());submitter_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=_A);file_uploads=db.relationship('FileUpload',backref='submit_record')
        def __repr__(A):return f"SubmitRecord('{A.submitted_at}', '{A.all_files_uploaded}')"
class User(db.Model):
        id=db.Column(db.Integer,primary_key=_B);employee_id=db.Column(db.String(100),nullable=_A);full_name=db.Column(db.String(100),nullable=_A);division=db.Column(db.String(100),nullable=_A);date_created=db.Column(db.DateTime,nullable=_A,default=now());submit_records=db.relationship('SubmitRecord',backref='user')
        def __repr__(A):return f"User('{A.employee_id}', '{A.full_name}', '{A.division}')"
"\nYou have to create db tables WITHIN the flask app context\nElse you will get an error like this: RuntimeError(unbound_message) from None RuntimeError: Working outside of application context.\nSolution: Use app's context manager to create db tables\n"        
with app.app_context():db.create_all()