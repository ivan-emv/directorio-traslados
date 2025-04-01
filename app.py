import streamlit as st
from firebase_config import init_firestore
from datetime import datetime
import uuid

# Configuración inicial
st.set_page_config(page_title="Gestión de Puntos de Encuentro", layout="wide")

# Inicializar variables de sesión
for key in ["refrescar", "eliminar_id", "edit_id", "ciudad_filtro"]:
    if key not in st.session_state:
        st.session_state[key] = None if key in ["edit_id", "eliminar_id", "ciudad_filtro"] else False

# Ejecutar eliminación si está marcada
if st.session_state["eliminar_id"]:
    db = init_firestore()
    db.collection("puntos_de_encuentro").document(st.session_state["eliminar_id"]).delete()
    st.success("✅ Punto eliminado correctamente.")
    st.session_state["eliminar_id"] = None
    st.session_state["refrescar"] = True

# Ejecutar recarga si fue marcada
if st.session_state["refrescar"]:
    st.session_state["refrescar"] = False
    st.experimental_rerun()

# Inicializar Firebase
db = init_firestore()

st.title("🧭 Gestión de Puntos de Encuentro - Departamento de Traslados")
st.markdown("---")

# Traer datos
docs = db.collection("puntos_de_encuentro").stream()
puntos = [{"id": doc.id, **doc.to_dict()} for doc in docs]
ciudades_disponibles = sorted(set(p["ciudad"] for p in puntos))

# Layout dividido
col_izq, col_der = st.columns([0.4, 0.6])

# ----------------------------------------------
# 📋 Columna izquierda: formulario + selector
# ----------------------------------------------
with col_izq:

    st.subheader("➕ Agregar / Editar Punto")

    # Recuperar punto si está en edición
    punto_edicion = None
    if st.session_state["edit_id"]:
        punto_edicion = next((p for p in puntos if p["id"] == st.session_state["edit_id"]), None)

    ciudad = st.text_input("Ciudad", value=punto_edicion["ciudad"] if punto_edicion else "")
    llegada_opciones = ["Aeropuerto", "Estación de Tren", "Puerto", "Otros"]
    llegada = st.selectbox("Punto de Llegada", llegada_opciones, index=llegada_opciones.index(punto_edicion["punto_llegada"]) if punto_edicion else 0)
    otro_llegada = st.text_input("Otro (si aplica)", value=punto_edicion.get("otro_llegada", "") if punto_edicion else "")
    proveedor = st.text_input("Nombre del Proveedor", value=punto_edicion["proveedor"] if punto_edicion else "")

    telefonos = []
    for i in range(5):
        col1, col2 = st.columns([1, 2])
        tel_val = punto_edicion["telefonos"][i] if punto_edicion and i < len(punto_edicion["telefonos"]) else {"titulo": "", "numero": ""}
        with col1:
            titulo = st.text_input(f"Título {i+1}", value=tel_val["titulo"], key=f"titulo_{i}")
        with col2:
            numero = st.text_input(f"Teléfono {i+1}", value=tel_val["numero"], key=f"numero_{i}")
        if titulo or numero:
            telefonos.append({"titulo": titulo, "numero": numero})

    punto_encuentro = st.text_area("Descripción del Punto de Encuentro", value=punto_edicion["punto_encuentro"] if punto_edicion else "")

    if st.button("💾 Guardar Punto"):
        if not ciudad or not proveedor or not punto_encuentro:
            st.warning("Por favor, completa los campos obligatorios.")
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
            if punto_edicion:
                db.collection("puntos_de_encuentro").document(st.session_state["edit_id"]).set(data)
            else:
                db.collection("puntos_de_encuentro").document(str(uuid.uuid4())).set(data)
            st.success("✅ Punto guardado correctamente.")
            st.session_state["edit_id"] = None
            st.session_state["refrescar"] = True

    st.markdown("---")
    st.subheader("🔎 Buscar por Ciudad")
    st.session_state["ciudad_filtro"] = st.selectbox("Selecciona una ciudad", ["Todas"] + ciudades_disponibles)

# ----------------------------------------------
# 📄 Columna derecha: visualización
# ----------------------------------------------
with col_der:
    st.subheader("📍 Puntos de Encuentro")

    filtro = puntos if st.session_state["ciudad_filtro"] == "Todas" else [
        p for p in puntos if p["ciudad"] == st.session_state["ciudad_filtro"]
    ]

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
                    st.session_state["refrescar"] = True
            with col2:
                if st.button("🗑️ Eliminar", key=f"delete_{punto['id']}"):
                    st.session_state["eliminar_id"] = punto["id"]
                    st.session_state["refrescar"] = True
