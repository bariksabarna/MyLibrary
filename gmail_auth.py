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

import os
import base64
from email.mime.text import MIMEText
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

# ─── Config (read once at startup) ──────────────────────────
FROM_EMAIL     = os.getenv("GMAIL_FROM_EMAIL",    "randompas112000@gmail.com")
CLIENT_ID      = os.getenv("GMAIL_CLIENT_ID",     "")
CLIENT_SECRET  = os.getenv("GMAIL_CLIENT_SECRET", "")
REFRESH_TOKEN  = os.getenv("GMAIL_REFRESH_TOKEN", "")
TOKEN_URI      = os.getenv("GMAIL_TOKEN_URI",     "https://oauth2.googleapis.com/token")


def get_gmail_service():
    """
    Build Gmail service from refresh token.
    - Access token is fetched/refreshed automatically on each call.
    - No browser, no pickle, no file writes — safe for all cloud hosts.
    - Refresh token never expires unless manually revoked in Google account.
    """
    if not REFRESH_TOKEN or not CLIENT_ID or not CLIENT_SECRET:
        raise RuntimeError(
            "Gmail credentials missing. Set GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, "
            "and GMAIL_REFRESH_TOKEN in your environment variables."
        )

    # Build credentials from raw fields — access_token=None forces an immediate refresh
    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri=TOKEN_URI,
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=['https://www.googleapis.com/auth/gmail.send'],
    )

    # This fetches a fresh access token using the refresh token — no browser needed
    creds.refresh(Request())

    return build('gmail', 'v1', credentials=creds)


def send_gmail(to_email, subject, body_html):
    """Send an HTML email via Gmail API. Returns True on success, False on failure."""
    try:
        service = get_gmail_service()
        message = MIMEText(body_html, 'html')
        message['to']      = to_email
        message['from']    = FROM_EMAIL
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        result = service.users().messages().send(userId='me', body={'raw': raw}).execute()
        print(f"Gmail: sent to {to_email} (id={result.get('id')})")
        return True
    except Exception as e:
        print(f"Gmail: ERROR sending to {to_email} — {e}")
        return False
