import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import base64
from io import BytesIO

# Configuración inicial de la página
st.set_page_config(
    page_title="Dashboard Fallone Investments",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración para metric cards
try:
    from streamlit_extras.metric_cards import metric_card
    METRIC_CARDS_ENABLED = True
except ImportError:
    METRIC_CARDS_ENABLED = False

# =============================================
# FUNCIÓN AUXILIAR PARA MANEJO SEGURO DE FECHAS
# =============================================

def safe_date_conversion(date_value):
    """Convierte valores a fecha de manera segura"""
    if pd.isna(date_value) or date_value is None or date_value == "N/D":
        return "N/D"
    try:
        if isinstance(date_value, (pd.Timestamp, datetime)):
            return date_value
        return pd.to_datetime(date_value)
    except:
        return "N/D"

# =============================================
# FUNCIÓN DE FILTROS AVANZADOS (sin cambios)
# =============================================

def advanced_filters(df):
    """Función con selector de fechas por mes y año"""
    with st.sidebar.expander("🔍 Filtros Avanzados", expanded=True):
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
# FUNCIÓN PARA MOSTRAR KPIs CON MANEJO SEGURO DE TIPOS
# =============================================

def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False, delta=None):
    if pd.isna(value) or value is None or value == "N/D":
        value_display = "N/D"
        delta_display = None
    else:
        if isinstance(value, (int, float)):
            if is_currency:
                value_display = f"${value:,.2f}"
            elif is_percentage:
                value_display = f"{value:.2f}%"
            else:
                value_display = str(value)
        else:
            value_display = str(value)
        
        delta_display = delta
    
    # Estilos mejorados para tema oscuro
    bg_color = "#1024ca"
    text_color = "#ffffff"
    border_color = "#3f33ff"
    highlight_color = "#1024ca"
    
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
        delta_color = "#4CAF50" if delta_display and str(delta_display).startswith('+') else "#F44336"
        delta_html = f"""
        <div style='color: {delta_color}; font-size: 14px; margin-top: 5px;'>
            {delta_display if delta_display else ''}
        </div>
        """ if delta_display else ""
        
        st.markdown(f"""
        <div style="
            background: {bg_color};
            color: {text_color};
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            margin-bottom: 20px;
            border-left: 4px solid {highlight_color};
        ">
            <div style="font-weight: 600; font-size: 14px; color: {highlight_color};">{icon} {title}</div>
            <div style="font-weight: 700; font-size: 24px; margin: 10px 0;">{value_display}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

# =============================================
# GRÁFICOS Y ANÁLISIS (sin cambios)
# =============================================

[...]  # Las funciones de gráficos se mantienen igual que en tu versión original

# =============================================
# INTERFAZ PRINCIPAL CON MANEJO DE ERRORES
# =============================================

def main():
    st.title("📊 Fondo de Inversión Fallone Investment")
    
    # Aplicar tema oscuro global
    st.markdown("""
    <style>
        .stApp {
            background-color: #121212;
            color: #ffffff;
        }
        .stSidebar {
            background-color: #1e1e1e !important;
            color: #ffffff;
        }
        .css-1aumxhk {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        .st-b7 {
            color: #ffffff;
        }
        .stTextInput, .stTextArea, .stSelectbox, .stSlider, .stDateInput {
            background-color: #2d2d2d;
            color: #ffffff;
        }
        .st-bb {
            background-color: transparent;
        }
        .st-cb {
            background-color: #2d2d2d;
        }
        .stButton>button {
            background-color: #3f33ff;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
        }
        .stButton>button:hover {
            background-color: #4d42ff;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            padding: 0 20px;
            background-color: #1e1e1e;
            border-radius: 4px 4px 0 0;
            border: 1px solid #3f33ff;
        }
        .stTabs [aria-selected="true"] {
            background-color: #3f33ff;
        }
    </style>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("📤 Subir archivo Excel", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
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
            
            # Manejo seguro de valores numéricos
            capital_inicial = float(df['Aumento Capital'].iloc[1]) if len(df) > 1 and pd.notna(df['Aumento Capital'].iloc[1]) else 0
            id_inversionista = str(df['ID Inv'].iloc[1]) if len(df) > 1 and pd.notna(df['ID Inv'].iloc[1]) else "N/D"
            
            # Manejo seguro de fechas
            fecha_entrada = safe_date_conversion(df['Fecha'].iloc[1] if len(df) > 1 else "N/D")
            if isinstance(fecha_entrada, (pd.Timestamp, datetime)):
                fecha_entrada_str = fecha_entrada.strftime('%d/%m/%Y')
                dias_en_fondo = (pd.to_datetime('today') - fecha_entrada).days
            else:
                fecha_entrada_str = "N/D"
                dias_en_fondo = "N/D"
            
            filtered_df = advanced_filters(df)
            
            required_columns = ['Fecha', 'Capital Invertido', 'Aumento Capital', 'ID Inv', 'Retiro de Fondos']
            missing_cols = [col for col in required_columns if col not in filtered_df.columns]
            
            if missing_cols:
                st.error(f"🚨 Error: Faltan columnas críticas: {', '.join(missing_cols)}")
                st.stop()
            
            st.success(f"✅ Datos cargados correctamente ({len(filtered_df)} registros)")
            
            if not METRIC_CARDS_ENABLED:
                st.warning("Para mejores visualizaciones, instala: pip install streamlit-extras")
            
            # SECCIÓN DE KPIs
            st.markdown("---")
            st.markdown('<h2 style="color: #1024ca; border-bottom: 2px solid #1024ca; padding-bottom: 10px;">📊 KPIs Financieros</h2>', unsafe_allow_html=True)
            
            # Primera fila de KPIs
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                display_kpi("ID Inversionista", id_inversionista, "🆔", is_currency=False)
            with col2:
                display_kpi("Fecha de Entrada al Fondo", fecha_entrada_str, "📅", is_currency=False)
            with col3:
                display_kpi("Capital Inicial al entrar al fondo", capital_inicial, "🏁")
            with col4:
                current_capital = float(filtered_df['Capital Invertido'].iloc[-1]) if len(filtered_df) > 0 and pd.notna(filtered_df['Capital Invertido'].iloc[-1]) else 0
                delta_capital = current_capital - capital_inicial if len(filtered_df) > 0 else 0
                display_kpi("Capital Actual", current_capital, "🏦", delta=f"{delta_capital:+,.2f}" if isinstance(delta_capital, (int, float)) else None)
            
            # Segunda fila de KPIs
            col5, col6, col7, col8 = st.columns(4)
            with col5:
                total_aumentos = float(filtered_df['Aumento Capital'].sum()) if 'Aumento Capital' in filtered_df.columns and pd.notna(filtered_df['Aumento Capital'].sum()) else 0
                display_kpi("Total Inyección de Capital", total_aumentos, "📈")
            with col6:
                ganancias_brutas = float(filtered_df['Ganancias/Pérdidas Brutas'].sum()) if 'Ganancias/Pérdidas Brutas' in filtered_df.columns and pd.notna(filtered_df['Ganancias/Pérdidas Brutas'].sum()) else None
                display_kpi("Ganancias Brutas", ganancias_brutas, "💵")
            with col7:
                ganancias_netas = float(filtered_df['Ganancias/Pérdidas Netas'].sum()) if 'Ganancias/Pérdidas Netas' in filtered_df.columns and pd.notna(filtered_df['Ganancias/Pérdidas Netas'].sum()) else None
                display_kpi("Ganancias Netas", ganancias_netas, "💰")
            with col8:
                comisiones = float(filtered_df['Comisiones Pagadas'].sum()) if 'Comisiones Pagadas' in filtered_df.columns and pd.notna(filtered_df['Comisiones Pagadas'].sum()) else None
                display_kpi("Comisiones Pagadas", comisiones, "💸")
            
            # Tercera fila de KPIs
            col9, col10, col11, col12 = st.columns(4)
            with col9:
                retiros = float(filtered_df['Retiro de Fondos'].sum()) if 'Retiro de Fondos' in filtered_df.columns and pd.notna(filtered_df['Retiro de Fondos'].sum()) else None
                display_kpi("Retiro de Dinero", retiros, "↘️")
            with col10:
                rentabilidad_acumulada = ((current_capital - capital_inicial) / capital_inicial) * 100 if capital_inicial != 0 else 0
                display_kpi("Rentabilidad Acumulada", rentabilidad_acumulada, "📊", is_percentage=True)
            with col11:
                display_kpi("Días en el Fondo", 
                           f"{dias_en_fondo} días" if isinstance(dias_en_fondo, int) else dias_en_fondo, 
                           "⏳", is_currency=False)
            
            # Resto del código de gráficos y tabs se mantiene igual
            [...]
            
        except Exception as e:
            st.error(f"Error al procesar el archivo: {str(e)}")
    else:
        st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")

if __name__ == "__main__":
    main()
