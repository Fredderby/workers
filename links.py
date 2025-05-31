import os
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
import gspread


# Load environment variables from .env file
load_dotenv()

def cred():
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Retrieve environment variables
    private_key = os.getenv("PRIVATE_KEY")
    project_id = os.getenv("PROJECT_ID")
    private_key_id = os.getenv("PRIVATE_KEY_ID")
    client_email = os.getenv("CLIENT_EMAIL")
    client_id = os.getenv("CLIENT_ID")
    client_x509_cert_ur = os.getenv("CLIENT_X509_CERT_URL")
    # Create credentials from environment variables
    credentials_dict = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": private_key_id,
        "private_key": private_key,  # Replace escaped newlines
        "client_email": client_email,
        "client_id": client_id,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": client_x509_cert_ur
    }

    # Use the dictionary to create credentials
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, SCOPES)
    
    # Authorize and return the client
    client = gspread.authorize(creds)
    return client

