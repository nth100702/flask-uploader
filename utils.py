# utils.py
import requests
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


def verify_recaptcha(response, remote_ip):
    recaptcha_secret = "your-recaptcha-secret-key"
    data = {
        'secret': recaptcha_secret,
        'response': response,
        'remoteip': remote_ip
    }
    r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
    result = r.json()

    # result will be a dict containing 'success': True/False and potentially 'error-codes'
    return result

# Use the function
recaptcha_response = "user-recaptcha-response"  # This should be obtained from the form submission
user_ip = "user-ip"  # This should be obtained from the request
result = verify_recaptcha(recaptcha_response, user_ip)

if result['success']:
    print("reCAPTCHA verified successfully.")
else:
    print("Failed to verify reCAPTCHA. Error codes: ", result.get('error-codes'))