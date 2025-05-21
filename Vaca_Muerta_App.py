import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import plotly.express as px

ggl_url='https://drive.google.com/uc?id=1gdB9iv8xcYrMMsQGwWOUSzQkJNu6k9Au'

st.set_page_config(page_title="Dashboard Vaca Muerta", layout="wide")

st.image(logo.png, width=100)
st.title("Dashboard de Producción - Vaca Muerta")

@st.cache_data
def cargar_datos():
    df = pd.read_csv(ggl_url, parse_dates=['fecha_data'])
    return df

df = cargar_datos()

# Normalizar nombre de compañía
principales = [
    'YPF', 'Vista Energy', 'Pluspetrol', 'Tecpetrol',
    'Pan American Energy', 'Pampa', 'Exxon', 'Shell', 'Total Energies'
]
def keep_main_or_other(nombre):
    if nombre in principales:
        return nombre
    elif pd.isnull(nombre):
        return 'Otros'
    else:
        return 'Otros'

if 'empresa_filtrada' not in df.columns:
    df['empresa_filtrada'] = df['empresa_unificada'].apply(keep_main_or_other)

# ---- FILTROS JERÁRQUICOS ----
st.sidebar.header("Filtros")
empresas_unicas = sorted(df['empresa_filtrada'].dropna().unique())
yacimientos_todos = sorted(df['areayacimiento'].dropna().unique())

# 1. Definí primero la compañía y yacimiento seleccionados (por defecto)
cia_sel = None
yac_sel = None

# 2. Lógica de filtros jerárquicos
if 'pozo' not in st.session_state:
    st.session_state['pozo'] = 'Todos'

# Selección de compañía
cia_sel = st.sidebar.selectbox('Compañía', ['Todos'] + empresas_unicas, key="cia")

# Selección de yacimiento (depende de compañía)
if cia_sel == 'Todos':
    yac_filtros = yacimientos_todos
else:
    yac_filtros = sorted(df[df['empresa_filtrada'] == cia_sel]['areayacimiento'].dropna().unique())
yac_sel = st.sidebar.selectbox('Yacimiento', ['Todos'] + yac_filtros, key="yac")

# Ahora definí los pozos filtrados según compañía y yacimiento seleccionados
if cia_sel == 'Todos' and yac_sel == 'Todos':
    pozos_filtrados = sorted(df['sigla'].dropna().unique())
elif cia_sel != 'Todos' and yac_sel == 'Todos':
    pozos_filtrados = sorted(df[df['empresa_filtrada'] == cia_sel]['sigla'].dropna().unique())
elif cia_sel == 'Todos' and yac_sel != 'Todos':
    pozos_filtrados = sorted(df[df['areayacimiento'] == yac_sel]['sigla'].dropna().unique())
else:
    pozos_filtrados = sorted(df[(df['empresa_filtrada'] == cia_sel) & (df['areayacimiento'] == yac_sel)]['sigla'].dropna().unique())

sigla_selected = st.sidebar.selectbox(
    'Pozo (sigla)',
    options=['Todos'] + pozos_filtrados,
    key="pozo"
)

# Si seleccionás un pozo, que te muestre su compañía y yacimiento automáticamente
if sigla_selected != 'Todos':
    info_pozo = df[df['sigla'] == sigla_selected].iloc[0]
    st.sidebar.markdown(f"**Compañía:** {info_pozo['empresa_filtrada']}")
    st.sidebar.markdown(f"**Yacimiento:** {info_pozo['areayacimiento']}")
    # (podés bloquear los selectbox de arriba si querés, pero así ya lo informa)
    cia_sel = info_pozo['empresa_filtrada']
    yac_sel = info_pozo['areayacimiento']

# ---- FILTRAR LA BASE SEGÚN LO SELECCIONADO ----
df_filtro = df.copy()
if sigla_selected != 'Todos':
    df_filtro = df_filtro[df_filtro['sigla'] == sigla_selected]
else:
    if cia_sel != 'Todos':
        df_filtro = df_filtro[df_filtro['empresa_filtrada'] == cia_sel]
    if yac_sel != 'Todos':
        df_filtro = df_filtro[df_filtro['areayacimiento'] == yac_sel]

# STACKED: Petróleo y Gas por año de inicio

