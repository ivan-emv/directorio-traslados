import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
import streamlit as st

@st.cache_resource
def init_firestore():
    # Cargar las credenciales desde secrets
    firebase_key = json.loads(st.secrets["FIREBASE_CREDENTIALS"])
    cred = credentials.Certificate(firebase_key)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    return db
