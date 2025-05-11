import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Financiero - Versión Corregida",
    layout="wide"
)

# Título principal
st.title("📊 Dashboard Financiero Corregido")

# Cargar archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # Leer archivo Excel con manejo de errores
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("Selecciona la hoja a analizar", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

        # Verificar columnas críticas
        required_columns = ['Capital Invertido', 'Aumento Capital', 'Ganancias/Pérdidas Brutas']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            st.error(f"Error: Faltan columnas críticas: {', '.join(missing_cols)}")
            st.stop()

        # Función segura para cálculos
        def safe_divide(a, b):
            return a / b if b != 0 else 0

        # =================================================================
        # SECCIÓN 1: KPIs CORREGIDOS
        # =================================================================
        st.header("📌 KPIs Financieros - Versión Corregida")
        
        # Fila 1 de KPIs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Capital Invertido (acumulado)
            capital_invertido = df['Capital Invertido'].iloc[-1]
            st.metric("Capital Invertido (Acumulado)", f"${capital_invertido:,.2f}")
        
        with col2:
            # Suma Aumento Capital
            suma_aumento = df['Aumento Capital'].sum()
            st.metric("Suma Aumento Capital", f"${suma_aumento:,.2f}")
        
        with col3:
            # Capital Inicial
            capital_inicial = df['Capital Invertido'].iloc[0]
            st.metric("Capital Inicial", f"${capital_inicial:,.2f}")

        # Fila 2 de KPIs
        col4, col5, col6 = st.columns(3)
        
        with col4:
            # Total Ganancias/Pérdidas Brutas
            total_bruto = df['Ganancias/Pérdidas Brutas'].sum()
            st.metric("Total Ganancias/Pérdidas Brutas", 
                     f"${total_bruto:,.2f}", 
                     delta_color="inverse" if total_bruto < 0 else "normal")
        
        with col5:
            # Total Comisiones Pagadas (si existe)
            if 'Comisiones Pagadas' in df.columns:
                total_comisiones = df['Comisiones Pagadas'].sum()
                st.metric("Total Comisiones Pagadas", f"${total_comisiones:,.2f}")
            else:
                st.warning("Columna 'Comisiones Pagadas' no encontrada")
        
        with col6:
            # Total Ganancias/Pérdidas Netas (si existe)
            if 'Ganancias/Pérdidas Netas' in df.columns:
                total_neto = df['Ganancias/Pérdidas Netas'].sum()
                st.metric("Total Ganancias/Pérdidas Netas", 
                         f"${total_neto:,.2f}",
                         delta_color="inverse" if total_neto < 0 else "normal")
            else:
                # Calcular si no existe la columna
                total_neto = total_bruto - (total_comisiones if 'Comisiones Pagadas' in df.columns else 0)
                st.metric("Total Ganancias/Pérdidas Netas (Calculado)", 
                         f"${total_neto:,.2f}",
                         delta_color="inverse" if total_neto < 0 else "normal")

        # Fila 3 de KPIs
        col7, col8, col9 = st.columns(3)
        
        with col7:
            # Promedio de Beneficio % (si existe)
            if 'Beneficio %' in df.columns:
                avg_beneficio = df['Beneficio %'].mean()
                st.metric("Promedio Beneficio %", 
                         f"{avg_beneficio:.2f}%",
                         delta_color="inverse" if avg_beneficio < 0 else "normal")
            else:
                st.warning("Columna 'Beneficio %' no encontrada")
        
        with col8:
            # Promedio Mensual de Ganancias
            avg_mensual = df['Ganancias/Pérdidas Brutas'].mean()
            st.metric("Promedio Mensual Ganancias", 
                     f"${avg_mensual:,.2f}",
                     delta_color="inverse" if avg_mensual < 0 else "normal")
        
        with col9:
            # ROI
            roi = safe_divide(total_neto, capital_inicial) * 100
            st.metric("ROI (Retorno sobre Inversión)", 
                     f"{roi:.2f}%",
                     delta_color="inverse" if roi < 0 else "normal")

        # =================================================================
        # SECCIÓN 2: GRÁFICOS CORREGIDOS
        # =================================================================
        st.header("📈 Gráficos Corregidos")
        
        # Gráfico de Aumento de Capital vs Fecha - Versión corregida
        st.subheader("Aumento de Capital por Período")
        
        try:
            # Convertir fecha si es necesario
            if not pd.api.types.is_datetime64_any_dtype(df['Fecha']):
                df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            
            # Filtrar datos válidos
            plot_data = df.dropna(subset=['Fecha', 'Aumento Capital'])
            
            if not plot_data.empty:
                fig = px.bar(
                    plot_data,
                    x='Fecha',
                    y='Aumento Capital',
                    title='Aumento de Capital por Fecha',
                    labels={'Aumento Capital': 'Monto ($)', 'Fecha': 'Fecha'},
                    color='Aumento Capital',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No hay datos válidos para mostrar (valores nulos o fechas inválidas)")
        except Exception as e:
            st.error(f"Error al generar gráfico: {str(e)}")

    except Exception as e:
        st.error(f"Error crítico al procesar el archivo: {str(e)}")
else:
    st.info("Por favor, sube un archivo Excel para comenzar el análisis")











