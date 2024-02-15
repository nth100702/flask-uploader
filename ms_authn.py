from msal import exceptions, ConfidentialClientApplication
# from msgraph import GraphClient

# MSAL: application vs. delegated permissions
# Public vs. confidential client

# GMD az
# APPLICATION_ID = "61a8ce14-21ce-4e70-9384-74b4e5984a35"
# CLIENT_SECRET = "qt88Q~BkzY9UBc7CUXfLoeJEcUjz3efhoOkP5djC"
# SCOPES = ["https://graph.microsoft.com/.default"]
# TENTANT_ID = "52251bad-a823-403e-aaa4-6c40a9fd624b"
# user_id = "43b76bad-50b0-43e2-9dec-fe4f639bf486"
# authority = f"https://login.microsoftonline.com/{TENTANT_ID}"

# Test az
APPLICATION_ID = "aefa3b3d-6eea-4be3-8354-b16cd4218544"
CLIENT_SECRET = "Vib8Q~EFqdBMp3DVLrvhSu1xuy1hGZ62hC3BvbXP"
SCOPES = ["https://graph.microsoft.com/.default"]
TENTANT_ID = "64ad74cc-5f52-4926-9f79-da2da923cbd6"
user_id = "ec6b0e1b-220f-4480-9756-93755315aac6"
authority = f"https://login.microsoftonline.com/{TENTANT_ID}"

# Init MSAL.ConfidentialClientApplication
app = ConfidentialClientApplication(
    APPLICATION_ID,
    authority=authority,
    client_credential=CLIENT_SECRET,
)

access_token: str | None = None

"""Notes:
- MSAL caches token after its has been acquired
- The app should first try to acquire token silently from cache before attempting to acquire token by other means (such as acquire_token_for_client)
"""

"""Implementation:
- Add error handling mechanism to handle token acquisition failure
"""

try:
    # Acquire token silently from cache first
    result = app.acquire_token_silent(SCOPES, account=None)
    # If no token found, acquire for client
    if not result:
        """Recommendation:
        - Implement OBF flow => more secure than the current implementation
            OBF will first ask for user's consent to access their data (not all msgraph resources like the current implementation)
        """
        result = app.acquire_token_for_client(scopes=SCOPES)   

    if "access_token" in result:
        # save access_token
        access_token= result["access_token"]
        # print("access_token", result["access_token"])  # Yay!
    else:
        print(result.get("error"))
        print(result.get("error_description"))
        print(result.get("correlation_id"))
except exceptions.MsalError as e:
    print(e)