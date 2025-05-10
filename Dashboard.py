import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# Configuración de la página (se mantiene igual)
st.set_page_config(page_title="Dashboard Avanzado", layout="wide")
st.title("📊 Dashboard Financiero con Proyecciones")

# --- Carga de archivo y manejo de hojas (se mantiene igual) ---
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("Selecciona la hoja a analizar", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

        # --- Sidebar con metadatos (se mantiene igual) ---
        st.sidebar.subheader("Información del archivo")
        st.sidebar.write(f"📄 Nombre: {uploaded_file.name}")
        st.sidebar.write(f"📅 Fecha carga: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.sidebar.write(f"📋 Hoja seleccionada: {selected_sheet}")
        st.sidebar.write(f"📊 Total filas: {len(df)}")
        st.sidebar.write(f"📈 Total columnas: {len(df.columns)}")

        # --- Identificación de columnas numéricas (se mantiene igual) ---
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        # --- Sección de KPIs (se mantiene igual) ---
        st.subheader("📌 KPIs Principales")
        col1, col2, col3 = st.columns(3)
        
        if len(numeric_cols) > 0:
            with col1:
                total = df[numeric_cols[0]].sum()
                st.metric(f"Total {numeric_cols[0]}", f"${total:,.2f}")
            
            with col2:
                avg = df[numeric_cols[0]].mean()
                st.metric(f"Promedio {numeric_cols[0]}", f"${avg:,.2f}")
            
            with col3:
                last_value = df[numeric_cols[0]].iloc[-1]
                st.metric(f"Último valor {numeric_cols[0]}", f"${last_value:,.2f}")

        # =================================================================
        # --- 🆕 NUEVA SECCIÓN: PROYECCIÓN DE GANANCIAS A 3 AÑOS ---
        # =================================================================
        st.markdown("---")
        st.subheader("🚀 Proyección de Ganancias (Interés Compuesto)")

        # Widgets para configurar la proyección
        col4, col5 = st.columns(2)
        
        with col4:
            annual_rate = st.slider(
                "Tasa de crecimiento anual (%)", 
                min_value=0.0, 
                max_value=50.0, 
                value=10.0, 
                step=0.5,
                help="Tasa de interés compuesto para la proyección"
            )
        
        with col5:
            initial_capital = st.number_input(
                "Capital inicial ($)", 
                min_value=0.0, 
                value=float(total) if 'total' in locals() else 10000.0, 
                step=1000.0
            )

        # Función para calcular proyección (nueva)
        def calculate_projection(initial, rate, periods, additional_capital=0):
            rate_decimal = rate / 100
            dates = [datetime.now() + timedelta(days=30*i) for i in range(periods+1)]  # Mensual
            values = [initial]
            
            for i in range(1, periods+1):
                if i % 12 == 0:  # Añadir capital adicional cada año
                    values.append(values[-1] * (1 + rate_decimal/12) + additional_capital)
                else:
                    values.append(values[-1] * (1 + rate_decimal/12))
            
            return pd.DataFrame({
                'Fecha': dates,
                'Valor': values,
                'Escenario': 'Sin capital adicional' if additional_capital == 0 else f'Con capital adicional (${additional_capital:,.0f})'
            })

        # Calcular proyecciones
        projection_no_capital = calculate_projection(initial_capital, annual_rate, 36)  # 36 meses = 3 años
        projection_with_capital = calculate_projection(initial_capital, annual_rate, 36, 5000)  # $5,000 adicionales/año

        # Combinar resultados
        all_projections = pd.concat([projection_no_capital, projection_with_capital])

        # Gráfico comparativo
        fig_projection = px.line(
            all_projections, 
            x='Fecha', 
            y='Valor', 
            color='Escenario',
            title=f"Proyección a 3 años ({annual_rate}% tasa anual)",
            labels={'Valor': 'Valor acumulado ($)'}
        )
        st.plotly_chart(fig_projection, use_container_width=True)

        # Mostrar tabla resumen
        st.write("**Resumen de proyección al final del período:**")
        final_values = pd.DataFrame({
            'Escenario': ['Sin capital adicional', 'Con capital adicional ($5,000/año)'],
            'Valor Final ($)': [
                projection_no_capital['Valor'].iloc[-1],
                projection_with_capital['Valor'].iloc[-1]
            ],
            'Diferencia ($)': [
                "-",
                projection_with_capital['Valor'].iloc[-1] - projection_no_capital['Valor'].iloc[-1]
            ]
        }).style.format({
            'Valor Final ($)': '${:,.2f}',
            'Diferencia ($)': '${:,.2f}'
        })
        st.dataframe(final_values)

        # --- Sección de análisis de datos original (se mantiene igual) ---
        st.markdown("---")
        st.subheader("📊 Análisis de Datos Originales")
        
        # ... (Aquí iría el resto de tu código original: filtros, gráficos interactivos, etc.)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
else:
    st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis.")