prod_pet = (
    df_filtro.groupby(['fecha_data', 'anio_inicio'])['pet_bpd'].sum().reset_index()
)
prod_gas = (
    df_filtro.groupby(['fecha_data', 'anio_inicio'])['gas_mm3d'].sum().reset_index()
)

fig_pet = go.Figure()
for anio in sorted(prod_pet['anio_inicio'].dropna().unique()):
    datos = prod_pet[prod_pet['anio_inicio'] == anio]
    fig_pet.add_trace(
        go.Scatter(
            x=datos['fecha_data'],
            y=datos['pet_bpd'],
            mode='lines',
            stackgroup='one',
            name=f"Año {int(anio)}"
        )
    )
fig_pet.update_layout(
    title="Petróleo (BPD) - Stacked por año de inicio",
    xaxis_title="Fecha",
    yaxis_title="Petróleo (BPD)",
    legend_title="Año de inicio",
    height=400
)

fig_gas = go.Figure()
for anio in sorted(prod_gas['anio_inicio'].dropna().unique()):
    datos = prod_gas[prod_gas['anio_inicio'] == anio]
    fig_gas.add_trace(
        go.Scatter(
            x=datos['fecha_data'],
            y=datos['gas_mm3d'],
            mode='lines',
            stackgroup='one',
            name=f"Año {int(anio)}"
        )
    )
fig_gas.update_layout(
    title="Gas (Mm³/d) - Stacked por año de inicio",
    xaxis_title="Fecha",
    yaxis_title="Gas (Mm³/d)",
    legend_title="Año de inicio",
    height=400
)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Petróleo")
    st.plotly_chart(fig_pet, use_container_width=True)
with col2:
    st.subheader("Gas")
    st.plotly_chart(fig_gas, use_container_width=True)



# --- PIE CHART por año de inicio, usando el penúltimo mes ---

col1, col2 = st.columns(2)


# Filtrá solo el penúltimo mes para petróleo

last_month = df_filtro['fecha_data'].max().to_period('M')
penult_month = (last_month - 1).to_timestamp()
df_mes = df_filtro[df_filtro['fecha_data'].dt.to_period('M') == penult_month.to_period('M')]

pie_pet_ano = df_mes.groupby('anio_inicio')['pet_bpd'].sum().reset_index()
pie_pet_ano = pie_pet_ano.sort_values('pet_bpd', ascending=False)
umbral = 0.02
total = pie_pet_ano['pet_bpd'].sum()
pie_pet_ano['porcentaje'] = pie_pet_ano['pet_bpd'] / total
main = pie_pet_ano[pie_pet_ano['porcentaje'] >= umbral]
otros = pie_pet_ano[pie_pet_ano['porcentaje'] < umbral]
otros_sum = otros['pet_bpd'].sum()
pie_pet_ano_agg = main.copy()
if otros_sum > 0:
    pie_pet_ano_agg = pd.concat([
        pie_pet_ano_agg,
        pd.DataFrame([{'anio_inicio': 'Otros', 'pet_bpd': otros_sum, 'porcentaje': otros_sum / total}])
    ], ignore_index=True)

fig_pie_pet_ano = px.pie(
    pie_pet_ano_agg,
    names='anio_inicio',
    values='pet_bpd',
    title=f"Participación por año de inicio (Petróleo) – {penult_month.strftime('%Y-%m')}",
    hole=0.4
)
fig_pie_pet_ano.update_traces(textinfo='percent+label')

# --- GAS PIE CHART ---
pie_gas_ano = df_mes.groupby('anio_inicio')['gas_mm3d'].sum().reset_index()
pie_gas_ano = pie_gas_ano.sort_values('gas_mm3d', ascending=False)
total_gas = pie_gas_ano['gas_mm3d'].sum()
pie_gas_ano['porcentaje'] = pie_gas_ano['gas_mm3d'] / total_gas
main_gas = pie_gas_ano[pie_gas_ano['porcentaje'] >= umbral]
otros_gas = pie_gas_ano[pie_gas_ano['porcentaje'] < umbral]
otros_sum_gas = otros_gas['gas_mm3d'].sum()
pie_gas_ano_agg = main_gas.copy()
if otros_sum_gas > 0:
    pie_gas_ano_agg = pd.concat([
        pie_gas_ano_agg,
        pd.DataFrame([{'anio_inicio': 'Otros', 'gas_mm3d': otros_sum_gas, 'porcentaje': otros_sum_gas / total_gas}])
    ], ignore_index=True)

