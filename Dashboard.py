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
# FUNCIÓN DE FILTROS AVANZADOS CORREGIDA
# =============================================

def advanced_filters(df):
    """Función corregida para filtros avanzados que evita el error de variables no asociadas"""
    with st.sidebar.expander("🔍 Filtros Avanzados", expanded=False):
        # Creamos una copia del DataFrame para no modificar el original
        filtered_df = df.copy()
        
        # 1. Filtro por rango de fechas
        if 'Fecha' in filtered_df.columns:
            try:
                # Convertimos a datetime y obtenemos min/max
                filtered_df['Fecha'] = pd.to_datetime(filtered_df['Fecha'])
                min_date = filtered_df['Fecha'].min().date()
                max_date = filtered_df['Fecha'].max().date()
                
                # Widget para selección de rango
                selected_dates = st.date_input(
                    "Seleccione rango de fechas",
                    [min_date, max_date],
                    min_value=min_date,
                    max_value=max_date
                )
                
                # Aplicamos filtro solo si se seleccionaron dos fechas
                if len(selected_dates) == 2:
                    start_date, end_date = selected_dates
                    filtered_df = filtered_df[
                        (filtered_df['Fecha'].dt.date >= start_date) & 
                        (filtered_df['Fecha'].dt.date <= end_date)
                    ]
            except Exception as e:
                st.warning(f"No se pudo aplicar el filtro de fechas: {str(e)}")
        
        # 2. Filtro por capital invertido
        if 'Capital Invertido' in filtered_df.columns:
            try:
                # Convertimos a numérico y eliminamos NaN
                capital_series = pd.to_numeric(
                    filtered_df['Capital Invertido'], 
                    errors='coerce'
                ).dropna()
                
                if not capital_series.empty:
                    min_cap = float(capital_series.min())
                    max_cap = float(capital_series.max())
                    
                    # Widget de slider para rango de capital
                    cap_range = st.slider(
                        "Seleccione rango de capital",
                        min_value=min_cap,
                        max_value=max_cap,
                        value=(min_cap, max_cap),
                        help="Filtre por rango de capital invertido"
                    )
                    
                    # Aplicamos filtro
                    filtered_df = filtered_df[
                        (pd.to_numeric(filtered_df['Capital Invertido'], errors='coerce') >= cap_range[0]) & 
                        (pd.to_numeric(filtered_df['Capital Invertido'], errors='coerce') <= cap_range[1])
                    ]
                else:
                    st.warning("No hay valores numéricos válidos en 'Capital Invertido'")
            except Exception as e:
                st.warning(f"No se pudo aplicar el filtro de capital: {str(e)}")
        
        # 3. Filtro por tipo de ganancias
        if 'Ganancias/Pérdidas Brutas' in filtered_df.columns:
            try:
                # Widget de selección
                profit_filter = st.selectbox(
                    "Filtrar por resultados",
                    options=["Todos", "Solo ganancias", "Solo pérdidas"],
                    index=0,
                    help="Filtre por tipo de resultados financieros"
                )
                
                # Aplicamos filtro según selección
                if profit_filter == "Solo ganancias":
                    filtered_df = filtered_df[filtered_df['Ganancias/Pérdidas Brutas'] >= 0]
                elif profit_filter == "Solo pérdidas":
                    filtered_df = filtered_df[filtered_df['Ganancias/Pérdidas Brutas'] < 0]
            except Exception as e:
                st.warning(f"No se pudo aplicar el filtro de ganancias: {str(e)}")
    
    return filtered_df

# =============================================
# INTERFAZ PRINCIPAL
# =============================================

# Sidebar con controles
with st.sidebar:
    st.title("⚙️ Configuración")
    theme = st.radio("Seleccionar tema", ["Claro", "Oscuro"], index=0)
    animations = st.checkbox("Activar animaciones", value=True)

