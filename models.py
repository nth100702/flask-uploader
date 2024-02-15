from app import db
from datetime import datetime

class ChunkedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dzuuid = db.Column(db.String(100), nullable=False)
    dzchunkindex = db.Column(db.Integer, nullable=False)
    dztotalfilesize = db.Column(db.Integer, nullable=False)
    dztotalchunkcount = db.Column(db.Integer, nullable=False)
    dzchunkbyteoffset = db.Column(db.Integer, nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    filepath = db.Column(db.String(100), nullable=False)
    date_uploaded = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    submit_record_id = db.Column(db.Integer, db.ForeignKey('submit_record.id'), nullable=False)
    # specify relationship to SubmitRecord
    submit_record = db.relationship('SubmitRecord', backref='chunked_files')
    def __repr__(self):
        return f"ChunkedFile('{self.filename}', '{self.date_uploaded}')"

class SubmitRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submitter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_submitted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # specify relationship to User
    submitter = db.relationship('User', backref='submitter')
    # specify relationship to ChunkedFile
    chunked_files = db.relationship('ChunkedFile', backref='submit_record')
    status = db.Column(db.String(100), nullable=False)
    def __repr__(self):
        return f"SubmitRecord('{self.date_submitted}', '{self.status}')"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(100), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    division = db.Column(db.String(100), nullable=False)
    submit_records = db.relationship('SubmitRecord', backref='user')
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # specify relationship to SubmitRecord
    submit_records = db.relationship('SubmitRecord', backref='user')
    def __repr__(self):
        return f"User('{self.employee_id}', '{self.full_name}', '{self.division}')"
