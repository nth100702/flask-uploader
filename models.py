# Define flask-alchemy models: ChunkedFile

from app import db
from datetime import datetime

class ChunkedFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    filepath = db.Column(db.String(100), nullable=False)
    date_uploaded = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ma_nhan_vien = db.Column(db.String(10), nullable=False)
    ho_ten = db.Column(db.String(50), nullable=False)
    ma_don_vi = db.Column(db.String(10), nullable=False)
    ten_tac_pham = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"ChunkedFile('{self.filename}', '{self.filepath}', '{self.date_uploaded}', '{self.ma_nhan_vien}', '{self.ho_ten}', '{self.ma_don_vi}', '{self.ten_tac_pham}')"