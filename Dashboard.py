import streamlit as st

# Configuración inicial de la página (DEBE SER EL PRIMER COMANDO)
st.set_page_config(
    page_title="Dashboard Financiero Premium",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Resto de imports
import pandas as pd
import plotly.express as px
from datetime import datetime
import base64
from io import BytesIO
import time

# Configuración para metric cards
try:
    from streamlit_extras.metric_cards import metric_card
    METRIC_CARDS_ENABLED = True
except ImportError:
    METRIC_CARDS_ENABLED = False

# =============================================
# FUNCIÓN DE FILTROS AVANZADOS
# =============================================

def advanced_filters(df):
    """Función con selector de fechas por mes y año"""
    with st.sidebar.expander("🔍 Filtros Avanzados", expanded=False):
        filtered_df = df.copy()
        
        if 'Fecha' in filtered_df.columns:
            try:
                filtered_df['Fecha'] = pd.to_datetime(filtered_df['Fecha'])
                filtered_df['MesAño'] = filtered_df['Fecha'].dt.to_period('M')
                
                min_date = filtered_df['Fecha'].min().to_pydatetime()
                max_date = filtered_df['Fecha'].max().to_pydatetime()
                
                st.write("**Seleccione el rango de meses:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    start_date = st.date_input(
                        "Mes inicial",
                        value=min_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="start_date"
                    ).replace(day=1)
                
                with col2:
                    end_date = st.date_input(
                        "Mes final",
                        value=max_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="end_date"
                    ).replace(day=1)
                
                start_period = pd.to_datetime(start_date).to_period('M')
                end_period = pd.to_datetime(end_date).to_period('M')
                
                filtered_df = filtered_df[
                    (filtered_df['MesAño'] >= start_period) & 
                    (filtered_df['MesAño'] <= end_period)
                ]
                
                filtered_df = filtered_df.drop(columns=['MesAño'])
                
            except Exception as e:
                st.warning(f"No se pudo aplicar el filtro de fechas: {str(e)}")
        
        if 'Capital Invertido' in filtered_df.columns:
            try:
                capital_series = pd.to_numeric(
                    filtered_df['Capital Invertido'], 
                    errors='coerce'
                ).dropna()
                
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
                else:
                    st.warning("No hay valores numéricos válidos en 'Capital Invertido'")
            except Exception as e:
                st.warning(f"No se pudo aplicar el filtro de capital: {str(e)}")
        
        if 'Ganancias/Pérdidas Brutas' in filtered_df.columns:
            try:
                profit_filter = st.selectbox(
                    "Filtrar por resultados",
                    options=["Todos", "Solo ganancias", "Solo pérdidas"],
                    index=0,
                    help="Filtre por tipo de resultados financieros"
                )
                
                if profit_filter == "Solo ganancias":
                    filtered_df = filtered_df[filtered_df['Ganancias/Pérdidas Brutas'] >= 0]
                elif profit_filter == "Solo pérdidas":
                    filtered_df = filtered_df[filtered_df['Ganancias/Pérdidas Brutas'] < 0]
            except Exception as e:
                st.warning(f"No se pudo aplicar el filtro de ganancias: {str(e)}")
    
    return filtered_df

# =============================================
# FUNCIÓN PARA MOSTRAR KPIs CON ESTILOS DE TEMA
# =============================================

def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False, delta=None, theme="claro"):
    if pd.isna(value) or value is None:
        value_display = "N/D"
        delta_display = None
    else:
        if is_currency:
            value_display = f"${value:,.2f}"
        elif is_percentage:
            value_display = f"{value:.2f}%"
        else:
            value_display = str(value)
        
        delta_display = delta
    
    # Estilos basados en el tema
    if theme == "oscuro":
        bg_color = "#333333"
        text_color = "#ffffff"
        border_color = "#67e4da"
    else:
        bg_color = "#ffffff"
        text_color = "#000000"  # Texto negro para tema claro
        border_color = "#67e4da"
    
    if METRIC_CARDS_ENABLED:
        metric_card(
            title=f"{icon} {title}",
            value=value_display,
            delta=delta_display,
            key=f"card_{title.replace(' ', '_')}",
            background=bg_color,
            border_color=border_color,
            border_size_px=2
        )
    else:
        delta_color = "color: green;" if delta_display and str(delta_display).startswith('+') else "color: red;"
        delta_html = f"<div style='{delta_color} font-size: 14px;'>{delta_display}</div>" if delta_display else ""
        
        st.markdown(f"""
        <div style="
            background: {bg_color};
            color: {text_color};
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
            border-left: 4px solid {border_color};
        ">
            <div style="font-weight: 600; font-size: 14px;">{icon} {title}</div>
            <div style="font-weight: 700; font-size: 24px; margin: 10px 0;">{value_display}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

# =============================================
# INTERFAZ PRINCIPAL
# =============================================

def main():
    # Inicializar el tema en session_state si no existe
    if 'theme' not in st.session_state:
        st.session_state.theme = "claro"
    
    with st.sidebar:
        st.title("⚙️ Configuración")
        # Usamos un callback para actualizar el tema
        def update_theme():
            st.session_state.theme = st.session_state.theme_selector
        
        theme = st.radio(
            "Seleccionar tema",
            ["Claro", "Oscuro"],
            index=0 if st.session_state.theme == "claro" else 1,
            key="theme_selector",
            on_change=update_theme
        )
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

            capital_inicial = df['Aumento Capital'].iloc[1] if len(df) > 1 else 0
            id_inversionista = df['ID Inv'].iloc[1] if len(df) > 1 else "N/D"
            
            filtered_df = advanced_filters(df)

            required_columns = ['Fecha', 'Capital Invertido', 'Aumento Capital', 'ID Inv', 'Retiro de Fondos']
            missing_cols = [col for col in required_columns if col not in filtered_df.columns]
            
            if missing_cols:
                st.error(f"🚨 Error: Faltan columnas críticas: {', '.join(missing_cols)}")
                st.stop()

            st.success(f"✅ Datos cargados correctamente ({len(filtered_df)} registros)")
            
            # Mostrar advertencia solo si no hay metric cards
            if not METRIC_CARDS_ENABLED:
                st.warning("Para mejores visualizaciones, instala: pip install streamlit-extras")
            
            # =============================================
            # SECCIÓN DE KPIs CON TEMA APLICADO
            # =============================================
            
            st.markdown("---")
            st.markdown(f'<h2 style="color: { "#ffffff" if st.session_state.theme == "oscuro" else "#000000" }; border-bottom: 2px solid #67e4da; padding-bottom: 10px;">📊 KPIs Financieros</h2>', unsafe_allow_html=True)

            # Primera fila de KPIs
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                display_kpi("ID Inversionista", id_inversionista, "🆔", is_currency=False, theme=st.session_state.theme)
            with col2:
                display_kpi("Capital Inicial", capital_inicial, "🏁", theme=st.session_state.theme)
            with col3:
                current_capital = filtered_df['Capital Invertido'].iloc[-1] if len(filtered_df) > 0 else 0
                delta_capital = current_capital - capital_inicial if len(filtered_df) > 0 else 0
                display_kpi("Capital Actual", current_capital, "🏦", delta=f"{delta_capital:+,.2f}", theme=st.session_state.theme)
            with col4:
                if 'Ganancias/Pérdidas Brutas' in filtered_df.columns and capital_inicial != 0:
                    ganancias_brutas = filtered_df['Ganancias/Pérdidas Brutas'].sum()
                    porcentaje_beneficio = (ganancias_brutas / capital_inicial) * 100
                    display_kpi("Porcentaje Beneficio", porcentaje_beneficio, "📊", is_percentage=True, theme=st.session_state.theme)
                else:
                    display_kpi("Porcentaje Beneficio", None, "📊", is_percentage=True, theme=st.session_state.theme)

            # Resto del código de KPIs y gráficos...
            
            # Configuración de gráficos según el tema
            plotly_template = "plotly_dark" if st.session_state.theme == "oscuro" else "plotly_white"
            
            # [El resto de tus gráficos con plotly_template aplicado...]
            
        except Exception as e:
            st.error(f"🚨 Error crítico al procesar el archivo: {str(e)}")
    else:
        st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")

    # Estilos CSS dinámicos según el tema
    if st.session_state.theme == "oscuro":
        st.markdown("""
        <style>
            .stApp {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            .stSidebar {
                background-color: #262626;
                color: #ffffff;
            }
            .stTextInput, .stTextArea, .stSelectbox, .stSlider, .stDateInput {
                background-color: #333333;
                color: #ffffff;
            }
            .css-1aumxhk {
                background-color: #333333;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
            .stApp {
                background-color: #f8f9fa;
                color: #000000;
            }
            .stSidebar {
                background-color: #ffffff;
                color: #000000;
            }
            .stTextInput, .stTextArea, .stSelectbox, .stSlider, .stDateInput {
                background-color: #ffffff;
                color: #000000;
            }
            .css-1aumxhk {
                background-color: #ffffff;
            }
        </style>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
