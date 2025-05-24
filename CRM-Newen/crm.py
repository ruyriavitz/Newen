import streamlit as st
import pandas as pd
from datetime import date

# Cargar datos
def cargar_datos():
    try:
        return pd.read_csv("seguimiento.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["Semana", "Representada", "Cliente", "Etapa", "Nombre", "Apellido", "Correo", "Última Conversación", "Responsable", "Observaciones"])

# Guardar datos
def guardar_datos(df):
    df.to_csv("seguimiento.csv", index=False)

st.set_page_config(page_title="CRM Newen", layout="wide")
st.title("📋 Seguimiento Comercial - Newen")

df = cargar_datos()

st.subheader("➕ Nueva entrada")
with st.form("formulario"):
    semana = st.date_input("Semana", value=date.today())
    representada = st.selectbox("Empresa Representada", ["Revsolz", "Seismos", "8Sigma", "Qnergy"])
    cliente = st.selectbox("Potencial Cliente", ["YPF", "Vista Energy", "Pluspetrol", "Tecpetrol", "PAE", "CGC", "Pampa", "Otro"])
    etapa = st.selectbox("Etapa", ["Introducción", "Technical Evaluation", "Commercial Evaluation", "Pilot", "Contract", "Dormant", "Descartado"])
    nombre = st.text_input("Nombre del contacto")
    apellido = st.text_input("Apellido del contacto")
    correo = st.text_input("Correo")
    ultima_conv = st.text_area("Resumen última conversación")
    responsable = st.text_input("Responsable interno")
    obs = st.text_area("Observaciones")

    submitted = st.form_submit_button("Agregar entrada")
    if submitted:
        nueva_fila = pd.DataFrame([{
            "Semana": semana,
            "Representada": representada,
            "Cliente": cliente,
            "Etapa": etapa,
            "Nombre": nombre,
            "Apellido": apellido,
            "Correo": correo,
            "Última Conversación": ultima_conv,
            "Responsable": responsable,
            "Observaciones": obs
        }])
        df = pd.concat([df, nueva_fila], ignore_index=True)
        guardar_datos(df)
        st.success("✅ Entrada agregada correctamente")

# Visualización
st.subheader("📊 Seguimiento actual")
filtro_cliente = st.multiselect("Filtrar por cliente", df["Cliente"].unique())
filtro_rep = st.multiselect("Filtrar por representada", df["Representada"].unique())
filtro_etapa = st.multiselect("Filtrar por etapa", df["Etapa"].unique())

df_filtrado = df.copy()
if filtro_cliente:
    df_filtrado = df_filtrado[df_filtrado["Cliente"].isin(filtro_cliente)]
if filtro_rep:
    df_filtrado = df_filtrado[df_filtrado["Representada"].isin(filtro_rep)]
if filtro_etapa:
    df_filtrado = df_filtrado[df_filtrado["Etapa"].isin(filtro_etapa)]

st.dataframe(df_filtrado, use_container_width=True)

# Exportación
st.download_button("📥 Descargar Excel", data=df_filtrado.to_csv(index=False), file_name="seguimiento_exportado.csv", mime="text/csv")
