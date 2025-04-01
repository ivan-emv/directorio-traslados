import streamlit as st
from firebase_config import init_firestore
from datetime import datetime
import uuid

# Configuración inicial
st.set_page_config(page_title="Gestión de Puntos de Encuentro", layout="wide")

# Inicializar variables de sesión
for key in ["modo", "edit_data", "ciudad_filtro"]:
    if key not in st.session_state:
        st.session_state[key] = None if key in ["edit_data", "ciudad_filtro"] else "nuevo"

# Inicializar Firebase
db = init_firestore()

st.title("🧭 Gestión de Puntos de Encuentro - Departamento de Traslados")
st.markdown("---")

# Traer datos desde Firebase
docs = db.collection("puntos_de_encuentro").stream()
puntos = [{"id": doc.id, **doc.to_dict()} for doc in docs]
ciudades_disponibles = sorted(set(p["ciudad"] for p in puntos))

# Layout 40/60
col_izq, col_der = st.columns([0.4, 0.6])

# ------------------ COLUMNA IZQUIERDA ------------------
with col_izq:
    st.subheader("📋 Punto de Encuentro")

    edit_data = st.session_state["edit_data"]
    modo = st.session_state["modo"]

    ciudad = st.text_input("Ciudad", value=edit_data["ciudad"] if edit_data else "")

    llegada_opciones = ["Aeropuerto", "Estación de Tren", "Puerto", "Otros"]
    llegada = st.selectbox("Punto de Llegada", llegada_opciones, index=llegada_opciones.index(edit_data["punto_llegada"]) if edit_data else 0)

    # Mostrar caja para especificar el nombre del punto de llegada (Orly, Atocha, etc.)
    nombre_punto_llegada = st.text_input("Nombre del Punto de Llegada", value=edit_data.get("nombre_punto_llegada", "") if edit_data else "")

    # Mostrar "Otro (si aplica)" solo si se selecciona "Otros"
    otro_llegada = ""
    if llegada == "Otros":
        otro_llegada = st.text_input("Otro (si aplica)", value=edit_data.get("otro_llegada", "") if edit_data else "")

    proveedor = st.text_input("Nombre del Proveedor", value=edit_data["proveedor"] if edit_data else "")

    telefonos = []
    for i in range(5):
        col1, col2 = st.columns([1, 2])
        tel_val = edit_data["telefonos"][i] if edit_data and i < len(edit_data["telefonos"]) else {"titulo": "", "numero": ""}
        with col1:
            titulo = st.text_input(f"Título {i+1}", value=tel_val["titulo"], key=f"titulo_{i}")
        with col2:
            numero = st.text_input(f"Teléfono {i+1}", value=tel_val["numero"], key=f"numero_{i}")
        if titulo or numero:
            telefonos.append({"titulo": titulo, "numero": numero})

    punto_encuentro = st.text_area("Descripción del Punto de Encuentro", value=edit_data["punto_encuentro"] if edit_data else "")

    if st.button("💾 Guardar Punto"):
        if not ciudad or not proveedor or not punto_encuentro or not nombre_punto_llegada:
            st.warning("Por favor, completa todos los campos obligatorios.")
        else:
            data = {
                "ciudad": ciudad,
                "punto_llegada": llegada,
                "nombre_punto_llegada": nombre_punto_llegada,
                "otro_llegada": otro_llegada if llegada == "Otros" else "",
                "proveedor": proveedor,
                "telefonos": telefonos,
                "punto_encuentro": punto_encuentro,
                "fecha_actualizacion": datetime.utcnow().isoformat()
            }

            if modo == "edit" and edit_data:
                db.collection("puntos_de_encuentro").document(edit_data["id"]).set(data)
                st.success("✅ Punto actualizado.")
            else:
                db.collection("puntos_de_encuentro").document(str(uuid.uuid4())).set(data)
                st.success("✅ Punto creado.")
            
            # Resetear modo
            st.session_state["modo"] = "nuevo"
            st.session_state["edit_data"] = None
            st.query_params["saved"] = "true"

    st.markdown("---")
    st.subheader("🔎 Buscar por Ciudad")
    st.session_state["ciudad_filtro"] = st.selectbox("Selecciona una ciudad", ["Todas"] + ciudades_disponibles)

# ------------------ COLUMNA DERECHA ------------------
with col_der:
    st.subheader("📍 Puntos de Encuentro")

    filtro = puntos if st.session_state["ciudad_filtro"] == "Todas" else [
        p for p in puntos if p["ciudad"] == st.session_state["ciudad_filtro"]
    ]

    for punto in filtro:
        with st.expander(f"📌 {punto['ciudad']} - {punto['punto_llegada']} - {punto.get('nombre_punto_llegada', '')}"):
            st.markdown(f"**Proveedor:** {punto['proveedor']}")
            st.markdown(f"**Punto de Encuentro:** {punto['punto_encuentro']}")
            st.markdown("**Teléfonos de Contacto:**")
            for tel in punto["telefonos"]:
                st.markdown(f"- **{tel['titulo']}**: {tel['numero']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Editar", key=f"edit_{punto['id']}"):
                    st.session_state["modo"] = "edit"
                    st.session_state["edit_data"] = punto
            with col2:
                if st.button("🗑️ Eliminar", key=f"delete_{punto['id']}"):
                    db.collection("puntos_de_encuentro").document(punto["id"]).delete()
                    st.success("✅ Punto eliminado correctamente.")
