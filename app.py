import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="Dashboard de Telecomunicaciones",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título del Dashboard
st.title("📊 Dashboard de Suscriptores y Servicios")
st.markdown("Análisis y visualización interactiva de la planta de servicios por región y estado.")

# Diccionario de coordenadas aproximadas para los estados de Venezuela para el mapa
COORDENADAS_ESTADOS = {
    'Distrito Capital': {'lat': 10.5000, 'lon': -66.9167},
    'La Guaira': {'lat': 10.6000, 'lon': -66.9333},
    'Miranda': {'lat': 10.2500, 'lon': -66.5000},
    'Aragua': {'lat': 10.2333, 'lon': -67.5833},
    'Carabobo': {'lat': 10.1667, 'lon': -68.0000},
    'Yaracuy': {'lat': 10.2500, 'lon': -68.7500},
    'Amazonas': {'lat': 5.0000, 'lon': -66.0000},
    'Bolívar': {'lat': 6.0000, 'lon': -63.0000},
    'Delta Amacuro': {'lat': 8.5000, 'lon': -61.5000},
    'Mérida': {'lat': 8.5833, 'lon': -71.1333},
    'Táchira': {'lat': 7.7667, 'lon': -72.2167},
    'Trujillo': {'lat': 9.3667, 'lon': -70.4333},
    'Apure': {'lat': 7.0000, 'lon': -68.5000},
    'Barinas': {'lat': 8.2500, 'lon': -69.5000},
    'Cojedes': {'lat': 9.5000, 'lon': -68.3000},
    'Guárico': {'lat': 9.0000, 'lon': -66.0000},
    'Portuguesa': {'lat': 9.1667, 'lon': -69.2500},
    'Falcón': {'lat': 11.1667, 'lon': -69.6667},
    'Lara': {'lat': 10.1667, 'lon': -69.5000},
    'Zulia': {'lat': 10.0000, 'lon': -72.0000},
    'Anzoátegui': {'lat': 9.0000, 'lon': -64.5000},
    'Monagas': {'lat': 9.5000, 'lon': -63.0000},
    'Nueva Esparta': {'lat': 11.0000, 'lon': -63.9000},
    'Sucre': {'lat': 10.5000, 'lon': -63.2500}
}

# Función para cargar y limpiar los datos
@st.cache_data
def cargar_datos():
    # Se lee el archivo asumiendo punto y coma como delimitador según la estructura
    df = pd.read_csv('Libro1.csv', sep=';')
    df = df.dropna(subset=['Estado', 'Región'])
    
    # Agregar latitudes y longitudes al DataFrame
    df['lat'] = df['Estado'].map(lambda x: COORDENADAS_ESTADOS.get(x, {}).get('lat', None))
    df['lon'] = df['Estado'].map(lambda x: COORDENADAS_ESTADOS.get(x, {}).get('lon', None))
    return df

