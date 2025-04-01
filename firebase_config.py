import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import json
from ast import literal_eval

@st.cache_resource
def init_firestore():
    # Interpretar el contenido de los secrets como diccionario
    firebase_key = literal_eval(st.secrets["FIREBASE_CREDENTIALS"])
    cred = credentials.Certificate(firebase_key)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    return db
