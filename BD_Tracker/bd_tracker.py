import streamlit as st
import pandas as pd
import datetime
import os

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
