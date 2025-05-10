import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Dashboard Financiero Acumulativo", layout="wide")
st.title("📈 Dashboard Financiero con Proyección Acumulativa")

# Cargar el archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # Leer el archivo Excel
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("Selecciona la hoja a analizar", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

        # Sidebar con metadatos
        st.sidebar.subheader("Información del archivo")
        st.sidebar.write(f"📄 Nombre: {uploaded_file.name}")
        st.sidebar.write(f"📅 Fecha carga: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.sidebar.write(f"📋 Hoja seleccionada: {selected_sheet}")

        # =================================================================
        # 🔢 SECCIÓN 1: KPIs DINÁMICOS (Capital Invertido, Ganancias Netas, Aumento Capital)
        # =================================================================
        st.subheader("📊 KPIs Clave")
        
        # Verificar columnas requeridas
        required_columns = ['Capital Invertido', 'Ganancias Netas', 'Aumento Capital']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            st.warning(f"⚠️ Faltan columnas: {', '.join(missing_cols)}. Usando primeras columnas numéricas.")
            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
            for i, col in enumerate(missing_cols):
                if i < len(numeric_cols):
                    df[col] = df[numeric_cols[i]]
        
        # Calcular KPIs (usando los últimos valores disponibles)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            capital_actual = df['Capital Invertido'].iloc[-1] if 'Capital Invertido' in df.columns else 0
            st.metric("Capital Invertido Actual", 
                     f"${capital_actual:,.2f}", 
                     help="Último valor registrado")
        
        with col2:
            ganancias_actual = df['Ganancias Netas'].iloc[-1] if 'Ganancias Netas' in df.columns else 0
            st.metric("Últimas Ganancias Netas", 
                     f"${ganancias_actual:,.2f}", 
                     help="Ganancias del último período")
        
        with col3:
            aumento_actual = df['Aumento Capital'].iloc[-1] if 'Aumento Capital' in df.columns else 0
            st.metric("Último Aumento Capital", 
                     f"${aumento_actual:,.2f}", 
                     help="Inyección de capital más reciente")

        # =================================================================
        # 🚀 SECCIÓN 2: PROYECCIÓN ACUMULATIVA (Capital + Ganancias + Aumentos)
        # =================================================================
        st.markdown("---")
        st.subheader("🔮 Proyección Acumulativa a 3 Años")
        
        # Configuración de parámetros
        col4, col5, col6 = st.columns(3)
        
        with col4:
            tasa_anual = st.slider("Tasa de crecimiento anual (%)", 
                                 min_value=0.0, 
                                 max_value=50.0, 
                                 value=10.0, 
                                 step=0.5)
        
        with col5:
            capital_inicial = st.number_input("Capital inicial ($)", 
                                           min_value=0.0, 
                                           value=float(capital_actual),
                                           step=1000.0)
        
        with col6:
            aumento_anual = st.number_input("Aumento capital anual ($)", 
                                          min_value=0.0, 
                                          value=5000.0,
                                          step=1000.0)

        # Función de proyección mejorada (acumulativa)
        def proyeccion_acumulativa(capital_inicial, tasa_anual, meses, aumento_anual=0):
            tasa_mensual = tasa_anual / 100 / 12
            fechas = []
            capital = []
            ganancias = []
            aumentos = []
            
            capital_actual = capital_inicial
            for mes in range(meses + 1):
                fecha = datetime.now() + timedelta(days=30*mes)
                fechas.append(fecha)
                
                # Calcular ganancias (interés compuesto)
                ganancia_mes = capital_actual * tasa_mensual
                
                # Aplicar aumento de capital anual
                aumento_mes = aumento_anual if mes % 12 == 0 and mes != 0 else 0
                
                # Actualizar capital (acumulativo)
                capital_actual += ganancia_mes + aumento_mes
                
                # Guardar valores
                capital.append(capital_actual)
                ganancias.append(ganancia_mes)
                aumentos.append(aumento_mes)
            
            return pd.DataFrame({
                'Fecha': fechas,
                'Capital Invertido': capital,
                'Ganancias Netas': ganancias,
                'Aumento Capital': aumentos,
                'Escenario': 'Base' if aumento_anual == 0 else f'Con +${aumento_anual:,.0f}/año'
            })

        # Calcular proyecciones
        meses_proyeccion = 36  # 3 años
        proyeccion_base = proyeccion_acumulativa(capital_inicial, tasa_anual, meses_proyeccion)
        proyeccion_aumento = proyeccion_acumulativa(capital_inicial, tasa_anual, meses_proyeccion, aumento_anual)
        
        # Combinar resultados
        df_proyeccion = pd.concat([proyeccion_base, proyeccion_aumento])

        # Mostrar resultados
        tab1, tab2 = st.tabs(["📈 Gráfico Interactivo", "📋 Datos Detallados"])

        with tab1:
            fig = px.line(
                df_proyeccion,
                x='Fecha',
                y='Capital Invertido',
                color='Escenario',
                title='Evolución del Capital Invertido',
                labels={'Capital Invertido': 'Valor ($)'},
                hover_data=['Ganancias Netas', 'Aumento Capital'],
                template='plotly_white'
            )
            fig.update_layout(hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)

            # Resumen comparativo
            st.subheader("🔍 Comparación Final")
            final_values = df_proyeccion[df_proyeccion['Fecha'] == df_proyeccion['Fecha'].max()]
            diferencia = final_values.iloc[1]['Capital Invertido'] - final_values.iloc[0]['Capital Invertido']
            
            col7, col8 = st.columns(2)
            with col7:
                st.metric("Capital Base (3 años)",
                         f"${final_values.iloc[0]['Capital Invertido']:,.2f}",
                         delta=f"Ganancias: ${final_values.iloc[0]['Ganancias Netas']:,.2f}/mes")
            
            with col8:
                st.metric(f"Con Aumento (${aumento_anual:,.0f}/año)",
                         f"${final_values.iloc[1]['Capital Invertido']:,.2f}",
                         delta=f"+${diferencia:,.2f} vs base")

        with tab2:
            st.dataframe(
                df_proyeccion.style.format({
                    'Fecha': lambda x: x.strftime('%Y-%m-%d'),
                    'Capital Invertido': '${:,.2f}',
                    'Ganancias Netas': '${:,.2f}',
                    'Aumento Capital': '${:,.2f}'
                }),
                height=500
            )

        # =================================================================
        # 📌 SECCIÓN 3: ANÁLISIS DE DATOS ORIGINALES (se mantiene igual)
        # =================================================================
        st.markdown("---")
        st.subheader("📌 Análisis de Datos Históricos")
        
        if st.checkbox("Mostrar datos originales"):
            st.dataframe(df.style.format({
                'Capital Invertido': '${:,.2f}',
                'Ganancias Netas': '${:,.2f}',
                'Aumento Capital': '${:,.2f}'
            }), height=300)
            
            if 'Fecha' in df.columns:
                fig_historico = px.line(
                    df,
                    x='Fecha',
                    y=['Capital Invertido', 'Ganancias Netas', 'Aumento Capital'],
                    title='Evolución Histórica'
                )
                st.plotly_chart(fig_historico, use_container_width=True)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
else:
    st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")













