import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import base64
from io import BytesIO
import time

# Configuración inicial de la página
st.set_page_config(
    page_title="Dashboard Financiero Premium",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# FUNCIONALIDADES ADICIONALES SOLICITADAS
# =============================================

# 1. Selector de temas (claro/oscuro)
def apply_theme(theme):
    if theme == "Oscuro":
        st.markdown("""
        <style>
            :root {
                --primary: #5ED6DC;
                --secondary: #67e4da;
                --bg: #1E1E1E;
                --text: #FFFFFF;
                --card-bg: #2D2D2D;
                --border: #3E3E3E;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
            :root {
                --primary: #5ED6DC;
                --secondary: #67e4da;
                --bg: #FFFFFF;
                --text: #2c3e50;
                --card-bg: #F8F9FA;
                --border: #E0E0E0;
            }
        </style>
        """, unsafe_allow_html=True)

# 2. Animaciones de carga
def loading_animation():
    with st.spinner('Cargando datos...'):
        time.sleep(1)
        st.success('¡Datos cargados con éxito!')

# 3. Generador de reportes en PDF/Excel
def generate_excel_report(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Datos Financieros')
    return output.getvalue()

def create_download_link(data, filename):
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Descargar {filename}</a>'

# 4. Panel de filtros avanzados
def advanced_filters(df):
    with st.sidebar.expander("🔍 Filtros Avanzados", expanded=False):
        # Filtro por rango de fechas
        if 'Fecha' in df.columns:
            min_date = pd.to_datetime(df['Fecha']).min()
            max_date = pd.to_datetime(df['Fecha']).max()
            date_range = st.date_input(
                "Rango de fechas",
                [min_date, max_date],
                min_value=min_date,
                max_value=max_date
            )
            df = df[(pd.to_datetime(df['Fecha']) >= pd.to_datetime(date_range[0])) & 
                   (pd.to_datetime(df['Fecha']) <= pd.to_datetime(date_range[1]))]
        
        # Filtro por capital invertido
        if 'Capital Invertido' in df.columns:
            min_cap, max_cap = st.slider(
                "Rango de Capital Invertido",
                float(df['Capital Invertido'].min()),
                float(df['Capital Invertido'].max()),
                (float(df['Capital Invertido'].min()), float(df['Capital Invertido'].max()))
            df = df[(df['Capital Invertido'] >= min_cap) & (df['Capital Invertido'] <= max_cap)]
        
        # Filtro por ganancias
        if 'Ganancias/Pérdidas Brutas' in df.columns:
            profit_filter = st.selectbox(
                "Filtrar por ganancias",
                ["Todos", "Solo positivas", "Solo negativas"]
            )
            if profit_filter == "Solo positivas":
                df = df[df['Ganancias/Pérdidas Brutas'] >= 0]
            elif profit_filter == "Solo negativas":
                df = df[df['Ganancias/Pérdidas Brutas'] < 0]
    
    return df

# =============================================
# INTERFAZ PRINCIPAL
# =============================================

# Sidebar con controles
with st.sidebar:
    st.title("⚙️ Configuración")
    
    # Selector de tema
    theme = st.radio("Seleccionar tema", ["Claro", "Oscuro"], index=0)
    apply_theme(theme)
    
    # Selector de animaciones
    animations = st.checkbox("Activar animaciones", value=True)

# Título principal con animación
if animations:
    with st.empty():
        for i in range(3):
            st.title(f"📊 Dashboard Financiero Premium{'...'[:i]}")
            time.sleep(0.3)
        st.title("📊 Dashboard Financiero Premium")
else:
    st.title("📊 Dashboard Financiero Premium")

# Cargar archivo Excel
uploaded_file = st.file_uploader("📤 Subir archivo Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    if animations:
        loading_animation()
    
    try:
        # Leer archivo Excel
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("📋 Seleccionar hoja de trabajo", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

        # Limpiar nombres de columnas duplicadas
        df = df.loc[:, ~df.columns.duplicated()]

        # Renombrar columnas
        column_mapping = {
            'Ganacias/Pérdidas Brutas': 'Ganancias/Pérdidas Brutas',
            'Ganacias/Pérdidas Netas': 'Ganancias/Pérdidas Netas',
            'Beneficio en %': 'Beneficio %',
            'Comisiones 10 %': 'Comisiones Pagadas'
        }
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

        # Aplicar filtros avanzados
        df = advanced_filters(df)

        # Verificar columnas críticas
        required_columns = ['Fecha', 'Capital Invertido', 'Aumento Capital']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            st.error(f"🚨 Error: Faltan columnas críticas: {', '.join(missing_cols)}")
            st.stop()

        # =============================================
        # SECCIÓN DE KPIs (Manteniendo el estilo anterior)
        # =============================================
        
        # ... (El código de KPIs y visualizaciones anterior se mantendría aquí)
        # Se mantendrían todas las funciones display_kpi y gráficos anteriores
        
        # =============================================
        # SECCIÓN DE REPORTES
        # =============================================
        
        st.markdown("---")
        st.markdown('<h2 class="header-style">📤 Generar Reportes</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Exportar Datos")
            if st.button("Generar Reporte Excel"):
                excel_data = generate_excel_report(df)
                st.markdown(create_download_link(excel_data, "reporte_financiero.xlsx"), unsafe_allow_html=True)
        
        with col2:
            st.subheader("Personalizar Reporte")
            report_name = st.text_input("Nombre del reporte", "Reporte_Financiero")
            selected_cols = st.multiselect(
                "Seleccionar columnas para exportar",
                df.columns.tolist(),
                default=df.columns.tolist()[:5]
            )
            
            if st.button("Generar Reporte Personalizado"):
                excel_data = generate_excel_report(df[selected_cols])
                st.markdown(create_download_link(excel_data, f"{report_name}.xlsx"), unsafe_allow_html=True)

        # =============================================
        # VISUALIZACIÓN DE DATOS (se mantendría igual)
        # =============================================

    except Exception as e:
        st.error(f"🚨 Error crítico al procesar el archivo: {str(e)}")
        st.error("Por favor verifica que el archivo tenga el formato correcto.")
else:
    st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")

# =============================================
# ESTILOS CSS PERSONALIZADOS (mejorados)
# =============================================

st.markdown(f"""
<style>
    /* Estilos base que cambian con el tema */
    body {{
        background-color: var(--bg);
        color: var(--text);
    }}
    
    /* Tarjetas de métricas */
    div[data-testid="metric-container"] {{
        background-color: var(--card-bg);
        border: 1px solid var(--border);
        border-left: 5px solid var(--primary);
        border-radius: 12px;
        padding: 20px 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 25px;
        transition: all 0.3s ease;
    }}
    
    div[data-testid="metric-container"]:hover {{
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.12);
    }}
    
    div[data-testid="metric-container"] > label {{
        color: var(--text) !important;
        font-weight: 600 !important;
        font-size: 16px !important;
    }}
    
    div[data-testid="metric-container"] > div {{
        color: var(--text) !important;
        font-weight: 700 !important;
        font-size: 26px !important;
    }}
    
    /* Botones y controles */
    .stButton>button {{
        background-color: var(--primary);
        color: white;
        border-radius: 8px;
        padding: 8px 16px;
        border: none;
        transition: all 0.3s;
    }}
    
    .stButton>button:hover {{
        background-color: var(--secondary);
        transform: scale(1.02);
    }}
    
    /* Pestañas */
    .stTabs [role="tablist"] {{
        background-color: var(--card-bg);
        border-radius: 8px;
    }}
    
    /* Animaciones */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .animate-fade {{
        animation: fadeIn 0.5s ease-out;
    }}
</style>
""", unsafe_allow_html=True)

# Aplicar clase de animación si está activado
if animations and uploaded_file is not None:
    st.markdown("""
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const elements = document.querySelectorAll('.stMetric, .stPlotlyChart, .stDataFrame');
            elements.forEach((el, i) => {
                el.classList.add('animate-fade');
                el.style.animationDelay = `${i * 0.1}s`;
            });
        });
    </script>
    """, unsafe_allow_html=True)




