"""
Implement the delegated authentication for the Microsoft Graph API using MSAL lib
"""

from msal import ConfidentialClientApplication
import webbrowser

# msal_config = {
#     "auth": {
#         "tenantId": "52251bad-a823-403e-aaa4-6c40a9fd624b",
#         "userId": "43b76bad-50b0-43e2-9dec-fe4f639bf486",
#         "clientId": "61a8ce14-21ce-4e70-9384-74b4e5984a35",
#         "authority": "https://login.microsoftonline.com/52251bad-a823-403e-aaa4-6c40a9fd624b",
#         "clientSecret": "qt88Q~BkzY9UBc7CUXfLoeJEcUjz3efhoOkP5djC",
#         "redirectUri": "http://localhost:5000/auth"
#     },
#     "cache": {
#         "cacheLocation": "localStorage",
#         "storeAuthStateInCookie": True
#     },
# "user": {
#         "businessPhones": [],
#         "displayName": "MediaMod",
#         "givenName": "Media",
#         "mail": "mediamod@gemadept.com.vn",
#         "preferredLanguage": "en-US",
#         "surname": "Mod",
#         "userPrincipalName": "mediamod@gemadept.com.vn",
#         "id": "fee2b48b-f942-40a7-9e8a-54d78dbd8397",
#     },
    # msgraph_config = {
    #     "apiUrl": "https://graph.microsoft.com/v1.0",
    #     "scopes": ["https://graph.microsoft.com/.default"]
# }


# GMD credentials
APPLICATION_ID = "61a8ce14-21ce-4e70-9384-74b4e5984a35"
CLIENT_SECRET = "qt88Q~BkzY9UBc7CUXfLoeJEcUjz3efhoOkP5djC"
SCOPES = ["https://graph.microsoft.com/.default"]
TENTANT_ID = "52251bad-a823-403e-aaa4-6c40a9fd624b"
REDIRECT_URI = "http://localhost:5000/auth"
user_id = "43b76bad-50b0-43e2-9dec-fe4f639bf486"
authority = f"https://login.microsoftonline.com/{TENTANT_ID}"


# Init MSAL.ConfidentialClientApplication
def init_msal_app():
    app = ConfidentialClientApplication(
        APPLICATION_ID,
        authority=authority,
        client_credential=CLIENT_SECRET,
    )
    return app


def get_auth_code_flow(app: ConfidentialClientApplication):
    auth_code_flow = app.initiate_auth_code_flow(
        scopes=SCOPES, redirect_uri=REDIRECT_URI
    )
    auth_url = auth_code_flow["auth_uri"]
    return auth_code_flow, auth_url


def get_auth_response(auth_url):
    webbrowser.open(auth_url)  # redirects to /auth


def get_token(app: ConfidentialClientApplication, auth_code_flow, auth_response):
    result = app.acquire_token_by_auth_code_flow(auth_code_flow=auth_code_flow, auth_response=auth_response, scopes=SCOPES)
    access_token = result["access_token"]
    return access_token


if __name__ == "__main__":
    print("if ms_auth_delegated.py is executed as a script it will print this line!")
