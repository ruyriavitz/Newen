import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(layout="wide")

@st.cache_data

def cargar_datos():
    produccion = pd.read_csv('http://datos.energia.gob.ar/dataset/c846e79c-026c-4040-897f-1ad3543b407c/resource/b5b58cdc-9e07-41f9-b392-fb9ec68b0725/download/produccin-de-pozos-de-gas-y-petrleo-no-convencional.csv',
                    usecols=['idpozo', 'sigla', 'anio', 'mes', 'prod_pet', 'prod_gas', 'tef', 'formprod', 'empresa', 'areayacimiento'])
    fracturas = pd.read_csv(
        'C:/Users/ruyri/Newen/Material de trabajo/Vaca Muerta/Datos Fracturas.csv',
        usecols=['idpozo', 'sigla', 'longitud_rama_horizontal_m', 'arena_bombeada_nacional_tn', 'cantidad_fracturas']
    )
    return produccion, fracturas

produccion, fracturas = cargar_datos()
produccion = produccion[(produccion['formprod'] == 'VMUT') & (produccion['tef'] > 0) & (produccion['anio'] >= 2010)]
produccion['date'] = pd.to_datetime(produccion['anio'].astype(str) + '-' + produccion['mes'].astype(str) + '-01')
produccion['bbl_pet'] = (produccion['prod_pet'] / produccion['tef']) * 6.2898
produccion['gas_Mm3_d'] = produccion['prod_gas'] / produccion['tef']
produccion['boe_gas'] = produccion['prod_gas'] * 5.615
produccion['boe_mes'] = produccion['bbl_pet'] * produccion['tef'] + produccion['boe_gas']
produccion['boed'] = produccion['boe_mes'] / produccion['tef']

inicio = produccion.groupby('idpozo')['date'].min().reset_index().rename(columns={'date': 'fecha_inicio'})
produccion = produccion.merge(inicio, on='idpozo', how='left')
produccion['mes_relativo'] = ((produccion['date'].dt.year - produccion['fecha_inicio'].dt.year) * 12 +
                               (produccion['date'].dt.month - produccion['fecha_inicio'].dt.month))
produccion['anio_inicio'] = produccion['fecha_inicio'].dt.year
# NOTA: Se eliminará este filtro global para conservar los datos de 2018 en el gráfico total
# produccion = produccion[produccion['anio_inicio'] >= 2018]

boed_por_pozo = produccion.groupby('idpozo').agg({'prod_pet': 'sum', 'prod_gas': 'sum'}).reset_index()
boed_por_pozo['tipo_pozo'] = boed_por_pozo.apply(lambda x: 'Petrolero' if x['prod_pet'] * 6.2898 > x['prod_gas'] * 5.615 else 'Gasífero', axis=1)
produccion = produccion.merge(boed_por_pozo[['idpozo', 'tipo_pozo']], on='idpozo', how='left')

fracturas = fracturas.groupby('idpozo').agg({
    'longitud_rama_horizontal_m': 'max',
    'arena_bombeada_nacional_tn': 'sum',
    'cantidad_fracturas': 'sum'
}).reset_index().reset_index()
produccion = produccion.merge(fracturas, on='idpozo', how='left')

st.sidebar.title("Explorador de Pozos")

empresas_validas = ["Todas"] + sorted(produccion['empresa'].dropna().unique())
empresa_seleccionada = st.sidebar.selectbox("Seleccionar Empresa", options=empresas_validas, index=empresas_validas.index("Todas"))

df_empresa = produccion.copy() if empresa_seleccionada == "Todas" else produccion[produccion['empresa'] == empresa_seleccionada]

yacimientos_validos = sorted(df_empresa['areayacimiento'].dropna().unique())
yacimiento_seleccionado = st.sidebar.selectbox("Seleccionar Yacimiento", options=["Todos"] + yacimientos_validos)

if yacimiento_seleccionado != "Todos":
    df_empresa = df_empresa[df_empresa['areayacimiento'] == yacimiento_seleccionado]

siglas_validas = df_empresa['sigla'].dropna().unique()
pozos_seleccionados = st.sidebar.multiselect("Seleccionar Pozos por Sigla", options=sorted(siglas_validas), default=[], help="Escribí parte de la sigla para filtrar")

