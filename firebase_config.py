import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
import base64
import tempfile
import json

@st.cache_resource
def init_firestore():
    try:
        # Leer y decodificar base64 desde secrets
        encoded = st.secrets["FIREBASE_BASE64"]
        decoded = base64.b64decode(encoded)

        # Crear archivo temporal para pasar a Firebase
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="wb") as f:
            f.write(decoded)
            temp_json_path = f.name

        # Verificar que el archivo temporal contiene JSON válido
        with open(temp_json_path, "r") as check_file:
            json.load(check_file)  # Si esto falla, el contenido no es válido

        # Inicializar Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate(temp_json_path)
            firebase_admin.initialize_app(cred)

        return firestore.client()

    except Exception as e:
        st.error("❌ Error al inicializar Firebase. Verifica tu Secret FIREBASE_BASE64.")
        st.stop()
