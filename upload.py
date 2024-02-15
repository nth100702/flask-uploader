import os
import requests

GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
}

file_path = os.path.abspath(f"uploads/GML-0001-NguyenVoMinhLuan-TacPhamDuThi.png")
file_name = os.path.basename(file_path)

with open(file_path, "rb") as upload:
    print('file_path', file_path)
    media_content = upload.read()

response = requests.put(
    f"{GRAPH_API_ENDPOINT}/users/{user_id}/drive/items/root:/{file_name}:/content",
    headers=headers,
    data=media_content,
)

print(response.json())
# if __name__ == "__main__":
#     flask_app.run(debug=True)

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