fig_pie_gas_ano = px.pie(
    pie_gas_ano_agg,
    names='anio_inicio',
    values='gas_mm3d',
    title=f"Participación por año de inicio (Gas) – {penult_month.strftime('%Y-%m')}",
    hole=0.4
)
fig_pie_gas_ano.update_traces(textinfo='percent+label')

# --- MOSTRAR EN DOS COLUMNAS ---
with col1:
    st.plotly_chart(fig_pie_pet_ano, use_container_width=True)
with col2:
    st.plotly_chart(fig_pie_gas_ano, use_container_width=True)


# STACKED: Petróleo y Gas por Compañía
prod_pet = (
    df_filtro.groupby(['fecha_data', 'empresa_filtrada'])['pet_bpd'].sum().reset_index()
)
prod_gas = (
    df_filtro.groupby(['fecha_data', 'empresa_filtrada'])['gas_mm3d'].sum().reset_index()
)

fig_pet = go.Figure()
for empresa in sorted(prod_pet['empresa_filtrada'].dropna().unique()):
    datos = prod_pet[prod_pet['empresa_filtrada'] == empresa]
    fig_pet.add_trace(
        go.Scatter(
            x=datos['fecha_data'],
            y=datos['pet_bpd'],
            mode='lines',
            stackgroup='one',
            name=(empresa)
        )
    )
fig_pet.update_layout(
    title="Petróleo (BPD) - Stacked por Compañía",
    xaxis_title="Fecha",
    yaxis_title="Petróleo (BPD)",
    legend_title="Compañía",
    height=400
)

fig_gas = go.Figure()
for empresa in sorted(prod_gas['empresa_filtrada'].dropna().unique()):
    datos = prod_gas[prod_gas['empresa_filtrada'] == empresa]
    fig_gas.add_trace(
        go.Scatter(
            x=datos['fecha_data'],
            y=datos['gas_mm3d'],
            mode='lines',
            stackgroup='one',
            name=(empresa)
        )
    )
fig_gas.update_layout(
    title="Gas (Mm³/d) - Stacked por Compañía",
    xaxis_title="Fecha",
    yaxis_title="Gas (Mm³/d)",
    legend_title="Compañia",
    height=400
)

col1, col2 = st.columns(2)
with col1:
    st.subheader("Visualizaciones de Petróleo")
    st.plotly_chart(fig_pet, use_container_width=True)
with col2:
    st.subheader("Visualizaciones de Gas")
    st.plotly_chart(fig_gas, use_container_width=True)

 # --- PIE CHART por compañía, usando el penúltimo mes ---
# Si no existe, podés crear prod_pet_cia y prod_gas_cia igual que prod_pet pero agrupando por compañía
import plotly.express as px

# --- PIE CHART: Producción por compañía (solo penúltimo mes, "Otros" <5%) ---
umbral = 0.05

# Petróleo
pie_pet_cia = df_mes.groupby('empresa_filtrada')['pet_bpd'].sum().reset_index()
pie_pet_cia = pie_pet_cia.sort_values('pet_bpd', ascending=False)
total_cia = pie_pet_cia['pet_bpd'].sum()
pie_pet_cia['porcentaje'] = pie_pet_cia['pet_bpd'] / total_cia
main_cia = pie_pet_cia[pie_pet_cia['porcentaje'] >= umbral]
otros_cia = pie_pet_cia[pie_pet_cia['porcentaje'] < umbral]
otros_sum_cia = otros_cia['pet_bpd'].sum()
pie_pet_cia_agg = main_cia.copy()
if otros_sum_cia > 0:
    pie_pet_cia_agg = pd.concat([
        pie_pet_cia_agg,
        pd.DataFrame([{'empresa_filtrada': 'Otros', 'pet_bpd': otros_sum_cia, 'porcentaje': otros_sum_cia / total_cia}])
    ], ignore_index=True)

fig_pie_pet_cia = px.pie(
    pie_pet_cia_agg,
    names='empresa_filtrada',
    values='pet_bpd',
    title=f"Participación por compañía (Petróleo) – {penult_month.strftime('%Y-%m')}",
    hole=0.4
)
fig_pie_pet_cia.update_traces(textinfo='percent+label')

