"""
Implement the delegated authentication for the Microsoft Graph API using MSAL lib
"""

from msal import ConfidentialClientApplication

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
#     }
# }

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
app = ConfidentialClientApplication(
    APPLICATION_ID,
    authority=authority,
    client_credential=CLIENT_SECRET,
)

"""
Every time the app runs, it must authenticate itself to the Microsoft Graph API on behalf of the user.
  Meaning if you restart it, you will need to (manually) authenticate again.
"""

# initiate auth code flow
auth_code_flow = app.initiate_auth_code_flow(scopes=SCOPES, redirect_uri=REDIRECT_URI)
# redirect user to auth_url to give permission consent
auth_url = auth_code_flow['auth_uri']

# auth_code = '0.AUoArRslUiOoPkCqpGxAqf1iSxTOqGHOIXBOk4R0tOWYSjWJAAg.AgABAAIAAADnfolhJpSnRYB1SVj-Hgd8AgDs_wUA9P8zQH1cRBnszLj1VjVEhMweuqPgN0-M3_fGT-Ko490l4AufcsMi5ishO34H_rER10Dgv3AMxa9koc9Qdl-9BGl6s1eoqsGR_5_aOSkxCGhJ2Uayk_8F-DH9XSYpTMegSQEdNTVtSS5m0ADWftbZJvm7TtUFc4qklqX5bifQMJmm4-o-J9jMtLisTf9wjPc3uTpPeqtprpFzKXEMhsMPxWusvEqEMLupNZO9uG7yvc63XKXnx2d9UUNIfed9D1aZ4F-4i3gS-4o743J1jESNH3mzYVvh5fKgD_3y71RlAJKNoiHnBMBca7T8au_aNmEf9k13S43J2dhvXIwXSYWs0wU0fjXlpiNRFCutHKW7HuT7Z3msf33DYnldNR3SrYT4qPS6k1Y9fz3zS87OMAMXWufRMlD1XTx4J-Le6c24-KiTxwsd6cAjPcmGQvUHXa0eu-jotTtwnfntWGphzzqRNeTH86ImmoOvjybxCeN2H531IY_HNVkh4nGN0ebMWn9ocdOZypiv4ySt4xR6H0pjPhyNkp5prkuJxMwuTM3rVoy-m6t_paMb5O8iT-l-XRB-tsbMqk9k-5Sgb_LoIijv7FQZ46oT6POJbdZqDtERB_d5FcNaSOjtfwpfrHhziW_Jx2VxtpE16klv50xbgJ3E0bQY_pCv4QAdPQqAqJaXX35EXysKZO54eOaU91F6hi6zVHWUOzYSvZbi4UHUAtF1VC6iHktq6Bu1LkWHAas4saYW00ALYhSFS-AXfrj8e7OJc4FeU_SAkdYv3tLHZEb_uQdaXDOrjo7Jdv6ZI9fum6X-SZpRtcHUP_5GxhJgcxbQJjz1uea3gLe57DrMZ5VsfFHFa7ywV2oUv_-eM-XMKs223cH8hYsXkO9kwpRToY2H_QKrQt0n2Wyyv8FlPlD3Z-MZgp5c0HjkX-xWaNeCHLetdMbv9Pw725swhYd5YhGVNC8P52jTRdWg4PFuFyH0bHd2AV-n86t6nNg-XhOW7mnjeDr6hBg6L37lmAfVvNKfxnwhokf6I7Elky3f8e5pjJZYV-wRw-CFGbB-irl2U1w9E9uh&client_info=eyJ1aWQiOiI0M2I3NmJhZC01MGIwLTQzZTItOWRlYy1mZTRmNjM5YmY0ODYiLCJ1dGlkIjoiNTIyNTFiYWQtYTgyMy00MDNlLWFhYTQtNmM0MGE5ZmQ2MjRiIn0&state=XmhSTnQpVFcHrWDA&session_state=58a07cd7-7beb-4f71-9b49-314d39518ea1'
print('auth_code_flow', auth_code_flow)
# acquire token by auth code flow
result = app.acquire_token_by_auth_code_flow(auth_code_flow, auth_code)
# print('result', result)

access_token = result['access_token']
print('access_token', access_token)

# # Acquire token silently from cache first
# result = app.acquire_token_silent(SCOPES, account=None)
# # If no token found, acquire authorization code
# if not result:
#     result = app.acquire_token_for_client(scopes=SCOPES)



