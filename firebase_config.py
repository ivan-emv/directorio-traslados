import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import json
import base64

@st.cache_resource
def init_firestore():
    # Leer el JSON desde secrets y convertirlo a dict
    key_dict = json.loads(st.secrets["FIREBASE_CREDENTIALS"])
    cred = credentials.Certificate(key_dict)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    return firestore.client()
