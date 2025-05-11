import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# Configuración inicial de la página
st.set_page_config(
    page_title="Dashboard Financiero Premium",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# FUNCIÓN PARA ESTILO PERSONALIZADO DE KPIs
# =============================================

def aplicar_estilo_kpis():
    """Aplica el estilo personalizado a las tarjetas de métricas"""
    st.markdown("""
    <style>
        div[data-testid="metric-container"] {
            background-color: #5ED6DC;
            border-left: 5px solid #67e4da;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        div[data-testid="metric-container"] > label {
            color: #2c3e50 !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }
        div[data-testid="metric-container"] > div {
            color: #2c3e50 !important;
            font-weight: 700 !important;
            font-size: 24px !important;
        }
        div[data-testid="metric-container"] > div > span {
            color: #2c3e50 !important;
            font-weight: 500 !important;
            font-size: 14px !important;
        }
    </style>
    """, unsafe_allow_html=True)

# =============================================
# FUNCIÓN DE FILTROS AVANZADOS
# =============================================

def advanced_filters(df):
    with st.sidebar.expander("🔍 Filtros Avanzados", expanded=False):
        filtered_df = df.copy()
        
        if 'Fecha' in filtered_df.columns:
            try:
                filtered_df['Fecha'] = pd.to_datetime(filtered_df['Fecha'])
                min_date = filtered_df['Fecha'].min().date()
                max_date = filtered_df['Fecha'].max().date()
                
                selected_dates = st.date_input(
                    "Seleccione rango de fechas",
                    [min_date, max_date],
                    min_value=min_date,
                    max_value=max_date
                )
                
                if len(selected_dates) == 2:
                    start_date, end_date = selected_dates
                    filtered_df = filtered_df[
                        (filtered_df['Fecha'].dt.date >= start_date) & 
                        (filtered_df['Fecha'].dt.date <= end_date)
                    ]
            except Exception as e:
                st.warning(f"No se pudo aplicar el filtro de fechas: {str(e)}")
        
        if 'Capital Invertido' in filtered_df.columns:
            try:
                capital_series = pd.to_numeric(filtered_df['Capital Invertido'], errors='coerce').dropna()
                if not capital_series.empty:
                    min_cap = float(capital_series.min())
                    max_cap = float(capital_series.max())
                    
                    cap_range = st.slider(
                        "Seleccione rango de capital",
                        min_value=min_cap,
                        max_value=max_cap,
                        value=(min_cap, max_cap),
                        help="Filtre por rango de capital invertido"
                    )
                    
                    filtered_df = filtered_df[
                        (pd.to_numeric(filtered_df['Capital Invertido'], errors='coerce') >= cap_range[0]) & 
                        (pd.to_numeric(filtered_df['Capital Invertido'], errors='coerce') <= cap_range[1])
                    ]
            except Exception as e:
                st.warning(f"No se pudo aplicar el filtro de capital: {str(e)}")
    
    return filtered_df

# =============================================
# INTERFAZ PRINCIPAL
# =============================================

with st.sidebar:
    st.title("⚙️ Configuración")
    theme = st.radio("Seleccionar tema", ["Claro", "Oscuro"], index=0)
    animations = st.checkbox("Activar animaciones", value=True)

if animations:
    with st.empty():
        for i in range(3):
            st.title(f"📊 Dashboard Financiero Premium{'...'[:i]}")
            time.sleep(0.3)
        st.title("📊 Dashboard Financiero Premium")
else:
    st.title("📊 Dashboard Financiero Premium")

uploaded_file = st.file_uploader("📤 Subir archivo Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    if animations:
        with st.spinner('Cargando datos...'):
            time.sleep(1)
    
    try:
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("📋 Seleccionar hoja de trabajo", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

        # Limpieza y preparación de datos
        df = df.loc[:, ~df.columns.duplicated()]
        rename_dict = {
            'Ganacias/Pérdidas Brutas': 'Ganancias/Pérdidas Brutas',
            'Ganacias/Pérdidas Netas': 'Ganancias/Pérdidas Netas',
            'Beneficio en %': 'Beneficio %'
        }
        for old_name, new_name in rename_dict.items():
            if old_name in df.columns and new_name not in df.columns:
                df = df.rename(columns={old_name: new_name})

        if 'Comisiones 10 %' in df.columns:
            if 'Comisiones Pagadas' not in df.columns:
                df = df.rename(columns={'Comisiones 10 %': 'Comisiones Pagadas'})
            else:
                df = df.drop(columns=['Comisiones 10 %'])

        # Valores fijos
        capital_inicial = df['Aumento Capital'].iloc[1] if len(df) > 1 else 0
        id_inversionista = df['ID Inv'].iloc[1] if len(df) > 1 else "N/D"
        
        # Aplicar filtros
        filtered_df = advanced_filters(df)

        # Aplicar estilo personalizado a los KPIs
        aplicar_estilo_kpis()

        # =============================================
        # SECCIÓN DE KPIs CON NUEVO ESTILO
        # =============================================
        
        st.markdown("---")
        st.markdown('<h2 style="color: #2c3e50; border-bottom: 2px solid #67e4da; padding-bottom: 10px;">📊 KPIs Financieros</h2>', unsafe_allow_html=True)
        
        def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False, delta=None):
            if pd.isna(value) or value is None:
                st.metric(label=f"{icon} {title}", value="N/D")
                return
            
            if is_currency:
                formatted_value = f"${value:,.2f}"
            elif is_percentage:
                formatted_value = f"{value:.2f}%"
            else:
                formatted_value = str(value)
            
            st.metric(
                label=f"{icon} {title}",
                value=formatted_value,
                delta=delta
            )

        # Primera fila de KPIs
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            display_kpi("ID Inversionista", id_inversionista, "🆔", is_currency=False)
        with col2:
            display_kpi("Capital Inicial", capital_inicial, "🏁")
        with col3:
            current_capital = filtered_df['Capital Invertido'].iloc[-1] if len(filtered_df) > 0 else 0
            delta_capital = current_capital - capital_inicial if len(filtered_df) > 0 else 0
            display_kpi("Capital Actual", current_capital, "🏦", delta=f"{delta_capital:+,.2f}")
        with col4:
            if 'Ganancias/Pérdidas Brutas' in filtered_df.columns and capital_inicial != 0:
                porcentaje_beneficio = (filtered_df['Ganancias/Pérdidas Brutas'].sum() / capital_inicial) * 100
                display_kpi("Porcentaje Beneficio", porcentaje_beneficio, "📊", is_percentage=True)
            else:
                display_kpi("Porcentaje Beneficio", None, "📊", is_percentage=True)

        # Segunda fila de KPIs
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            display_kpi("Total Aumentos", filtered_df['Aumento Capital'].sum(), "📈")
        with col6:
            display_kpi("Ganancias Brutas", filtered_df['Ganancias/Pérdidas Brutas'].sum() if 'Ganancias/Pérdidas Brutas' in filtered_df.columns else None, "💵")
        with col7:
            display_kpi("Ganancias Netas", filtered_df['Ganancias/Pérdidas Netas'].sum() if 'Ganancias/Pérdidas Netas' in filtered_df.columns else None, "💰")
        with col8:
            display_kpi("Comisiones Pagadas", filtered_df['Comisiones Pagadas'].sum() if 'Comisiones Pagadas' in filtered_df.columns else None, "💸")

        # Tercera fila de KPIs
        col9, col10, col11, col12 = st.columns(4)
        with col9:
            display_kpi("Retiro de Dinero", filtered_df['Retiro de Fondos'].sum() if 'Retiro de Fondos' in filtered_df.columns else None, "↘️")

        # [Resto del código de gráficos permanece igual...]

    except Exception as e:
        st.error(f"🚨 Error crítico al procesar el archivo: {str(e)}")
else:
    st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")

