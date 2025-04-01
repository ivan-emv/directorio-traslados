import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import base64
import tempfile

@st.cache_resource
def init_firestore():
    encoded = st.secrets["FIREBASE_BASE64"]
    decoded = base64.b64decode(encoded)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as f:
        f.write(decoded)
        cred = credentials.Certificate(f.name)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    return firestore.client()