df_filtrado = df_empresa[df_empresa['sigla'].isin(pozos_seleccionados)] if pozos_seleccionados else df_empresa.copy()

st.header("⚡ Producción Total por Mes")
total_prod = df_empresa.groupby(['date']).agg({
    'bbl_pet': 'sum',
    'gas_Mm3_d': 'sum'
}).reset_index()

fig_total = px.line(total_prod, x='date')
fig_total.add_scatter(x=total_prod['date'], y=total_prod['bbl_pet'], name='petróleo (bbl/d)', yaxis='y1')
fig_total.add_scatter(x=total_prod['date'], y=total_prod['gas_Mm3_d'], name='gas (Mm³/d)', yaxis='y2')
fig_total.update_layout(
    title='Producción Total por Mes - Petróleo y Gas',
    xaxis_title='Fecha',
    yaxis=dict(title='Petróleo (bbl/d)', side='left'),
    yaxis2=dict(title='Gas (Mm³/d)', overlaying='y', side='right', showgrid=False),
    legend_title='Fluido',
    legend=dict(x=0.01, y=0.99, xanchor='left')
)
st.plotly_chart(fig_total, use_container_width=True)

if not df_filtrado.empty and not pozos_seleccionados == []:
    df_filtrado = df_filtrado.sort_values(['sigla', 'date'])
    df_filtrado['boe_acumulado'] = df_filtrado.groupby('sigla')['boe_mes'].cumsum()

    tab1, tab2, tab3, tab4 = st.tabs(["BOED Mensual", "BOE Acumulado", "BOED vs Tiempo", "BOE Acumulado vs Tiempo"])

    with tab1:
        fig = px.line(df_filtrado, x='date', y='boed', color='sigla', title='Producción BOED mensual por Pozo')
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig2 = px.line(df_filtrado, x='date', y='boe_acumulado', color='sigla', title='Producción BOE Acumulada por Pozo')
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        fig3 = px.line(df_filtrado, x='mes_relativo', y='boed', color='sigla', title='Producción BOED mensual desde inicio (Mes 0)')
        st.plotly_chart(fig3, use_container_width=True)

    with tab4:
        fig4 = px.line(df_filtrado, x='mes_relativo', y='boe_acumulado', color='sigla', title='Producción BOE Acumulada desde inicio (Mes 0)')
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("📋 Tabla de Producción por Mes desde Inicio")
    tabla = df_filtrado[['sigla', 'mes_relativo', 'boed', 'longitud_rama_horizontal_m']].copy()
    tabla['boed'] = tabla['boed'].round().astype('Int64')
    tabla_pivot = tabla.pivot_table(index=['sigla', 'longitud_rama_horizontal_m'], columns='mes_relativo', values='boed')
    tabla_pivot.columns = [f"Mes {int(c)}" for c in tabla_pivot.columns]
    tabla_pivot = tabla_pivot.reset_index()
    st.dataframe(tabla_pivot)
    st.download_button("📥 Descargar Tabla de Producción", data=tabla_pivot.to_csv(index=False).encode('utf-8'), file_name='tabla_produccion.csv', mime='text/csv')

# Filtrar datos para análisis de promedios sólo desde 2018
df_promedios = df_empresa[df_empresa['anio_inicio'] >= 2018].copy()

st.download_button(
    label="📥 Descargar Datos Filtrados",
    data=df_filtrado.to_csv(index=False).encode('utf-8'),
    file_name='datos_filtrados.csv',
    mime='text/csv'
)

# Gráficos de promedios y acumulados solo con pozos desde 2018
max_mes = st.sidebar.slider("Límite de Mes desde Inicio para Gráficos Promedio", min_value=6, max_value=60, value=24)

st.header("📈 Pozo Promedio por Año de Inicio")
pozos_yac = df_promedios[df_promedios['mes_relativo'] <= max_mes].copy()
pozos_por_campaña = pozos_yac.groupby(['anio_inicio', 'idpozo', 'mes_relativo']).agg({'boed': 'mean'}).reset_index()
promedios_por_año = pozos_por_campaña.groupby(['anio_inicio', 'mes_relativo'])['boed'].mean().reset_index()
fig5 = px.line(promedios_por_año, x='mes_relativo', y='boed', color='anio_inicio',
               title='Curvas Promedio de Producción por Campaña (mes relativo)',
               labels={'boed': 'BOED Promedio', 'mes_relativo': 'Mes desde Inicio'})
