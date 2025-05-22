import streamlit as st
import pandas as pd
import datetime
import os
from gmail_reader import get_sent_emails

# Nombre del archivo para guardar los datos
data_file = 'bd_tracking.csv'

# Función para cargar o crear archivo de seguimiento
def load_data():
    if os.path.exists(data_file):
        return pd.read_csv(data_file)
    else:
        return pd.DataFrame(columns=['Empresa', 'Cliente', 'Semana', 'Acción'])

# Función para guardar los datos
def save_data(df):
    df.to_csv(data_file, index=False)

# Calcular la semana actual
hoy = datetime.date.today()
semana_actual = hoy.isocalendar()[1]

# Cargar datos existentes
df = load_data()

st.title("📈 Seguimiento de BD - Newen")
# Leer correos enviados automáticamente
st.subheader("📬 Acciones detectadas en correos enviados")

if st.button("Leer correos enviados desde Gmail"):
    dominios_relevantes = ['@ypf.com.ar', '@pan-energy.com', '@pampaenergia.com']  # Agregá los que quieras
    correos_df = get_sent_emails(domains=dominios_relevantes, days_back=7)

    nuevas_filas = []
    for _, row in correos_df.iterrows():
        semana_correo = row['Fecha'].isocalendar()[1]
        empresa = ''  # Esto podrías inferirlo según el dominio si querés automatizarlo más
        cliente = row['Destinatario']
        accion = f"Correo: {row['Asunto']} - {row['Resumen']}"
        nuevas_filas.append([empresa, cliente, semana_correo, accion])

    if nuevas_filas:
        df_nuevo = pd.DataFrame(nuevas_filas, columns=['Empresa', 'Cliente', 'Semana', 'Acción'])
        df = pd.concat([df, df_nuevo], ignore_index=True)
        save_data(df)
        st.success(f"✅ Se agregaron {len(nuevas_filas)} acciones desde Gmail.")
    else:
        st.info("📭 No se encontraron correos enviados relevantes en los últimos días.")

# Formulario de entrada
st.subheader("Agregar nueva acción")

with st.form("formulario_entrada"):
    empresa = st.text_input("Empresa representada")
    cliente = st.text_input("Cliente potencial")
    semana = st.number_input("Semana del año", min_value=1, max_value=53, value=semana_actual)
    accion = st.text_area("Acción realizada")
    submitted = st.form_submit_button("Guardar")

    if submitted:
        nueva_fila = pd.DataFrame([[empresa, cliente, semana, accion]], columns=df.columns)
        df = pd.concat([df, nueva_fila], ignore_index=True)
        save_data(df)
        st.success("✅ Acción guardada correctamente")

# Mostrar tabla dinámica
st.subheader("Resumen por empresa y semana")
df_pivot = df.pivot_table(index=['Empresa', 'Cliente'], columns='Semana', values='Acción', aggfunc=lambda x: ' | '.join(x)).fillna('')
st.dataframe(df_pivot, use_container_width=True)

# Generar reporte semanal
def generar_reporte(df, semana):
    df_semana = df[df['Semana'] == semana]
    if df_semana.empty:
        return "No se registraron acciones esta semana."
    reporte = f"📋 **Reporte semanal de acciones (Semana {semana})**\n\n"
    for (empresa, cliente), grupo in df_semana.groupby(['Empresa', 'Cliente']):
        reporte += f"- **{empresa}** - *{cliente}*: {grupo['Acción'].iloc[-1]}\n"
    return reporte

st.subheader("Generar reporte semanal")
semana_reporte = st.number_input("Semana a reportar", min_value=1, max_value=53, value=semana_actual, key='reporte')
if st.button("Generar reporte"):
    reporte_texto = generar_reporte(df, semana_reporte)
    st.markdown(reporte_texto)
    st.download_button("📤 Descargar reporte", data=reporte_texto, file_name=f"reporte_semana_{semana_reporte}.txt")
