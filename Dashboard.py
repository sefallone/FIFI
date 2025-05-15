import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime
import base64
from io import BytesIO
from typing import Optional, Dict, Tuple, List
import logging

# Configuración inicial
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================
# CONFIGURACIÓN DE LA PÁGINA Y ESTILOS
# =============================================

def configure_page():
    """Configura la página de Streamlit con parámetros iniciales."""
    st.set_page_config(
        page_title="Dashboard Fallone Investments Pro",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://falloneinvestments.com/help',
            'Report a bug': "https://falloneinvestments.com/bug",
            'About': "### Dashboard de Análisis de Inversiones v2.0"
        }
    )
    load_custom_css()

def load_custom_css():
    """Carga estilos CSS personalizados."""
    st.markdown("""
    <style>
        :root {
            --primary-color: #3f33ff;
            --secondary-color: #1024ca;
            --success-color: #00cc96;
            --danger-color: #ff4b4b;
            --dark-bg: #121212;
            --sidebar-bg: #1e1e1e;
        }
        
        .stApp {
            background-color: var(--dark-bg);
            color: #ffffff;
        }
        
        .stSidebar {
            background-color: var(--sidebar-bg) !important;
        }
        
        .metric-card {
            background: var(--secondary-color);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            border-left: 4px solid var(--primary-color);
        }
        
        .metric-title {
            font-weight: 600;
            font-size: 14px;
            color: #ffffff;
        }
        
        .metric-value {
            font-weight: 700;
            font-size: 24px;
            margin: 10px 0;
        }
        
        .positive-delta {
            color: var(--success-color);
        }
        
        .negative-delta {
            color: var(--danger-color);
        }
    </style>
    """, unsafe_allow_html=True)

# =============================================
# MANEJO DE DATOS
# =============================================

@st.cache_data(ttl=3600, show_spinner="Cargando datos...")
def load_and_preprocess_data(uploaded_file: BytesIO, selected_sheet: str) -> Optional[pd.DataFrame]:
    """Carga y preprocesa los datos del archivo Excel."""
    try:
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        df = df.loc[:, ~df.columns.duplicated()]
        
        # Normalización de nombres de columnas
        column_mapping = {
            'Ganacias/Pérdidas Brutas': 'Ganancias/Pérdidas Brutas',
            'Ganacias/Pérdidas Netas': 'Ganancias/Pérdidas Netas',
            'Beneficio en %': 'Beneficio %',
            'Comisiones 10 %': 'Comisiones Pagadas'
        }
        
        df = df.rename(columns={col: column_mapping[col] for col in column_mapping 
                              if col in df.columns and column_mapping[col] not in df.columns})
        
        # Conversión y limpieza de fechas
        if 'Fecha' in df.columns:
            df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            df = df.dropna(subset=['Fecha'])
            df['MesAño'] = df['Fecha'].dt.to_period('M')
        
        # Conversión de columnas numéricas
        numeric_cols = ['Capital Invertido', 'Ganancias/Pérdidas Brutas', 
                       'Ganancias/Pérdidas Netas', 'Comisiones Pagadas']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    except Exception as e:
        logger.error(f"Error al cargar datos: {str(e)}")
        st.error(f"Error al procesar el archivo: {str(e)}")
        return None

# =============================================
# COMPONENTES DE INTERFAZ
# =============================================

def display_metric_card(title: str, value, icon: str = "💰", 
                       is_currency: bool = True, is_percentage: bool = False, 
                       delta: Optional[str] = None):
    """
    Muestra una tarjeta de métrica con estilo mejorado.
    
    Args:
        title: Título de la métrica
        value: Valor a mostrar
        icon: Icono para la métrica
        is_currency: Si el valor es monetario
        is_percentage: Si el valor es porcentual
        delta: Variación respecto a período anterior (opcional)
    """
    if pd.isna(value) or value is None:
        value_display = "N/D"
        delta_display = None
    else:
        if is_currency:
            value_display = f"${float(value):,.2f}"
        elif is_percentage:
            value_display = f"{float(value):.2f}%"
        else:
            value_display = f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
    
    delta_class = ""
    if delta:
        delta_class = "positive-delta" if str(delta).startswith('+') else "negative-delta"
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">{icon} {title}</div>
        <div class="metric-value">{value_display}</div>
        <div class="{delta_class}">
            {delta if delta else ''}
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_date_range_filter(df: pd.DataFrame) -> Tuple[datetime, datetime]:
    """Crea un filtro de rango de fechas en el sidebar."""
    min_date = df['Fecha'].min().to_pydatetime()
    max_date = df['Fecha'].max().to_pydatetime()
    
    st.sidebar.write("**Seleccione el rango de meses:**")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Mes inicial",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key="start_date"
        )
        start_date = datetime(start_date.year, start_date.month, 1)
    
    with col2:
        end_date = st.date_input(
            "Mes final",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="end_date"
        )
        end_date = datetime(end_date.year, end_date.month, 1)
    
    return start_date, end_date