# Título principal
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
        with st.spinner('Cargando datos...'):
            time.sleep(1)
    
    try:
        # Leer archivo Excel
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("📋 Seleccionar hoja de trabajo", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

        # --- CORRECCIÓN PARA COLUMNAS DUPLICADAS ---
        # 1. Eliminar columnas completamente duplicadas
        df = df.loc[:, ~df.columns.duplicated()]

        # 2. Renombrar columnas MANUALMENTE verificando existencia
        rename_dict = {
            'Ganacias/Pérdidas Brutas': 'Ganancias/Pérdidas Brutas',
            'Ganacias/Pérdidas Netas': 'Ganancias/Pérdidas Netas',
            'Beneficio en %': 'Beneficio %'
        }

        # Solo renombrar si la columna origen existe y la destino NO existe
        for old_name, new_name in rename_dict.items():
            if old_name in df.columns and new_name not in df.columns:
                df = df.rename(columns={old_name: new_name})

        # 3. Manejar columnas de comisiones ESPECIALMENTE
        if 'Comisiones 10 %' in df.columns:
            if 'Comisiones Pagadas' not in df.columns:
                df = df.rename(columns={'Comisiones 10 %': 'Comisiones Pagadas'})
            else:
                # Si ambas existen, conservar solo 'Comisiones Pagadas'
                df = df.drop(columns=['Comisiones 10 %'])

        # Obtener valores fijos (no afectados por filtros)
        capital_inicial = df['Aumento Capital'].iloc[1] if len(df) > 1 else 0
        id_inversionista = df['ID Inv'].iloc[1] if len(df) > 1 else "N/D"
        
        # Aplicar filtros avanzados (función corregida)
        filtered_df = advanced_filters(df)

        # Verificar columnas críticas en los datos filtrados
        required_columns = ['Fecha', 'Capital Invertido', 'Aumento Capital', 'ID Inv']
        missing_cols = [col for col in required_columns if col not in filtered_df.columns]
        
        if missing_cols:
            st.error(f"🚨 Error: Faltan columnas críticas: {', '.join(missing_cols)}")
            st.stop()

        # Mostrar métricas con los datos filtrados
        st.success(f"✅ Datos cargados correctamente ({len(filtered_df)} registros)")
        
        # =============================================
        # SECCIÓN DE KPIs
        # =============================================
        
        st.markdown("---")
        st.markdown('<h2 style="color: #2c3e50; border-bottom: 2px solid #67e4da; padding-bottom: 10px;">📊 KPIs Financieros</h2>', unsafe_allow_html=True)
        
        # Función para mostrar KPIs
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

        # Primera fila de KPIs (valores fijos y principales)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            # KPI de ID Inversionista (segunda casilla de 'ID Inv')
            display_kpi("ID Inversionista", id_inversionista, "🆔", is_currency=False)
            
        with col2:
            # KPI de Capital Inicial (segunda casilla de 'Aumento Capital')
            display_kpi("Capital Inicial", capital_inicial, "🏁")
            
        with col3:
            # KPI de Capital Actual (afectado por filtros)
            current_capital = filtered_df['Capital Invertido'].iloc[-1] if len(filtered_df) > 0 else 0
            delta_capital = current_capital - capital_inicial if len(filtered_df) > 0 else 0
            display_kpi("Capital Actual", current_capital, "🏦", delta=f"{delta_capital:+,.2f}")
            
        with col4:
            # KPI de Porcentaje de Beneficio (Ganancias Brutas / Capital Inicial)
            if 'Ganancias/Pérdidas Brutas' in filtered_df.columns and capital_inicial != 0:
                ganancias_brutas = filtered_df['Ganancias/Pérdidas Brutas'].sum()
                porcentaje_beneficio = (ganancias_brutas / capital_inicial) * 100
                display_kpi("Porcentaje Beneficio", porcentaje_beneficio, "📊", is_percentage=True)
            else:
                display_kpi("Porcentaje Beneficio", None, "📊", is_percentage=True)

        # Segunda fila de KPIs (valores afectados por filtros)
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            # KPI de Total Aumentos
            total_aumentos = filtered_df['Aumento Capital'].sum()
            display_kpi("Total Aumentos", total_aumentos, "📈")
            
        with col6:
            # KPI de Ganancias Brutas
            ganancias_brutas = filtered_df['Ganancias/Pérdidas Brutas'].sum() if 'Ganancias/Pérdidas Brutas' in filtered_df.columns else None
            display_kpi("Ganancias Brutas", ganancias_brutas, "💵")
            
        with col7:
            # KPI de Ganancias Netas
            ganancias_netas = filtered_df['Ganancias/Pérdidas Netas'].sum() if 'Ganancias/Pérdidas Netas' in filtered_df.columns else None
            display_kpi("Ganancias Netas", ganancias_netas, "💰")
            
        with col8:
            # KPI de Comisiones Pagadas
            comisiones = filtered_df['Comisiones Pagadas'].sum() if 'Comisiones Pagadas' in filtered_df.columns else None
            display_kpi("Comisiones Pagadas", comisiones, "💸")

        # =============================================
        # SECCIÓN DE GRÁFICOS
        # =============================================
        
        st.markdown("---")
        st.markdown('<h2 style="color: #2c3e50; border-bottom: 2px solid #67e4da; padding-bottom: 10px;">📈 Visualizaciones</h2>', unsafe_allow_html=True)
        
        # Gráfico de evolución temporal del capital
        if 'Fecha' in filtered_df.columns and 'Capital Invertido' in filtered_df.columns:
            try:
                fig1 = px.line(
                    filtered_df,
                    x='Fecha',
                    y='Capital Invertido',
                    title='Evolución del Capital Invertido',
                    labels={'Capital Invertido': 'Monto ($)', 'Fecha': 'Fecha'},
                    template='plotly_white'
                )
                # Añadir línea horizontal para el capital inicial
                fig1.add_hline(y=capital_inicial, line_dash="dash", line_color="green", 
                              annotation_text=f"Capital Inicial: ${capital_inicial:,.2f}", 
                              annotation_position="bottom right")
                fig1.update_layout(height=400)
                st.plotly_chart(fig1, use_container_width=True)
            except Exception as e:
                st.error(f"Error al generar gráfico de capital: {str(e)}")

        # Gráfico de barras para ganancias/pérdidas
        if 'Ganancias/Pérdidas Brutas' in filtered_df.columns and 'Fecha' in filtered_df.columns:
            try:
                fig2 = px.bar(
                    filtered_df,
                    x='Fecha',
                    y='Ganancias/Pérdidas Brutas',
                    title='Ganancias/Pérdidas Brutas por Periodo',
                    color='Ganancias/Pérdidas Brutas',
                    color_continuous_scale=px.colors.diverging.RdYlGn,
                    labels={'Ganancias/Pérdidas Brutas': 'Monto ($)', 'Fecha': 'Fecha'},
                    template='plotly_white'
                )
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)
            except Exception as e:
                st.error(f"Error al generar gráfico de ganancias: {str(e)}")

        # Gráfico de dispersión: Capital vs Ganancias
        if 'Capital Invertido' in filtered_df.columns and 'Ganancias/Pérdidas Brutas' in filtered_df.columns:
            try:
                fig3 = px.scatter(
                    filtered_df,
                    x='Capital Invertido',
                    y='Ganancias/Pérdidas Brutas',
                    title='Relación entre Capital Invertido y Ganancias',
                    color='Ganancias/Pérdidas Brutas',
                    size='Ganancias/Pérdidas Brutas',
                    hover_data=['Fecha'],
                    color_continuous_scale=px.colors.diverging.RdYlGn,
                    template='plotly_white'
                )
                fig3.update_layout(height=500)
                st.plotly_chart(fig3, use_container_width=True)
            except Exception as e:
                st.error(f"Error al generar gráfico de dispersión: {str(e)}")

        # Gráfico de área para comisiones acumuladas
        if 'Comisiones Pagadas' in filtered_df.columns and 'Fecha' in filtered_df.columns:
            try:
                filtered_df['Comisiones Acumuladas'] = filtered_df['Comisiones Pagadas'].cumsum()
                fig4 = px.area(
                    filtered_df,
                    x='Fecha',
                    y='Comisiones Acumuladas',
                    title='Comisiones Pagadas Acumuladas',
                    labels={'Comisiones Acumuladas': 'Monto ($)', 'Fecha': 'Fecha'},
                    template='plotly_white'
                )
                fig4.update_layout(height=400)
                st.plotly_chart(fig4, use_container_width=True)
            except Exception as e:
                st.error(f"Error al generar gráfico de comisiones: {str(e)}")

    except Exception as e:
        st.error(f"🚨 Error crítico al procesar el archivo: {str(e)}")
else:
    st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")

# Estilos CSS
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
    }
    div[data-testid="metric-container"] > div {
        color: #2c3e50 !important;
        font-weight: 700 !important;
        font-size: 24px !important;
    }
    .stPlotlyChart {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 15px;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

