import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Financiero - Estilo Personalizado",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para las tarjetas de métricas
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: #5ED6DC;
        border: 1px solid #5ED6DC;
        border-left: 5px solid #67e4da;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    div[data-testid="metric-container"] > label {
        color: #2c3e50 !important;
        font-weight: 600 !important;
        font-size: 16px !important;
    }
    div[data-testid="metric-container"] > div {
        color: #2c3e50 !important;
        font-weight: 700 !important;
        font-size: 24px !important;
    }
    .positive {
        color: #2ecc71 !important;
    }
    .negative {
        color: #e74c3c !important;
    }
    .header-style {
        color: #2c3e50;
        border-bottom: 2px solid #67e4da;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Título principal con estilo personalizado
st.markdown('<h1 style="color: #2c3e50; border-bottom: 3px solid #67e4da; padding-bottom: 10px;">📊 Dashboard Financiero</h1>', unsafe_allow_html=True)

# Cargar archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # Leer archivo Excel
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("Selecciona la hoja a analizar", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

        # Limpiar nombres de columnas duplicadas
        df = df.loc[:, ~df.columns.duplicated()]

        # Renombrar columnas según los nombres correctos
        column_mapping = {
            'Ganacias/Pérdidas Brutas': 'Ganancias/Pérdidas Brutas',
            'Ganacias/Pérdidas Netas': 'Ganancias/Pérdidas Netas',
            'Beneficio en %': 'Beneficio %',
            'Comisiones 10 %': 'Comisiones Pagadas'
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

        # Verificar columnas críticas
        required_columns = ['Fecha', 'Capital Invertido', 'Aumento Capital']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            st.error(f"Error: Faltan columnas críticas: {', '.join(missing_cols)}")
            st.stop()

        # =================================================================
        # SECCIÓN 1: KPIs CON ESTILO PERSONALIZADO
        # =================================================================
        st.markdown('<h2 class="header-style">📌 KPIs Financieros</h2>', unsafe_allow_html=True)

        # Función para mostrar KPIs con estilo
        def display_kpi(title, value, is_currency=True, is_percentage=False, delta_value=None):
            if pd.isna(value) or value is None:
                st.metric(label=title, value="N/D")
                return
            
            if is_currency:
                formatted_value = f"${value:,.2f}"
            elif is_percentage:
                formatted_value = f"{value:.2f}%"
            else:
                formatted_value = str(value)
            
            delta = None
            delta_color = "normal"
            
            if delta_value is not None and not pd.isna(delta_value):
                if is_percentage:
                    delta = f"{delta_value:.2f}%"
                else:
                    delta = f"{delta_value:+,.2f}"
                
                delta_color = "inverse" if delta_value < 0 else "normal"
            
            st.metric(
                label=title,
                value=formatted_value,
                delta=delta,
                delta_color=delta_color
            )

        # Fila 1 de KPIs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            display_kpi("Capital Invertido (Acumulado)", df['Capital Invertido'].iloc[-1])
        
        with col2:
            display_kpi("Suma Aumento Capital", df['Aumento Capital'].sum())
        
        with col3:
            display_kpi("Capital Inicial", df['Capital Invertido'].iloc[0])

        # Fila 2 de KPIs
        col4, col5, col6 = st.columns(3)
        
        with col4:
            bruto = df['Ganancias/Pérdidas Brutas'].sum() if 'Ganancias/Pérdidas Brutas' in df.columns else None
            display_kpi("Total Ganancias/Pérdidas Brutas", bruto)
        
        with col5:
            comisiones = df['Comisiones Pagadas'].sum() if 'Comisiones Pagadas' in df.columns else None
            display_kpi("Total Comisiones Pagadas", comisiones)
        
        with col6:
            if 'Ganancias/Pérdidas Netas' in df.columns:
                neto = df['Ganancias/Pérdidas Netas'].sum()
            elif bruto is not None and comisiones is not None:
                neto = bruto - comisiones
            else:
                neto = None
                
            display_kpi("Total Ganancias/Pérdidas Netas", neto)

        # Fila 3 de KPIs
        col7, col8, col9 = st.columns(3)
        
        with col7:
            avg_beneficio = df['Beneficio %'].mean() if 'Beneficio %' in df.columns else None
            display_kpi("Promedio Beneficio %", avg_beneficio, is_currency=False, is_percentage=True)
        
        with col8:
            avg_mensual = df['Ganancias/Pérdidas Brutas'].mean() if 'Ganancias/Pérdidas Brutas' in df.columns else None
            display_kpi("Promedio Mensual Ganancias", avg_mensual)
        
        with col9:
            if 'Capital Invertido' in df.columns and len(df) > 0 and 'Ganancias/Pérdidas Netas' in df.columns:
                roi = (df['Ganancias/Pérdidas Netas'].sum() / df['Capital Invertido'].iloc[0]) * 100
                display_kpi("ROI (Retorno sobre Inversión)", roi, is_currency=False, is_percentage=True)
            else:
                display_kpi("ROI (Retorno sobre Inversión)", None)

        # =================================================================
        # SECCIÓN 2: GRÁFICOS
        # =================================================================
        st.markdown('<h2 class="header-style">📈 Visualización de Datos</h2>', unsafe_allow_html=True)

        # Gráfico 1: Aumento de Capital vs Fecha
        st.subheader("Aumento de Capital por Fecha")
        
        try:
            plot_data = df[['Fecha', 'Aumento Capital']].copy()
            plot_data['Fecha'] = pd.to_datetime(plot_data['Fecha'], errors='coerce')
            plot_data = plot_data.dropna()
            
            if not plot_data.empty:
                fig = px.bar(
                    plot_data,
                    x='Fecha',
                    y='Aumento Capital',
                    title='Aumento de Capital por Fecha',
                    labels={'Aumento Capital': 'Monto ($)', 'Fecha': 'Fecha'},
                    color='Aumento Capital',
                    color_continuous_scale=['#5ED6DC', '#67e4da', '#2c3e50']
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No hay datos válidos para mostrar")
        except Exception as e:
            st.error(f"Error al generar gráfico: {str(e)}")

        # Gráfico 2: Evolución del Capital Invertido
        st.subheader("Evolución del Capital Invertido")
        
        try:
            capital_data = df[['Fecha', 'Capital Invertido']].copy()
            capital_data['Fecha'] = pd.to_datetime(capital_data['Fecha'], errors='coerce')
            capital_data = capital_data.dropna()
            
            if not capital_data.empty:
                fig = px.line(
                    capital_data,
                    x='Fecha',
                    y='Capital Invertido',
                    title='Evolución del Capital Invertido',
                    labels={'Capital Invertido': 'Monto ($)', 'Fecha': 'Fecha'},
                    color_discrete_sequence=['#67e4da']
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error al generar gráfico: {str(e)}")

        # =================================================================
        # SECCIÓN 3: DATOS TABULARES
        # =================================================================
        st.markdown('<h2 class="header-style">📋 Datos Financieros</h2>', unsafe_allow_html=True)
        
        try:
            st.dataframe(df.style.format({
                'Capital Invertido': '${:,.2f}',
                'Aumento Capital': '${:,.2f}',
                'Ganancias/Pérdidas Brutas': '${:,.2f}',
                'Comisiones Pagadas': '${:,.2f}',
                'Ganancias/Pérdidas Netas': '${:,.2f}',
                'Beneficio %': '{:.2f}%'
            }), height=400)
        except Exception as e:
            st.error(f"Error al mostrar datos: {str(e)}")
            st.dataframe(df)  # Mostrar sin formateo si falla

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.error("Por favor verifica que el archivo tenga el formato correcto.")
else:
    st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")