try:
    df_raw = cargar_datos()
    
    # Identificar las columnas de productos dinámicamente
    columnas_base = ['Región', 'Estado', 'lat', 'lon']
    lista_productos = [col for col in df_raw.columns if col not in columnas_base]

    # --- BARRA LATERAL (FILTROS) ---
    st.sidebar.header("⚙️ Filtros de Selección")
    
    # Filtro por Región
    regiones_disponibles = sorted(df_raw['Región'].unique())
    regiones_seleccionadas = st.sidebar.multiselect("Selecciona Región(es):", regiones_disponibles, default=regiones_disponibles)
    
    # Filtrar estados disponibles según las regiones seleccionadas
    df_filtrado_preliminar = df_raw[df_raw['Región'].isin(regiones_seleccionadas)]
    estados_disponibles = sorted(df_filtrado_preliminar['Estado'].unique())
    
    # Filtro por Estado
    estados_seleccionados = st.sidebar.multiselect("Selecciona Estado(s):", estados_disponibles, default=estados_disponibles)
    
    # Filtro por Producto
    productos_seleccionados = st.sidebar.multiselect("Selecciona Producto(s) a Visualizar:", lista_productos, default=lista_productos)

    # Aplicar Filtros Finales al DataFrame
    df_filtrado = df_raw[
        (df_raw['Región'].isin(regiones_seleccionadas)) & 
        (df_raw['Estado'].isin(estados_seleccionados))
    ]

    # Calcular columna de Total según los productos seleccionados
    if productos_seleccionados:
        df_filtrado['Total Seleccionado'] = df_filtrado[productos_seleccionados].sum(axis=1)
    else:
        df_filtrado['Total Seleccionado'] = 0

    # --- SECCIÓN DE KPIS ---
    st.subheader("📌 Indicadores Clave (KPIs)")
    kpi1, kpi2, kpi3 = st.columns(3)
    
    total_suscriptores = df_filtrado['Total Seleccionado'].sum()
    total_estados = df_filtrado['Estado'].nunique()
    total_regiones = df_filtrado['Región'].nunique()
    
    kpi1.metric(label="Total Líneas/Servicios (Filtro)", value=f"{total_suscriptores:,}")
    kpi2.metric(label="Estados Seleccionados", value=total_estados)
    kpi3.metric(label="Regiones Activas", value=total_regiones)
    
    st.markdown("---")

    # --- SECCIÓN DE GRÁFICOS Y MAPAS ---
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.subheader("📈 Volumen de Servicios por Estado")
        if productos_seleccionados and not df_filtrado.empty:
            # Reestructurar datos para graficar correctamente con Plotly express
            df_melted = df_filtrado.melt(id_vars=['Estado'], value_vars=productos_seleccionados, var_name='Producto', value_name='Cantidad')
            fig_bar = px.bar(df_melted, x='Estado', y='Cantidad', color='Producto', title="Distribución por Producto y Estado", barmode='stack')
            fig_bar.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("Selecciona al menos un producto para visualizar el gráfico.")

    with col_der:
        st.subheader("🗺️ Mapa de Distribución Geográfica")
        # Filtrar filas que tengan coordenadas válidas y datos mayores a 0
        df_mapa = df_filtrado[df_filtrado['lat'].notna() & (df_filtrado['Total Seleccionado'] > 0)]
        
        if not df_mapa.empty:
            # Crear un mapa de burbujas interactivo con Plotly para mejor control visual
            fig_map = px.scatter_mapbox(
                df_mapa, 
                lat="lat", 
                lon="lon", 
                size="Total Seleccionado", 
                color="Región",
                hover_name="Estado", 
                hover_data=productos_seleccionados,
                zoom=5, 
                height=400,
                title="Concentración de Servicios por Estado"
            )
            fig_map.update_layout(mapbox_style="open-street-map")
            fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.info("No hay datos geográficos disponibles para la selección actual.")

    st.markdown("---")

    # --- TABLA DE DATOS Y DESCARGA ---
    st.subheader("📋 Datos Detallados de la Selección")
    
    # Columnas a mostrar en la tabla interactiva
    columnas_mostrar = ['Región', 'Estado'] + productos_seleccionados + ['Total Seleccionado']
    st.dataframe(df_filtrado[columnas_mostrar].reset_index(drop=True), use_container_width=True)

    # Botón de descarga de archivo CSV adaptado a los filtros
    st.subheader("📥 Exportar Resultados")
    
    # Convertir el dataframe filtrado a CSV string listo para descargar
    csv_data = df_filtrado[columnas_mostrar].to_csv(index=False, sep=';').encode('utf-8')
    
    st.download_button(
        label="Descargar Selección Actual como CSV",
        data=csv_data,
        file_name="seleccion_servicios_filtrado.csv",
        mime="text/csv",
        key='download-csv'
    )

except FileNotFoundError:
    st.error("❌ No se encontró el archivo 'Libro1.csv'. Por favor, asegúrate de colocar el archivo en el mismo directorio que este script.")
except Exception as e:
    st.error(f"❌ Ocurrió un error inesperado: {e}")