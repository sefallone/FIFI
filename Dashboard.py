import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards
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
# FUNCIÓN DE FILTROS AVANZADOS CON SELECTOR POR MES/AÑO
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
        
        # =============================================
        # SECCIÓN DE KPIs CON METRIC CARDS
        # =============================================
        
        st.markdown("---")
        st.markdown('<h2 style="color: #2c3e50; border-bottom: 2px solid #67e4da; padding-bottom: 10px;">📊 KPIs Financieros</h2>', unsafe_allow_html=True)
        
        def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False, delta=None):
            if pd.isna(value) or value is None:
                metric_cards(
                    title=f"{icon} {title}",
                    value="N/D",
                    key=f"card_{title}"
                )
                return
            
            if is_currency:
                formatted_value = f"${value:,.2f}"
            elif is_percentage:
                formatted_value = f"{value:.2f}%"
            else:
                formatted_value = str(value)
            
            metric_cards(
                title=f"{icon} {title}",
                value=formatted_value,
                delta=delta if delta else None,
                key=f"card_{title}"
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
                ganancias_brutas = filtered_df['Ganancias/Pérdidas Brutas'].sum()
                porcentaje_beneficio = (ganancias_brutas / capital_inicial) * 100
                display_kpi("Porcentaje Beneficio", porcentaje_beneficio, "📊", is_percentage=True)
            else:
                display_kpi("Porcentaje Beneficio", None, "📊", is_percentage=True)

        # Segunda fila de KPIs
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            total_aumentos = filtered_df['Aumento Capital'].sum()
            display_kpi("Total Aumentos", total_aumentos, "📈")
        with col6:
            ganancias_brutas = filtered_df['Ganancias/Pérdidas Brutas'].sum() if 'Ganancias/Pérdidas Brutas' in filtered_df.columns else None
            display_kpi("Ganancias Brutas", ganancias_brutas, "💵")
        with col7:
            ganancias_netas = filtered_df['Ganancias/Pérdidas Netas'].sum() if 'Ganancias/Pérdidas Netas' in filtered_df.columns else None
            display_kpi("Ganancias Netas", ganancias_netas, "💰")
        with col8:
            comisiones = filtered_df['Comisiones Pagadas'].sum() if 'Comisiones Pagadas' in filtered_df.columns else None
            display_kpi("Comisiones Pagadas", comisiones, "💸")

        # Tercera fila de KPIs (con el nuevo KPI)
        col9, col10, col11, col12 = st.columns(4)
        with col9:
            retiros = filtered_df['Retiro de Fondos'].sum() if 'Retiro de Fondos' in filtered_df.columns else None
            display_kpi("Retiro de Dinero", retiros, "↘️")
        
        # =============================================
        # SECCIÓN DE GRÁFICOS (se mantiene igual)
        # =============================================
        
        st.markdown("---")
        st.markdown('<h2 style="color: #2c3e50; border-bottom: 2px solid #67e4da; padding-bottom: 10px;">📈 Visualizaciones</h2>', unsafe_allow_html=True)
        
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
                fig1.add_hline(y=capital_inicial, line_dash="dash", line_color="green", 
                              annotation_text=f"Capital Inicial: ${capital_inicial:,.2f}", 
                              annotation_position="bottom right")
                fig1.update_layout(height=400)
                st.plotly_chart(fig1, use_container_width=True)
            except Exception as e:
                st.error(f"Error al generar gráfico de capital: {str(e)}")

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

# Estilos CSS (actualizado para mantener solo los estilos de gráficos)
st.markdown("""
<style>
    .stPlotlyChart {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 15px;
        background-color: white;
    }
    /* Estilos para mejorar el aspecto general */
    .stApp {
        background-color: #f8f9fa;
    }
    .stSidebar {
        background-color: #ffffff;
        box-shadow: 2px 0 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)