# Gas
pie_gas_cia = df_mes.groupby('empresa_filtrada')['gas_mm3d'].sum().reset_index()
pie_gas_cia = pie_gas_cia.sort_values('gas_mm3d', ascending=False)
total_gas_cia = pie_gas_cia['gas_mm3d'].sum()
pie_gas_cia['porcentaje'] = pie_gas_cia['gas_mm3d'] / total_gas_cia
main_gas_cia = pie_gas_cia[pie_gas_cia['porcentaje'] >= umbral]
otros_gas_cia = pie_gas_cia[pie_gas_cia['porcentaje'] < umbral]
otros_sum_gas_cia = otros_gas_cia['gas_mm3d'].sum()
pie_gas_cia_agg = main_gas_cia.copy()
if otros_sum_gas_cia > 0:
    pie_gas_cia_agg = pd.concat([
        pie_gas_cia_agg,
        pd.DataFrame([{'empresa_filtrada': 'Otros', 'gas_mm3d': otros_sum_gas_cia, 'porcentaje': otros_sum_gas_cia / total_gas_cia}])
    ], ignore_index=True)

fig_pie_gas_cia = px.pie(
    pie_gas_cia_agg,
    names='empresa_filtrada',
    values='gas_mm3d',
    title=f"Participación por compañía (Gas) – {penult_month.strftime('%Y-%m')}",
    hole=0.4
)
fig_pie_gas_cia.update_traces(textinfo='percent+label')

# --- MOSTRAR EN DOS COLUMNAS ---
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(fig_pie_pet_cia, use_container_width=True)
with col2:
    st.plotly_chart(fig_pie_gas_cia, use_container_width=True)


st.info("Selecciona filtros en la barra lateral para ver los resultados actualizados por Compañía, Yacimiento y Pozo")

# --- FUNCIONES Y DATA PARA TABS (Pozos promedio/acumulada y KPIs) ---
def fig_promedio(df, y_col, title, y_label):
    fig = go.Figure()
    for anio in sorted(df['anio_inicio'].dropna().unique()):
        datos = df[df['anio_inicio'] == anio]
        fig.add_trace(
            go.Scatter(
                x=datos['mes_desde_inicio'],
                y=datos[y_col],
                mode='lines',
                name=f"Año {int(anio)}"
            )
        )
    fig.update_layout(
        title=title,
        xaxis_title="Mes desde Inicio",
        yaxis_title=y_label,
        legend_title="Año de inicio",
        height=400
    )
    fig.update_xaxes(range=[0, 12])
    return fig

# --- DATA PARA PROMEDIO Y ACUMULADA ---
df_oil = df_filtro[
    (df_filtro['tipopozo'].str.upper().str.strip() == 'PETROLÍFERO') &
    (df_filtro['anio_inicio'] > 2017)
]
df_gas = df_filtro[
    (df_filtro['tipopozo'].str.upper().str.strip() == 'GASÍFERO') &
    (df_filtro['anio_inicio'] > 2017)
]

pozo_prom_pet = (
    df_oil.groupby(['anio_inicio', 'mes_desde_inicio'])['pet_bpd']
    .mean().reset_index()
)
pozo_acum_pet = (
    df_oil.groupby(['anio_inicio', 'mes_desde_inicio'])['pet_mbbl_acum']
    .mean().reset_index()
)
pozo_prom_gas = (
    df_gas.groupby(['anio_inicio', 'mes_desde_inicio'])['gas_mm3d']
    .mean().reset_index()
)
pozo_acum_gas = (
    df_gas.groupby(['anio_inicio', 'mes_desde_inicio'])['gas_bcf_acum']
    .mean().reset_index()
)

