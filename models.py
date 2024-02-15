# Define flask-alchemy models: ChunkedFile

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

class FormData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ma_nhan_vien = db.Column(db.String(100), nullable=False)
    ho_ten = db.Column(db.String(100), nullable=False)
    ma_don_vi = db.Column(db.String(100), nullable=False)

# specify model relationships
# each entry has many chunked files
# each chunked file belongs to one entry


    def __repr__(self):
        return f"ChunkedFile('{self.filename}', '{self.filepath}', '{self.date_uploaded}', '{self.ma_nhan_vien}', '{self.ho_ten}', '{self.ma_don_vi}', '{self.ten_tac_pham}')"