# =============================================
# ANÁLISIS FINANCIERO
# =============================================

def calculate_financial_metrics(df: pd.DataFrame, capital_inicial: float) -> Dict:
    """Calcula métricas financieras clave."""
    metrics = {}
    
    try:
        # Métricas básicas
        metrics['current_capital'] = df['Capital Invertido'].iloc[-1] if len(df) > 0 else 0
        metrics['delta_capital'] = metrics['current_capital'] - capital_inicial if len(df) > 0 else 0
        metrics['total_injections'] = df['Aumento Capital'].sum()
        metrics['gross_profit'] = df['Ganancias/Pérdidas Brutas'].sum() if 'Ganancias/Pérdidas Brutas' in df.columns else 0
        metrics['net_profit'] = df['Ganancias/Pérdidas Netas'].sum() if 'Ganancias/Pérdidas Netas' in df.columns else 0
        metrics['fees'] = df['Comisiones Pagadas'].sum() if 'Comisiones Pagadas' in df.columns else 0
        metrics['withdrawals'] = df['Retiro de Fondos'].sum() if 'Retiro de Fondos' in df.columns else 0
        
        # Métricas avanzadas
        metrics['roi'] = calculate_roi(df, capital_inicial)
        metrics['cagr'] = calculate_cagr(df, capital_inicial, metrics['current_capital'])
        metrics['sharpe_ratio'] = calculate_sharpe_ratio(df)
        metrics['max_drawdown'] = calculate_max_drawdown(df)
        
    except Exception as e:
        logger.error(f"Error calculando métricas: {str(e)}")
    
    return metrics

def calculate_roi(df: pd.DataFrame, capital_inicial: float) -> float:
    """Calcula el Retorno sobre la Inversión (ROI)."""
    if 'Ganancias/Pérdidas Netas' in df.columns and capital_inicial and float(capital_inicial) != 0:
        ganancias_netas = df['Ganancias/Pérdidas Netas'].sum()
        return (float(ganancias_netas) / float(capital_inicial)) * 100
    return 0

def calculate_cagr(df: pd.DataFrame, capital_inicial: float, current_capital: float) -> float:
    """Calcula la Tasa de Crecimiento Anual Compuesto (CAGR)."""
    if len(df) > 1 and capital_inicial and float(capital_inicial) != 0:
        start_date = df['Fecha'].iloc[0]
        end_date = df['Fecha'].iloc[-1]
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if months <= 0:
            months = 1
        return ((float(current_capital) / float(capital_inicial)) ** (12/months) - 1) * 100
    return 0

# =============================================
# VISUALIZACIONES
# =============================================

