# utils.py

from flask_wtf import FlaskForm
from wtforms import ValidationError

def FileMaxSizeMB(max_size: int):
    def _file_max_size(form: FlaskForm, field):
        if field.data:
            for file in field.data:
                file_size = len(file.read())
                if file_size > max_size * 1024 * 1024:
                    raise ValidationError(f"File size must be less than {max_size}MB")
                file.seek(0)  # Reset file position to the beginning

    return _file_max_size