# Pozo individual
show_indiv_pet = False
show_indiv_gas = False
if df_filtro['sigla'].nunique() == 1:
    pozo_ind = df_filtro['sigla'].iloc[0]
    df_pozo = df_filtro[df_filtro['sigla'] == pozo_ind].sort_values('mes_desde_inicio')
    if df_pozo['tipopozo'].str.upper().str.strip().iloc[0] == 'PETROLÍFERO':
        show_indiv_pet = True
        fig_pozo_indiv_pet = go.Figure()
        fig_pozo_indiv_pet.add_trace(go.Scatter(
            x=df_pozo['mes_desde_inicio'],
            y=df_pozo['pet_bpd'],
            mode='lines+markers',
            name=f"Pozo {pozo_ind} (BPD)"
        ))
        fig_pozo_indiv_pet.add_trace(go.Scatter(
            x=df_pozo['mes_desde_inicio'],
            y=df_pozo['pet_mbbl_acum'],
            mode='lines+markers',
            name=f"Pozo {pozo_ind} (Acum Mbbls)",
            yaxis='y2'
        ))
        fig_pozo_indiv_pet.update_layout(
            title=f"Producción diaria y acumulada - {pozo_ind}",
            xaxis_title="Mes desde Inicio",
            yaxis=dict(title="Petróleo (BPD)"),
            yaxis2=dict(title="Acumulado (Mbbls)", overlaying='y', side='right'),
            legend_title="Curva"
        )
    elif df_pozo['tipopozo'].str.upper().str.strip().iloc[0] == 'GASÍFERO':
        show_indiv_gas = True
        fig_pozo_indiv_gas = go.Figure()
        fig_pozo_indiv_gas.add_trace(go.Scatter(
            x=df_pozo['mes_desde_inicio'],
            y=df_pozo['gas_mm3d'],
            mode='lines+markers',
            name=f"Pozo {pozo_ind} (Mm³/d)"
        ))
        fig_pozo_indiv_gas.add_trace(go.Scatter(
            x=df_pozo['mes_desde_inicio'],
            y=df_pozo['gas_bcf_acum'],
            mode='lines+markers',
            name=f"Pozo {pozo_ind} (Acum Bcf)",
            yaxis='y2'
        ))
        fig_pozo_indiv_gas.update_layout(
            title=f"Producción diaria y acumulada - {pozo_ind}",
            xaxis_title="Mes desde Inicio",
            yaxis=dict(title="Gas (Mm³/d)"),
            yaxis2=dict(title="Acumulado (Bcf)", overlaying='y', side='right'),
            legend_title="Curva"
        )

# --- TABS: Pozos promedio / KPIs ---
tab_tipo, tab_kpi = st.tabs(["Pozos promedio", "KPIs 6m"])

with tab_tipo:
    st.subheader("Pozos promedio por año de inicio")
    col1, col2 = st.columns(2)
    # Selector tipo de curva
    tipo_curva = st.radio(
        "Tipo de curva a visualizar",
        options=["Producción promedio mensual", "Acumulada promedio mes a mes"],
        index=0,
        horizontal=True
    )

    with col1:
        
        if tipo_curva == "Producción promedio mensual":
            st.plotly_chart(fig_promedio(pozo_prom_pet, 'pet_bpd', "Pozo Promedio por Año de Inicio (Petróleo)", "Petróleo promedio (BPD)"), use_container_width=True)
        else:
            st.plotly_chart(fig_promedio(pozo_acum_pet, 'pet_mbbl_acum', "Pozo Promedio Acumulado por Año (Petróleo)", "Petróleo acumulado promedio (Mbbls)"), use_container_width=True)


    with col2:
        if tipo_curva == "Producción promedio mensual":
            st.plotly_chart(fig_promedio(pozo_prom_gas, 'gas_mm3d', "Pozo Promedio por Año de Inicio (Gas)", "Gas promedio (Mm³/d)"), use_container_width=True)
        else:
            st.plotly_chart(fig_promedio(pozo_acum_gas, 'gas_bcf_acum', "Pozo Promedio Acumulado por Año (Gas)", "Gas acumulado promedio (Bcf)"), use_container_width=True)

    if show_indiv_pet or show_indiv_gas:
        st.markdown("### Pozo individual seleccionado")
        if show_indiv_pet:
            st.plotly_chart(fig_pozo_indiv_pet, use_container_width=True)
        elif show_indiv_gas:
            st.plotly_chart(fig_pozo_indiv_gas, use_container_width=True)


