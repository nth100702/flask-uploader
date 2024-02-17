from models import User, SubmitRecord, FileUpload, ChunkedFile
from app import db
import requests, os

# database helpers
def get_user(query: dict):
  user = User.query.filter_by(**query).first()
  if user is None:
    user = User(**query)
    db.session.add(user)
    db.session.commit()
    user = User.query.filter_by(**query).first()
  return user

def get_submit_record(query: dict):
  submit_record = SubmitRecord.query.filter_by(**query).first()
  if submit_record is None:
    submit_record = SubmitRecord(**query)
    db.session.add(submit_record)
    db.session.commit()
    submit_record = SubmitRecord.query.filter_by(**query).first()
  return submit_record

def get_file_upload(query: dict):
  try:
    file_upload = FileUpload.query.filter_by(**query).first()
    if file_upload is None:
      file_upload = FileUpload(**query)
      db.session.add(file_upload)
      db.session.commit()
      file_upload = FileUpload.query.filter_by(**query).first()
    return file_upload
  except Exception as e:
    # Handle the exception here
    print(f"Error occurred in get_file_upload: {str(e)}")
    return None

def get_first_chunk(dzuuid):
  first_chunk = ChunkedFile.query.filter_by(dzuuid=dzuuid, dzchunksize=0).first()
  return first_chunk

def add_chunked_file(**args):
  chunked_file = ChunkedFile(**args)
  db.session.add(chunked_file)
  db.session.commit()
  return chunked_file

# files helpers
def reassemble_file(submit_dir, filename, dztotalchunkcount):
  # Reassemble the file from the chunks
  with open(os.path.join(submit_dir, filename), "wb") as output_file:
    for i in range(dztotalchunkcount):
      chunk_path = os.path.join(submit_dir, f"{filename}.part{i}")
      with open(chunk_path, "rb") as chunk_file:
        output_file.write(chunk_file.read())
      os.remove(chunk_path)  # Delete the chunk

def upload_smallfile_to_onedrive(local_submit_dir: str, file_name: str, msgraph_access_token):
  # prep inputs
  GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
  access_token = msgraph_access_token
  print("access_token", access_token)
  headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
  }
  onedrive_data_fyi = (
    {
      "createdDateTime": "2024-02-07T02:41:10Z",
      "eTag": '"{0E451124-1D58-4399-8B0C-E93622F58CFC},1"',
      "id": "01E26M3MJECFCQ4WA5TFBYWDHJGYRPLDH4",
      "lastModifiedDateTime": "2024-02-07T02:41:10Z",
      "name": "GMD Thi Ảnh Đẹp 2024",
      "webUrl": "https://gmdcorp-my.sharepoint.com/personal/mediamod_gemadept_com_vn/Documents/GMD%20Thi%20%E1%BA%A2nh%20%C4%90%E1%BA%B9p%202024",
      "cTag": '"c:{0E451124-1D58-4399-8B0C-E93622F58CFC},0"',
      "size": 0,
      "createdBy": {
        "user": {
          "email": "mediamod@gemadept.com.vn",
          "id": "fee2b48b-f942-40a7-9e8a-54d78dbd8397",
          "displayName": "MediaMod",
        }
      },
      "lastModifiedBy": {
        "user": {
          "email": "mediamod@gemadept.com.vn",
          "id": "fee2b48b-f942-40a7-9e8a-54d78dbd8397",
          "displayName": "MediaMod",
        }
      },
      "parentReference": {
        "driveType": "business",
        "driveId": "b!BSMpwLx6u0q_b-Nt-1W-O7tis30oT8lEvvD4tylYPZ1oPotOMoVXT5wqC5MaOvrI",
        "id": "01E26M3MN6Y2GOVW7725BZO354PWSELRRZ",
        "name": "Documents",
        "path": "/drive/root:",
        "siteId": "c0292305-7abc-4abb-bf6f-e36dfb55be3b",
      },
      "fileSystemInfo": {
        "createdDateTime": "2024-02-07T02:41:10Z",
        "lastModifiedDateTime": "2024-02-07T02:41:10Z",
      },
      "folder": {"childCount": 0},
    },
  )
  onedrive_target_folder_id = (
    "01E26M3MJECFCQ4WA5TFBYWDHJGYRPLDH4"  # "Thi Anh Dep 2024"
  )
  onedrive_target_user_id = "fee2b48b-f942-40a7-9e8a-54d78dbd8397"  # MediaMod
  ONEDRIVE_API_ENDPOINT = f"{GRAPH_API_ENDPOINT}/users/{onedrive_target_user_id}/drive/items/{onedrive_target_folder_id}"
  # first check if folder exists, if not create it; onedrive_submit_dir = local_submit_dir
  onedrive_submit_dir = local_submit_dir
  res = requests.get(ONEDRIVE_API_ENDPOINT, headers=headers)
  print("res, get all drive items", res.json())

  with open(onedrive_submit_dir, "rb") as upload:
    media_content = upload.read()
  response = requests.put(
    f"{GRAPH_API_ENDPOINT}/users/{onedrive_target_user_id}/drive/items/{onedrive_target_folder_id}:/{file_name}:/content",
    headers=headers,
    data=media_content,
  )
  print("uploading to onedrive", response.json())
  # check if the file has been uploaded to OneDrive
  if response.status_code == 200:
    return True
  else:
    return False

# upload large file to OneDrive
  
# Small file upload ref: https://learn.microsoft.com/en-us/graph/api/driveitem-put-content?view=graph-rest-1.0&tabs=http
# Large file upload ref: https://learn.microsoft.com/en-us/graph/api/driveitem-createuploadsession?view=graph-rest-1.0

"""Recommendation:
- Implement retry mechanism to handle large file upload
"""

"""rety mechanism example
max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
      response = requests.put(
        f"{GRAPH_API_ENDPOINT}/users/{user_id}/drive/items/root:/{file_name}:/content",
        headers=headers,
        data=media_content,
      )
      if response.status_code == 200:
        print(response.json())
        break
      else:
        retry_count += 1
        print(f"Request failed. Retrying... (Attempt {retry_count}/{max_retries})")
    else:
      print("Max retries exceeded. Request failed.")
"""