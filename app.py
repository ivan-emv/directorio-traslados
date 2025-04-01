import streamlit as st
from firebase_config import init_firestore
from datetime import datetime
import uuid

# ✅ Obligatorio: debe ser el primer comando Streamlit
st.set_page_config(page_title="Gestión de Puntos de Encuentro", layout="wide")

# Inicializar conexión con Firebase
db = init_firestore()

st.title("🧭 Gestión de Puntos de Encuentro - Departamento de Traslados")
st.markdown("---")

# ------------------ Función para guardar ------------------ #
def guardar_punto(data, edit_id=None):
    if edit_id:
        db.collection("puntos_de_encuentro").document(edit_id).set(data)
    else:
        db.collection("puntos_de_encuentro").document(str(uuid.uuid4())).set(data)

# ------------------ Formulario de Registro ------------------ #
with st.expander("➕ Agregar / Editar Punto de Encuentro", expanded=False):
    ciudad = st.text_input("Ciudad", placeholder="Ej: Madrid")

    opciones_llegada = ["Aeropuerto", "Estación de Tren", "Puerto", "Otros"]
    llegada = st.selectbox("Punto de Llegada", opciones_llegada)

    otro_llegada = ""
    if llegada == "Otros":
        otro_llegada = st.text_input("Especificar otro punto de llegada")

    proveedor = st.text_input("Nombre del Proveedor de Traslados")

    telefonos = []
    for i in range(5):
        col1, col2 = st.columns([1, 2])
        with col1:
            titulo = st.text_input(f"Título {i+1}", key=f"titulo_{i}")
        with col2:
            numero = st.text_input(f"Teléfono {i+1}", key=f"numero_{i}")
        if titulo or numero:
            telefonos.append({"titulo": titulo, "numero": numero})

    punto_encuentro = st.text_area("Descripción del Punto de Encuentro")

    edit_id = st.session_state.get("edit_id", None)

    if st.button("💾 Guardar Punto"):
        if not ciudad or not proveedor or not punto_encuentro:
            st.warning("Por favor, completa todos los campos obligatorios.")
        else:
            data = {
                "ciudad": ciudad,
                "punto_llegada": llegada,
                "otro_llegada": otro_llegada,
                "proveedor": proveedor,
                "telefonos": telefonos,
                "punto_encuentro": punto_encuentro,
                "fecha_actualizacion": datetime.utcnow().isoformat()
            }
            guardar_punto(data, edit_id)
            st.success("✅ Punto de encuentro guardado exitosamente.")
            st.session_state["edit_id"] = None
            st.experimental_rerun()

# ------------------ Visualización ------------------ #
st.subheader("📍 Puntos de Encuentro Registrados")

# Traer datos desde Firebase
docs = db.collection("puntos_de_encuentro").stream()
puntos = [{"id": doc.id, **doc.to_dict()} for doc in docs]

# Organización por ciudad
ciudades_disponibles = sorted(set(p["ciudad"] for p in puntos))
ciudad_filtro = st.selectbox("Selecciona una ciudad", ["Todas"] + ciudades_disponibles)

filtro = puntos if ciudad_filtro == "Todas" else [p for p in puntos if p["ciudad"] == ciudad_filtro]

for punto in filtro:
    with st.expander(f"📌 {punto['ciudad']} - {punto['punto_llegada']} ({punto.get('otro_llegada','')})"):
        st.markdown(f"**Proveedor:** {punto['proveedor']}")
        st.markdown(f"**Punto de Encuentro:** {punto['punto_encuentro']}")
        st.markdown("**Teléfonos de Contacto:**")
        for tel in punto["telefonos"]:
            st.markdown(f"- **{tel['titulo']}**: {tel['numero']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Editar", key=f"edit_{punto['id']}"):
                st.session_state["edit_id"] = punto["id"]
                st.experimental_rerun()
        with col2:
            if st.button("🗑️ Eliminar", key=f"delete_{punto['id']}"):
                db.collection("puntos_de_encuentro").document(punto["id"]).delete()
                st.success("✅ Punto eliminado correctamente.")
                st.experimental_rerun()
