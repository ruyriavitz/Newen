import streamlit as st
import pandas as pd
import datetime
import os
from gmail_reader import get_sent_emails

# Archivo donde se guardan los datos
data_file = 'BD_Tracker/bd_tracking.csv'

# Cargar o crear base de datos
def load_data():
    if os.path.exists(data_file):
        return pd.read_csv(data_file)
    else:
        return pd.DataFrame(columns=['Empresa', 'Cliente', 'Semana', 'Acción'])

def save_data(df):
    df.to_csv(data_file, index=False)

# Calcular la semana actual
hoy = datetime.date.today()
semana_actual = hoy.isocalendar()[1]

# Cargar datos
df = load_data()

st.title("📊 Seguimiento BD - Newen")

# Leer correos enviados automáticamente
st.subheader("📬 Acciones detectadas en correos enviados")

if st.button("Leer correos enviados desde Gmail"):
    dominios_relevantes = ['@ypf.com.ar', '@pan-energy.com', '@pampaenergia.com', '@tecpetrol.com', '@pluspetrol.net', '@vistaenergy.com', '@shell.com', '@enap.cl', '@ecopetrol.com.co', '@eneva.com.br']
    correos_df = get_sent_emails(domains=dominios_relevantes, days_back=7)

    nuevas_filas = []
    for _, row in correos_df.iterrows():
        semana_correo = row['Fecha'].isocalendar()[1]
        empresa = row['Empresa']
        cliente = row['Cliente']
        accion = f"Correo: {row['Asunto']} - {row['Resumen']}"
        nuevas_filas.append([empresa, cliente, semana_correo, accion])

    if nuevas_filas:
        df_nuevo = pd.DataFrame(nuevas_filas, columns=['Empresa', 'Cliente', 'Semana', 'Acción'])
        df = pd.concat([df, df_nuevo], ignore_index=True)
        save_data(df)
        st.success(f"✅ Se agregaron {len(nuevas_filas)} acciones desde Gmail.")
    else:
        st.info("📭 No se encontraron correos enviados relevantes en los últimos días.")

# Formulario de entrada manual
st.subheader("Registrar nueva acción")
with st.form("entrada"):
    empresa = st.text_input("Empresa representada")
    cliente = st.text_input("Cliente potencial")
    semana = st.number_input("Semana del año", min_value=1, max_value=53, value=semana_actual)
    accion = st.text_area("Acción realizada")
    submitted = st.form_submit_button("Guardar")

    if submitted:
        nueva_fila = pd.DataFrame([[empresa, cliente, semana, accion]], columns=df.columns)
        df = pd.concat([df, nueva_fila], ignore_index=True)
        save_data(df)
        st.success("✅ Acción registrada correctamente.")

# Tabla dinámica
st.subheader("Resumen semanal")
df_pivot = df.pivot_table(index=['Empresa', 'Cliente'], columns='Semana', values='Acción', aggfunc=lambda x: ' | '.join(x)).fillna('')
st.dataframe(df_pivot, use_container_width=True)

# Generar reporte
def generar_reporte(df, semana):
    df_semana = df[df['Semana'] == semana]
    if df_semana.empty:
        return "No se registraron acciones esta semana."
    reporte = f"📋 Reporte semanal (Semana {semana})\n\n"
    for (empresa, cliente), grupo in df_semana.groupby(['Empresa', 'Cliente']):
        reporte += f"- {empresa} - {cliente}: {grupo['Acción'].iloc[-1]}\n"
    return reporte

st.subheader("Reporte para enviar al cliente")
semana_reporte = st.number_input("Seleccionar semana", min_value=1, max_value=53, value=semana_actual, key="reporte")
if st.button("Generar reporte"):
    texto_reporte = generar_reporte(df, semana_reporte)
    st.text_area("Reporte generado", texto_reporte, height=300)
    st.download_button("📥 Descargar reporte", data=texto_reporte, file_name=f"reporte_semana_{semana_reporte}.txt")