def plot_combined_metrics(df: pd.DataFrame, capital_inicial: float):
    """Gráfico combinado de capital y ganancias."""
    if not all(col in df.columns for col in ['Fecha', 'Capital Invertido', 'Ganancias/Pérdidas Brutas']):
        return
    
    fig = px.line(
        df,
        x='Fecha',
        y=['Capital Invertido', 'Ganancias/Pérdidas Brutas'],
        title='Evolución Combinada de Capital y Ganancias',
        labels={'value': 'Monto ($)', 'variable': 'Métrica'},
        template="plotly_dark",
        color_discrete_sequence=['#3f33ff', '#00cc96']
    )
    
    fig.add_hline(
        y=capital_inicial, 
        line_dash="dash", 
        line_color="green",
        annotation_text=f"Capital Inicial: ${capital_inicial:,.2f}"
    )
    
    fig.update_layout(
        height=500,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def plot_profit_analysis(df: pd.DataFrame):
    """Análisis visual de ganancias/pérdidas."""
    if 'Ganancias/Pérdidas Brutas' not in df.columns:
        return
    
    tab1, tab2 = st.tabs(["Distribución", "Acumulado"])
    
    with tab1:
        fig1 = px.histogram(
            df,
            x='Ganancias/Pérdidas Brutas',
            nbins=20,
            title='Distribución de Ganancias/Pérdidas',
            template="plotly_dark"
        )
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, use_container_width=True)
    
    with tab2:
        df['Ganancias Acumuladas'] = df['Ganancias/Pérdidas Brutas'].cumsum()
        fig2 = px.area(
            df,
            x='Fecha',
            y='Ganancias Acumuladas',
            title='Ganancias Acumuladas en el Tiempo',
            template="plotly_dark"
        )
        fig2.update_layout(height=400)
        st.plotly_chart(fig2, use_container_width=True)

# =============================================
# FUNCIÓN PRINCIPAL
# =============================================

def main():
    # Configuración inicial
    configure_page()
    st.title("📊 Dashboard de Inversiones - Fallone Investments Pro")
    
    # Carga de datos
    uploaded_file = st.sidebar.file_uploader(
        "📤 Subir archivo Excel", 
        type=['xlsx', 'xls'],
        help="Suba el archivo de reporte mensual en formato Excel"
    )
    
    if uploaded_file is not None:
        try:
            # Selección de hoja
            sheet_names = pd.ExcelFile(uploaded_file).sheet_names
            selected_sheet = st.sidebar.selectbox(
                "📋 Seleccionar hoja de trabajo", 
                sheet_names,
                key="sheet_selector"
            )
            
            # Carga y preprocesamiento
            df = load_and_preprocess_data(uploaded_file, selected_sheet)
            if df is None:
                return
                
            # Filtros
            st.sidebar.subheader("🔍 Filtros Avanzados")
            start_date, end_date = create_date_range_filter(df)
            
            # Aplicar filtros
            filtered_df = df[
                (df['Fecha'] >= pd.to_datetime(start_date)) & 
                (df['Fecha'] <= pd.to_datetime(end_date))
            ].copy()
            
            # Mostrar resumen
            st.success(f"✅ Datos cargados correctamente ({len(filtered_df)} registros)")
            
            # Información del inversionista
            capital_inicial = filtered_df['Aumento Capital'].iloc[1] if len(filtered_df) > 1 else 0
            investor_id = filtered_df['ID Inv'].iloc[1] if len(filtered_df) > 1 else "N/D"
            
            # Métricas financieras
            metrics = calculate_financial_metrics(filtered_df, capital_inicial)
            
            # Visualización de KPIs
            st.subheader("📊 Métricas Clave de Rendimiento")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                display_metric_card("ID Inversionista", investor_id, "🆔", False)
            with col2:
                display_metric_card("Capital Actual", metrics['current_capital'], "🏦", delta=f"{metrics['delta_capital']:+,.2f}")
            with col3:
                display_metric_card("ROI", metrics['roi'], "📊", False, True)
            with col4:
                display_metric_card("CAGR Mensual", metrics['cagr'], "🚀", False, True)
            
            # Visualizaciones
            st.subheader("📈 Análisis Visual")
            plot_combined_metrics(filtered_df, capital_inicial)
            plot_profit_analysis(filtered_df)
            
            # Datos detallados
            st.subheader("📝 Datos Detallados")
            st.dataframe(
                filtered_df.style.format({
                    'Capital Invertido': '${:,.2f}',
                    'Ganancias/Pérdidas Brutas': '${:,.2f}',
                    'Ganancias/Pérdidas Netas': '${:,.2f}',
                    'Comisiones Pagadas': '${:,.2f}'
                }),
                use_container_width=True
            )
            
        except Exception as e:
            logger.error(f"Error en el flujo principal: {str(e)}")
            st.error(f"Ocurrió un error: {str(e)}")
    else:
        st.info("👋 Por favor, suba un archivo Excel para comenzar el análisis")

if __name__ == "__main__":
    main()
