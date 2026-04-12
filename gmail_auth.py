# Copyright © Sabarna Barik 
# 
# This code is open-source for **educational and non-commercial purposes only**.
# 
# You may:
# - Read, study, and learn from this code.
# - Modify or experiment with it for personal learning.
# 
# You may NOT:
# - Claim this code as your own.
# - Use this code in commercial projects or for profit without written permission.
# - Distribute this code as your own work.
# 
# If you use or adapt this code, you **must give credit** to the original author: Sabarna Barik
# For commercial use or special permissions, contact: sabarnabarik@gmail.com
# 
# # Copyright © 2026 Sabarna Barik
# # Non-commercial use only. Credit required if used.
# 
# License:
# This project is open-source for learning only.
# Commercial use is prohibited.
# Credit is required if you use any part of this code.

# gmail_auth.py
import pickle, base64
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
import os, io, json
from dotenv import load_dotenv

load_dotenv()

# ─── EMBEDDED CREDENTIALS ───────────────────────────────
CREDENTIALS_JSON_STR = os.getenv("GMAIL_CREDENTIALS_JSON", '{}')
try:
    CREDENTIALS_JSON = json.loads(CREDENTIALS_JSON_STR)
except Exception:
    CREDENTIALS_JSON = {}

TOKEN_B64 = os.getenv("GMAIL_TOKEN_B64", "")
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
FROM_EMAIL = os.getenv("GMAIL_FROM_EMAIL", "randompas112000@gmail.com")


def get_gmail_service():
    # Load token from embedded string
    creds = None
    if TOKEN_B64:
        try:
            creds = pickle.loads(base64.b64decode(TOKEN_B64))
        except Exception as e:
            print(f"Gmail Auth: Failed to load token from environment: {e}")
            creds = None

    # Refresh if expired
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Local auth fallback (only needed once)
            flow = InstalledAppFlow.from_client_config(CREDENTIALS_JSON, SCOPES)
            creds = flow.run_local_server(port=0)

    service = build('gmail', 'v1', credentials=creds)
    return service


def send_gmail(to_email, subject, body_html):
    service = get_gmail_service()
    message = MIMEText(body_html, 'html')
    message['to'] = to_email
    message['from'] = FROM_EMAIL
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    try:
        msg = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        print(f"Gmail sent to {to_email}, id={msg['id']}")
        return True
    except Exception as e:
        print(f"Gmail error: {e}")
        return False