st.plotly_chart(fig5, use_container_width=True)

pozos_por_campaña_acum = pozos_yac.groupby(['anio_inicio', 'idpozo', 'mes_relativo']).agg({'boe_mes': 'sum'}).reset_index()
pozos_por_campaña_acum['boe_acumulado'] = pozos_por_campaña_acum.groupby(['anio_inicio', 'idpozo'])['boe_mes'].cumsum()
promedios_acumulados = pozos_por_campaña_acum.groupby(['anio_inicio', 'mes_relativo'])['boe_acumulado'].mean().reset_index()
fig6 = px.line(promedios_acumulados, x='mes_relativo', y='boe_acumulado', color='anio_inicio',
               title='Acumulado Promedio de Producción por Campaña (BOE)',
               labels={'boe_acumulado': 'BOE Acumulado Promedio', 'mes_relativo': 'Mes desde Inicio'})
st.plotly_chart(fig6, use_container_width=True)

st.header("📊 Productividad Inicial en Primeros 6 Meses")
modo_kpi = st.radio("Seleccionar KPI", options=["Por metro lateral", "Por tonelada de arena", "Por cantidad de fracturas"], horizontal=True)

pozo_6m = df_promedios[df_promedios['mes_relativo'] < 6].groupby('idpozo').agg({
    'boe_mes': 'sum',
    'longitud_rama_horizontal_m': 'max',
    'arena_bombeada_nacional_tn': 'sum',
    'cantidad_fracturas': 'sum',
    'anio_inicio': 'first',
    'tipo_pozo': 'first'
}).reset_index()

if modo_kpi == "Por metro lateral":
    pozo_6m['kpi'] = pozo_6m['boe_mes'] / pozo_6m['longitud_rama_horizontal_m']
    y_label = 'BOE 6m / m lateral'
elif modo_kpi == "Por tonelada de arena":
    pozo_6m['kpi'] = pozo_6m['boe_mes'] / pozo_6m['arena_bombeada_nacional_tn']
    y_label = 'BOE 6m / ton arena'
else:
    pozo_6m['kpi'] = pozo_6m['boe_mes'] / pozo_6m['cantidad_fracturas']
    y_label = 'BOE 6m / fractura'

fig7 = px.box(pozo_6m, x='anio_inicio', y='kpi', color='tipo_pozo',
              title=f'Distribución del KPI de Productividad Inicial ({modo_kpi})',
              labels={'anio_inicio': 'Año de Inicio', 'kpi': y_label})
st.plotly_chart(fig7, use_container_width=True)

st.caption("App actualizada: integración completa de datos, gráficos, tablas, filtros y descarga para exploración avanzada de la producción en Vaca Muerta. ✅")

# Evolución de arena por etapa
st.header("📉 Evolución de Arena Bombeada por Fractura")
pozos_etapas = df_promedios[df_promedios['cantidad_fracturas'] > 0].copy()
pozos_etapas['arena_por_fractura'] = pozos_etapas['arena_bombeada_nacional_tn'] / pozos_etapas['cantidad_fracturas']

kpi_evol = pozos_etapas.groupby('anio_inicio')['arena_por_fractura'].mean().reset_index()
fig8 = px.line(kpi_evol, x='anio_inicio', y='arena_por_fractura', markers=True,
               title='Arena Bombeada Promedio por Fractura por Año de Inicio',
               labels={'arena_por_fractura': 'tn arena / fractura', 'anio_inicio': 'Año de Inicio'})
st.plotly_chart(fig8, use_container_width=True)

fig9 = px.box(pozos_etapas, x='anio_inicio', y='arena_por_fractura',
              title='Distribución de Arena Bombeada por Fractura por Año de Inicio',
              labels={'arena_por_fractura': 'tn arena / fractura', 'anio_inicio': 'Año de Inicio'})
st.plotly_chart(fig9, use_container_width=True)

st.caption("App actualizada: integración completa de datos, gráficos, tablas, filtros y descarga para exploración avanzada de la producción en Vaca Muerta. ✅")