with tab_kpi:
    st.subheader("KPIs de 6 meses por año de inicio")
    col1, col2 = st.columns(2)
    # --- KPI GAS ---
    df_gas['gas6m_x_lateral_m3'] = df_gas['gas6m_x_lateral'] * 1000
    df_gas['gas6m_x_arena_m3']   = df_gas['gas6m_x_arena'] * 1000
    df_gas['gas6m_x_frac_m3']    = df_gas['gas6m_x_frac'] * 1000

    gas_labels = {
        'gas6m_x_lateral_m3': 'Gas 6m / Lateral (m³/m)',
        'gas6m_x_arena_m3':   'Gas 6m / Arena (m³/tn)',
        'gas6m_x_frac_m3':    'Gas 6m / Frac (m³/frac)'
    }
    fig_gas_kpi = go.Figure()
    for col, label in gas_labels.items():
        fig_gas_kpi.add_trace(go.Bar(
            x=df_gas['anio_inicio'],
            y=df_gas[col],
            name=label,
            visible=(col == 'gas6m_x_lateral_m3')
        ))
    buttons_gas = []
    for i, (col, label) in enumerate(gas_labels.items()):
        vis = [False] * len(gas_labels)
        vis[i] = True
        buttons_gas.append(dict(
            label=label,
            method="update",
            args=[{"visible": vis},
                  {"title": f"KPI Gasífero: {label}"}]
        ))
    fig_gas_kpi.update_layout(
        updatemenus=[dict(
            active=0,
            buttons=buttons_gas,
            direction='down',
            showactive=True,
            x=1.1, y=1.15
        )],
        title="KPI Gasífero: Gas 6m / Lateral (m³/m)",
        xaxis_title="Año de inicio",
        yaxis_title="Valor KPI (m³)",
        legend_title="KPI",
        height=400
    )
    # --- KPI PETRÓLEO ---
    pet_labels = {
        'oil6m_x_lateral': 'Oil 6m / Lateral (Mbbl/m)',
        'oil6m_x_arena': 'Oil 6m / Arena (Mbbl/tn)',
        'oil6m_x_frac': 'Oil 6m / Frac (Mbbl/frac)'
    }
    fig_pet_kpi = go.Figure()
    for col, label in pet_labels.items():
        fig_pet_kpi.add_trace(go.Bar(
            x=df_oil['anio_inicio'],
            y=df_oil[col],
            name=label,
            visible=(col == 'oil6m_x_lateral')
        ))
    buttons_pet = []
    for i, (col, label) in enumerate(pet_labels.items()):
        vis = [False] * len(pet_labels)
        vis[i] = True
        buttons_pet.append(dict(
            label=label,
            method="update",
            args=[{"visible": vis},
                  {"title": f"KPI Petrolero: {label}"}]
        ))
    fig_pet_kpi.update_layout(
        updatemenus=[dict(
            active=0,
            buttons=buttons_pet,
            direction='down',
            showactive=True,
            x=1.1, y=1.15
        )],
        title="KPI Petrolero: Oil 6m / Lateral (Mbbl/m)",
        xaxis_title="Año de inicio",
        yaxis_title="Valor KPI (Mbbl)",
        legend_title="KPI",
        height=400
    )
    with col1:
        st.plotly_chart(fig_pet_kpi, use_container_width=True)
    with col2:
        st.plotly_chart(fig_gas_kpi, use_container_width=True)

# --- TOP 10 MEJORES POZOS DE PETRÓLEO Y GAS POR ACUMULADO EN 6 MESES (1 POZO ÚNICO) ---

st.markdown("## Top 10 mejores pozos en 6 meses (Oil & Gas)")

col1, col2 = st.columns(2)

# --- PETRÓLEO ---
top_oil = (
    df[df['oil_acum_6m_mbbl'].notnull()]
    .groupby('sigla', as_index=False)
    .agg({
        'oil_acum_6m_mbbl': 'max',
        'areayacimiento': 'first',
        'empresa_filtrada': 'first'
    })
    .sort_values('oil_acum_6m_mbbl', ascending=False)
    .head(10)
    .copy()
)
top_oil = top_oil[::-1]

with col1:
    st.subheader("Top 10 Pozos Petrolíferos (acum. 6 meses)")
    fig_top_oil = go.Figure(go.Bar(
        x=top_oil['oil_acum_6m_mbbl'],
        y=top_oil['sigla'],
        orientation='h',
        marker=dict(color='indianred'),
        text=[f"{yac} | {cia}" for yac, cia in zip(top_oil['areayacimiento'], top_oil['empresa_filtrada'])],
        hovertemplate='Pozo: %{y}<br>Acum. 6m: %{x:.2f} Mbbl<br>%{text}<extra></extra>'
    ))
    fig_top_oil.update_layout(
        xaxis_title="Acumulado 6 meses (Mbbl)",
        yaxis_title="Pozo (sigla)",
        title="Top 10 Pozos de Petróleo (acumulado 6 meses)",
        height=400
    )
    st.plotly_chart(fig_top_oil, use_container_width=True)

