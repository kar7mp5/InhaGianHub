import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

"""
Initializes Firebase Firestore connection depending on environment.

- In development: loads credentials from `firebase_credentials.json` file.
- In production: loads JSON string from FIREBASE_CREDENTIALS environment variable.
"""

ENV = os.getenv("ENV", "dev")  # default to development
cred_dict = None

if ENV == "dev":
    # Development: Load from local file
    try:
        with open("firebase_credentials.json") as f:
            cred_dict = json.load(f)
    except FileNotFoundError:
        raise RuntimeError("firebase_credentials.json file not found for development environment")
else:
    # Production: Load from environment variable
    cred_raw = os.environ.get("FIREBASE_CREDENTIALS")
    if not cred_raw:
        raise RuntimeError("FIREBASE_CREDENTIALS not found in environment")
    try:
        cred_dict = json.loads(cred_raw)
    except json.JSONDecodeError:
        # Fallback to assuming it's a file path
        with open(cred_raw) as f:
            cred_dict = json.load(f)

cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()
