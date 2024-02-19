'\nImplement the delegated authentication for the Microsoft Graph API using MSAL lib\n'
from msal import ConfidentialClientApplication
import webbrowser
APPLICATION_ID='61a8ce14-21ce-4e70-9384-74b4e5984a35'
CLIENT_SECRET='qt88Q~BkzY9UBc7CUXfLoeJEcUjz3efhoOkP5djC'
SCOPES=['https://graph.microsoft.com/.default']
TENTANT_ID='52251bad-a823-403e-aaa4-6c40a9fd624b'
REDIRECT_URI='http://localhost:5000/auth'
user_id='43b76bad-50b0-43e2-9dec-fe4f639bf486'
authority=f"https://login.microsoftonline.com/{TENTANT_ID}"
def init_msal_app():A=ConfidentialClientApplication(APPLICATION_ID,authority=authority,client_credential=CLIENT_SECRET);return A
def get_auth_code_flow(app):A=app.initiate_auth_code_flow(scopes=SCOPES,redirect_uri=REDIRECT_URI);B=A['auth_uri'];return A,B
def get_auth_response(auth_url):webbrowser.open(auth_url)
def get_token(app,auth_code_flow,auth_response):A=app.acquire_token_by_auth_code_flow(auth_code_flow=auth_code_flow,auth_response=auth_response,scopes=SCOPES);B=A['access_token'];return B
if __name__=='__main__':print('if ms_auth_delegated.py is executed as a script it will print this line!')