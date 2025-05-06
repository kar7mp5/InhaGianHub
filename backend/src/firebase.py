import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

cred_json = os.environ.get("FIREBASE_CREDENTIALS")
if not cred_json:
    raise RuntimeError("FIREBASE_CREDENTIALS not found in environment")

cred_dict = json.loads(cred_json)
cred = credentials.Certificate(cred_dict)
firebase_admin.initialize_app(cred)
db = firestore.client()
