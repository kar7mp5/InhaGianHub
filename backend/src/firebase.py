import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

cred_raw = os.environ.get("FIREBASE_CREDENTIALS")
if not cred_raw:
    raise RuntimeError("FIREBASE_CREDENTIALS not found in environment")

try:
    # JSON string directly from env
    cred_dict = json.loads(cred_raw)
except json.JSONDecodeError:
    # Otherwise, assume it's a path
    with open(cred_raw) as f:
        cred_dict = json.load(f)

cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()