# --- GAS ---
top_gas = (
    df[df['gas_acum_6m_bcf'].notnull()]
    .groupby('sigla', as_index=False)
    .agg({
        'gas_acum_6m_bcf': 'max',
        'areayacimiento': 'first',
        'empresa_filtrada': 'first'
    })
    .sort_values('gas_acum_6m_bcf', ascending=False)
    .head(10)
    .copy()
)
top_gas = top_gas[::-1]

with col2:
    st.subheader("Top 10 Pozos Gasíferos (acum. 6 meses)")
    fig_top_gas = go.Figure(go.Bar(
        x=top_gas['gas_acum_6m_bcf'],
        y=top_gas['sigla'],
        orientation='h',
        marker=dict(color='steelblue'),
        text=[f"{yac} | {cia}" for yac, cia in zip(top_gas['areayacimiento'], top_gas['empresa_filtrada'])],
        hovertemplate='Pozo: %{y}<br>Acum. 6m: %{x:.2f} Bcf<br>%{text}<extra></extra>'
    ))
    fig_top_gas.update_layout(
        xaxis_title="Acumulado 6 meses (Bcf)",
        yaxis_title="Pozo (sigla)",
        title="Top 10 Pozos de Gas (acumulado 6 meses)",
        height=400
    )
    st.plotly_chart(fig_top_gas, use_container_width=True)

# --- SCATTER DE ARENA POR FRACTURA POR AÑO ---


# Aseguramos que no haya división por cero
df_oil_scatter = df_oil.copy()
df_gas_scatter = df_gas.copy()
df_oil_scatter['arena_por_frac'] = np.where(df_oil_scatter['cantidad_fracturas'] > 0,
                                            df_oil_scatter['arena_bombeada'] / df_oil_scatter['cantidad_fracturas'],
                                            np.nan)
df_gas_scatter['arena_por_frac'] = np.where(df_gas_scatter['cantidad_fracturas'] > 0,
                                            df_gas_scatter['arena_bombeada'] / df_gas_scatter['cantidad_fracturas'],
                                            np.nan)

st.markdown("---")
st.markdown("### Arena bombeada por fractura por año de inicio")

col1, col2 = st.columns(2)

with col1:
    fig_scatter_oil = go.Figure()
    fig_scatter_oil.add_trace(go.Scatter(
        x=df_oil_scatter['anio_inicio'],
        y=df_oil_scatter['arena_por_frac'],
        mode='markers',
        marker=dict(size=7, color=df_oil_scatter['empresa_filtrada'].astype('category').cat.codes,
                    colorbar=dict()),
        text=df_oil_scatter['sigla'],
        hovertemplate="Pozo: %{text}<br>Año: %{x}<br>Arena/Frac: %{y:.1f} tn"
    ))
    fig_scatter_oil.update_layout(
        title="Petrolíferos: Arena bombeada por fractura",
        xaxis_title="Año de inicio",
        yaxis_title="Arena por fractura (toneladas)",
        height=400
    )
    st.plotly_chart(fig_scatter_oil, use_container_width=True)

with col2:
    fig_scatter_gas = go.Figure()
    fig_scatter_gas.add_trace(go.Scatter(
        x=df_gas_scatter['anio_inicio'],
        y=df_gas_scatter['arena_por_frac'],
        mode='markers',
        marker=dict(size=7, color=df_gas_scatter['empresa_filtrada'].astype('category').cat.codes,
                    colorbar=dict()),
        text=df_gas_scatter['sigla'],
        hovertemplate="Pozo: %{text}<br>Año: %{x}<br>Arena/Frac: %{y:.1f} tn"
    ))
    fig_scatter_gas.update_layout(
        title="Gasíferos: Arena bombeada por fractura",
        xaxis_title="Año de inicio",
        yaxis_title="Arena por fractura (toneladas)",
        height=400
    )
    st.plotly_chart(fig_scatter_gas, use_container_width=True)

