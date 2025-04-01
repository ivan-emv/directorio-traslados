import streamlit as st
from firebase_config import init_firestore
from datetime import datetime
import uuid

st.set_page_config(page_title="Gestión de Puntos de Encuentro", layout="wide")

# Inicializar sesión
for key in ["modo", "edit_data", "ciudad_filtro", "puntos", "num_telefonos", "limpiar"]:
    if key not in st.session_state:
        if key == "puntos":
            st.session_state[key] = None
        elif key == "num_telefonos":
            st.session_state[key] = 1
        elif key == "limpiar":
            st.session_state[key] = False
        else:
            st.session_state[key] = None if key in ["edit_data", "ciudad_filtro"] else "nuevo"

# Limpiar formulario
if st.session_state["limpiar"]:
    st.session_state["modo"] = "nuevo"
    st.session_state["edit_data"] = None
    st.session_state["num_telefonos"] = 1
    st.session_state["limpiar"] = False
    for key in list(st.session_state.keys()):
        if key.startswith("titulo_") or key.startswith("numero_") or key in [
            "Ciudad", "Proveedor", "PuntoEncuentro", "NombrePuntoLlegada", "OtroLlegada"
        ]:
            del st.session_state[key]

# Inicializar Firebase
db = init_firestore()

st.title("🧭 Gestión de Puntos de Encuentro - Departamento de Traslados")
st.markdown("---")

# Cargar puntos si es necesario
if st.session_state["puntos"] is None:
    docs = db.collection("puntos_de_encuentro").stream()
    st.session_state["puntos"] = [{"id": doc.id, **doc.to_dict()} for doc in docs if doc.to_dict()]

puntos = st.session_state["puntos"]
ciudades_disponibles = sorted(set(p["ciudad"] for p in puntos if p and "ciudad" in p))

# Layout principal
col_izq, col_der = st.columns([0.4, 0.6])

# ------------------ FORMULARIO ------------------
with col_izq:
    st.subheader("📋 Punto de Encuentro")

    edit_data = st.session_state["edit_data"]
    modo = st.session_state["modo"]

    ciudad = st.text_input("Ciudad", value=edit_data.get("ciudad", "") if edit_data else "", key="Ciudad")

    llegada_opciones = ["Aeropuerto", "Estación de Tren", "Puerto", "Otros"]
    llegada = st.selectbox("Punto de Llegada", llegada_opciones, index=llegada_opciones.index(edit_data["punto_llegada"]) if edit_data else 0)

    nombre_punto_llegada = ""
    otro_llegada = ""

    if llegada in ["Aeropuerto", "Estación de Tren", "Puerto"]:
        nombre_punto_llegada = st.text_input("Nombre del Punto de Llegada", value=edit_data.get("nombre_punto_llegada", "") if edit_data else "", key="NombrePuntoLlegada")

    if llegada == "Otros":
        otro_llegada = st.text_input("Otros (si aplica)", value=edit_data.get("otro_llegada", "") if edit_data else "", key="OtroLlegada")

    proveedor = st.text_input("Nombre del Proveedor", value=edit_data.get("proveedor", "") if edit_data else "", key="Proveedor")

    st.markdown("### 📞 Teléfonos de Contacto")

    if modo == "edit" and edit_data:
        st.session_state["num_telefonos"] = len(edit_data["telefonos"]) or 1

    telefonos = []
    for i in range(st.session_state["num_telefonos"]):
        col1, col2 = st.columns([1, 2])
        tel_val = edit_data["telefonos"][i] if edit_data and i < len(edit_data["telefonos"]) else {"titulo": "", "numero": ""}
        with col1:
            titulo = st.text_input(f"Título {i+1}", value=tel_val["titulo"], key=f"titulo_{i}")
        with col2:
            numero = st.text_input(f"Teléfono {i+1}", value=tel_val["numero"], key=f"numero_{i}")
        if titulo or numero:
            telefonos.append({"titulo": titulo, "numero": numero})

    if st.session_state["num_telefonos"] < 5:
        if st.button("➕ Agregar otro número"):
            st.session_state["num_telefonos"] += 1

    punto_encuentro = st.text_area("Descripción del Punto de Encuentro", value=edit_data.get("punto_encuentro", "") if edit_data else "", key="PuntoEncuentro")

    col_guardar, col_limpiar = st.columns(2)

    with col_guardar:
        if st.button("💾 Guardar Punto"):
            if not ciudad or not proveedor or not punto_encuentro or (llegada != "Otros" and not nombre_punto_llegada):
                st.warning("Por favor, completa todos los campos obligatorios.")
            else:
                data = {
                    "ciudad": ciudad,
                    "punto_llegada": llegada,
                    "nombre_punto_llegada": nombre_punto_llegada,
                    "otro_llegada": otro_llegada,
                    "proveedor": proveedor,
                    "telefonos": telefonos,
                    "punto_encuentro": punto_encuentro,
                    "fecha_actualizacion": datetime.utcnow().isoformat()
                }

                if modo == "edit" and edit_data:
                    doc_id = edit_data["id"]
                    db.collection("puntos_de_encuentro").document(doc_id).set(data)
                    for i, p in enumerate(st.session_state["puntos"]):
                        if p["id"] == doc_id:
                            st.session_state["puntos"][i] = {"id": doc_id, **data}
                            break
                    st.success("✅ Punto actualizado.")
                else:
                    doc_id = str(uuid.uuid4())
                    db.collection("puntos_de_encuentro").document(doc_id).set(data)

                    if not isinstance(st.session_state["puntos"], list):
                        st.session_state["puntos"] = []

                    st.session_state["puntos"].append({"id": doc_id, **data})
                    st.success("✅ Punto creado.")

                st.session_state["limpiar"] = True
                st.session_state["puntos"] = None  # ← fuerza recarga visual desde Firebase

    with col_limpiar:
        if st.button("🧹 Limpiar Formulario"):
            st.session_state["limpiar"] = True

    st.markdown("---")
    st.subheader("🔎 Buscar por Ciudad")
    st.session_state["ciudad_filtro"] = st.selectbox("Selecciona una ciudad", ["Todas"] + ciudades_disponibles)

# ------------------ VISTA DERECHA ------------------
with col_der:
    st.subheader("📍 Puntos de Encuentro")

    filtro = puntos if st.session_state["ciudad_filtro"] == "Todas" else [
        p for p in puntos if p.get("ciudad") == st.session_state["ciudad_filtro"]
    ]

    for punto in filtro:
        with st.expander(f"📌 {punto.get('ciudad', 'Sin Ciudad')} - {punto.get('punto_llegada', 'Sin Llegada')} - {punto.get('nombre_punto_llegada', '')}"):
            st.markdown(f"**Proveedor:** {punto.get('proveedor', 'N/D')}")
            st.markdown(f"**Punto de Encuentro:** {punto.get('punto_encuentro', '')}")
            st.markdown("**Teléfonos de Contacto:**")
            for tel in punto.get("telefonos", []):
                st.markdown(f"- **{tel.get('titulo', '')}**: {tel.get('numero', '')}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Editar", key=f"edit_{punto['id']}"):
                    st.session_state["modo"] = "edit"
                    st.session_state["edit_data"] = punto
            with col2:
                if st.button("🗑️ Eliminar", key=f"delete_{punto['id']}"):
                    db.collection("puntos_de_encuentro").document(punto["id"]).delete()
                    st.session_state["puntos"] = [p for p in st.session_state["puntos"] if p["id"] != punto["id"]]
                    st.success("✅ Punto eliminado correctamente.")
