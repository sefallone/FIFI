import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Dashboard Financiero", layout="wide")

# Título del dashboard
st.title("📈 Dashboard Financiero con Proyecciones")

# Cargar el archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel con datos financieros", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # Leer todas las hojas del Excel
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        
        # Seleccionar hoja a analizar
        selected_sheet = st.selectbox("Selecciona la hoja con datos financieros", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        
        # Mostrar metadatos del archivo
        st.sidebar.subheader("Información del archivo")
        st.sidebar.write(f"📄 Nombre: {uploaded_file.name}")
        st.sidebar.write(f"📅 Fecha carga: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.sidebar.write(f"📋 Hoja seleccionada: {selected_sheet}")
        
        # Identificar columnas clave
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        # Sección de KPIs financieros
        st.subheader("🔍 Indicadores Clave")
        
        # Verificar si tenemos columnas necesarias para proyecciones
        if 'Ganancias' not in df.columns and 'Beneficios' not in df.columns and 'Ingresos' not in df.columns:
            st.warning("No se encontraron columnas claras de ganancias/ingresos. Usando primera columna numérica para proyecciones.")
            profit_col = numeric_cols[0] if numeric_cols else None
        else:
            # Intentar identificar automáticamente la columna de ganancias
            profit_col = next((col for col in ['Ganancias', 'Beneficios', 'Ingresos', 'Profit'] if col in df.columns), None)
            if not profit_col and numeric_cols:
                profit_col = numeric_cols[0]
        
        if profit_col:
            # Calcular KPIs básicos
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_profit = df[profit_col].sum()
                st.metric(label=f"Total {profit_col}", value=f"${total_profit:,.2f}")
            
            with col2:
                avg_profit = df[profit_col].mean()
                st.metric(label=f"Promedio mensual {profit_col}", value=f"${avg_profit:,.2f}")
            
            with col3:
                last_profit = df[profit_col].iloc[-1]
                st.metric(label=f"Último valor {profit_col}", value=f"${last_profit:,.2f}")
            
            # Sección de proyecciones
            st.subheader("🚀 Proyección Financiera a 3 años")
            
            # Configuración de proyección
            col4, col5 = st.columns(2)
            
            with col4:
                annual_rate = st.slider("Tasa de crecimiento anual (%)", 
                                        min_value=0.0, 
                                        max_value=50.0, 
                                        value=10.0, 
                                        step=0.5,
                                        help="Tasa de interés compuesto para la proyección")
            
            with col5:
                initial_capital = st.number_input("Capital inicial para proyección ($)", 
                                                min_value=0.0, 
                                                value=float(total_profit), 
                                                step=1000.0)
            
            # Función para calcular proyección
            def calculate_projection(initial, rate, periods, additional_capital=0):
                rate_decimal = rate / 100
                dates = [datetime.now() + timedelta(days=365*i/12) for i in range(periods+1)]
                values = [initial]
                
                for i in range(1, periods+1):
                    if i % 12 == 0:  # Añadir capital adicional cada año
                        values.append(values[-1] * (1 + rate_decimal) + additional_capital)
                    else:
                        values.append(values[-1] * (1 + rate_decimal/12))
                
                return pd.DataFrame({
                    'Fecha': dates,
                    'Valor': values,
                    'Escenario': 'Sin capital adicional' if additional_capital == 0 else f'Con capital adicional (${additional_capital:,.0f})'
                })
            
            # Calcular ambos escenarios
            periods = 36  # 3 años en meses
            
            projection_no_capital = calculate_projection(initial_capital, annual_rate, periods)
            projection_with_capital = calculate_projection(initial_capital, annual_rate, periods, additional_capital=5000)
            
            # Combinar proyecciones
            all_projections = pd.concat([projection_no_capital, projection_with_capital])
            
            # Mostrar resultados
            tab1, tab2, tab3 = st.tabs(["📊 Gráfico Comparativo", "📅 Tabla de Proyección", "💡 Resumen"])
            
            with tab1:
                fig = px.line(all_projections, 
                             x='Fecha', 
                             y='Valor', 
                             color='Escenario',
                             title=f"Proyección a 3 años ({annual_rate}% tasa anual)",
                             labels={'Valor': 'Valor acumulado ($)'},
                             template='plotly_white')
                
                fig.update_layout(hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                # Mostrar tabla con puntos clave
                st.write("**Puntos clave de la proyección:**")
                
                # Resumen anual
                for scenario in all_projections['Escenario'].unique():
                    st.subheader(scenario)
                    scenario_data = all_projections[all_projections['Escenario'] == scenario]
                    
                    # Encontrar valores anuales
                    annual_data = scenario_data.iloc[::12, :]  # Tomar datos cada 12 meses
                    if len(annual_data) < 3:  # Asegurarnos de tener 3 años
                        annual_data = scenario_data.iloc[[0, 12, 24, 36], :]
                    
                    st.dataframe(annual_data.style.format({
                        'Fecha': lambda x: x.strftime('%Y-%m-%d'),
                        'Valor': '${:,.2f}'
                    }))
            
            with tab3:
                st.subheader("Resumen Comparativo")
                
                # Calcular métricas comparativas
                final_no_capital = projection_no_capital['Valor'].iloc[-1]
                final_with_capital = projection_with_capital['Valor'].iloc[-1]
                difference = final_with_capital - final_no_capital
                
                col6, col7, col8 = st.columns(3)
                
                with col6:
                    st.metric("Valor final sin capital adicional", 
                             f"${final_no_capital:,.2f}")
                
                with col7:
                    st.metric("Valor final con capital adicional", 
                             f"${final_with_capital:,.2f}")
                
                with col8:
                    st.metric("Diferencia", 
                             f"${difference:,.2f}", 
                             delta=f"{(difference/final_no_capital*100):.1f}%")
                
                st.write("""
                **Supuestos de la proyección:**
                - Tasa de crecimiento constante del {}% anual
                - Capital adicional de $5,000 inyectado al inicio de cada año
                - Interés compuesto mensual
                - No se consideran impuestos o inflación
                """.format(annual_rate))
        
        # Sección de análisis de datos original (como antes)
        st.subheader("📌 Análisis de Datos Originales")
        
        if st.checkbox("Mostrar análisis detallado de los datos"):
            columns = df.columns.tolist()
            selected_columns = st.multiselect("Selecciona columnas para analizar", 
                                             columns, 
                                             default=columns[:min(3, len(columns))])
            
            if len(selected_columns) > 0:
                st.write("**Estadísticas descriptivas:**")
                st.dataframe(df[selected_columns].describe())
                
                chart_type = st.selectbox("Tipo de gráfico", 
                                        ["Línea", "Barras", "Histograma"])
                
                if chart_type == "Línea":
                    fig = px.line(df, x=selected_columns[0], y=selected_columns[1:])
                elif chart_type == "Barras":
                    fig = px.bar(df, x=selected_columns[0], y=selected_columns[1:])
                elif chart_type == "Histograma":
                    fig = px.histogram(df, x=selected_columns[0])
                
                st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
else:
    st.info("👋 Por favor, sube un archivo Excel con datos financieros para comenzar el análisis.")













