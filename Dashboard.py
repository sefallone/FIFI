import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
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
# FUNCIÓN DE FILTROS AVANZADOS
# =============================================

def advanced_filters(df):
    """Función con selector de fechas por mes y año"""
    with st.sidebar.expander("🔍 Filtros Avanzados", expanded=True):
        filtered_df = df.copy()
        
        if 'Fecha' in filtered_df.columns:
            try:
                filtered_df['Fecha'] = pd.to_datetime(filtered_df['Fecha'], errors='coerce')
                filtered_df = filtered_df.dropna(subset=['Fecha'])
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
                
                start_period = pd.Period(start_date, freq='M')
                end_period = pd.Period(end_date, freq='M')
                
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
# FUNCIÓN PARA MOSTRAR KPIs CON TOOLTIPS
# =============================================

def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False, delta=None):
    """
    Muestra un KPI con tooltip explicativo al pasar el mouse.
    
    Parámetros:
        title (str): Nombre del KPI
        value: Valor a mostrar
        icon (str): Emoji para el KPI
        is_currency (bool): Si es valor monetario
        is_percentage (bool): Si es porcentaje
        delta: Variación del valor
    """
    # Diccionario de explicaciones para cada KPI
    kpi_explanations = {
        "ID Inversionista": "Identificador único del inversionista en el sistema.",
        "Fecha de Entrada al Fondo": "Fecha inicial de participación en el fondo de inversión.",
        "Capital Inicial": "Monto inicial invertido por el usuario.",
        "Capital Actual": "Valor actual de la inversión (incluyendo ganancias/pérdidas).",
        "Total Inyección de Capital": "Suma total de capital adicional aportado.",
        "Ganancias Brutas": "Beneficios antes de deducir comisiones e impuestos.",
        "Ganancias Netas": "Beneficios después de comisiones e impuestos.",
        "Comisiones Pagadas": "Total acumulado en comisiones de gestión.",
        "Retiro de Dinero": "Capital retirado por el inversionista.",
        "ROI": "Retorno sobre la inversión (Ganancias Netas / Capital Inicial).",
        "CAGR Mensual": "Tasa de crecimiento anual compuesto mensualizada.",
        "Drawdown Máximo": "Peor pérdida porcentual respecto al máximo histórico.",
        "Ratio Sharpe": "Medida de rendimiento ajustado al riesgo (mayor = mejor)."
    }

    # Formatear el valor
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
        
        delta_display = delta

    # Tooltip con explicación
    explanation = kpi_explanations.get(title, "Métrica financiera clave.")
    
    if METRIC_CARDS_ENABLED:
        metric_card(
            title=f"{icon} {title}",
            value=value_display,
            delta=delta_display,
            key=f"card_{title.replace(' ', '_')}",
            background="#1024ca",
            border_color="#3f33ff",
            border_size_px=2,
            help=explanation  # Tooltip añadido
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
            background: #1024ca;
            color: #ffffff;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            margin-bottom: 20px;
            border-left: 4px solid #1024ca;
            position: relative;
        ">
            <div style="font-weight: 600; font-size: 14px; color: #ffffff;">
                {icon} {title}
                <span style="font-size: 12px; color: #aaa; margin-left: 5px; cursor: pointer;" title="{explanation}">ℹ️</span>
            </div>
            <div style="font-weight: 700; font-size: 24px; margin: 10px 0;">{value_display}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

# =============================================
# GRÁFICOS MEJORADOS (resto del código se mantiene igual)
# =============================================

[...]  # El resto de tus funciones (plot_capital_profit_relation, plot_bubble_chart, etc.) se mantienen SIN cambios

# =============================================
# INTERFAZ PRINCIPAL (con KPIs actualizados)
# =============================================

def main():
    st.title("📊 Fondo de Inversión Fallone Investment")
    
    # Aplicar tema oscuro global (se mantiene igual)
    st.markdown("""
    <style>
        .stApp {
            background-color: #121212;
            color: #ffffff;
        }
        [...]
    </style>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("📤 Subir archivo Excel", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            [...]  # Código de carga de datos se mantiene igual
            
            # SECCIÓN DE KPIs CON TOOLTIPS
            st.markdown("---")
            st.markdown('<h2 style="color: #1024ca; border-bottom: 2px solid #1024ca; padding-bottom: 10px;">📊 KPIs Financieros</h2>', unsafe_allow_html=True)
            
            current_capital = filtered_df['Capital Invertido'].iloc[-1] if len(filtered_df) > 0 else 0
            delta_capital = current_capital - capital_inicial if len(filtered_df) > 0 else 0
            
            # Primera fila de KPIs (ahora con tooltips)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                display_kpi("ID Inversionista", id_inversionista, "🆔", is_currency=False)
            with col2:
                display_kpi("Fecha de Entrada al Fondo", fecha_entrada, "📅", is_currency=False)
            with col3:
                display_kpi("Capital Inicial", capital_inicial, "🏁")
            with col4:
                display_kpi("Capital Actual", current_capital, "🏦", delta=f"{delta_capital:+,.2f}")
            
            # Resto del código se mantiene igual...
            
        except Exception as e:
            st.error(f"🚨 Error crítico al procesar el archivo: {str(e)}")

if __name__ == "__main__":
    main()
