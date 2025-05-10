import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Dashboard Financiero Acumulativo", layout="wide")
st.title("📈 Dashboard Financiero con Proyección Acumulativa")

# Cargar el archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # Leer el archivo Excel con manejo de errores
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        
        if not sheet_names:
            st.error("El archivo Excel no contiene hojas válidas")
            st.stop()
            
        selected_sheet = st.selectbox("Selecciona la hoja a analizar", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        
        # Verificar si el DataFrame está vacío
        if df.empty:
            st.error("La hoja seleccionada está vacía o no contiene datos")
            st.stop()

        # Sidebar con metadatos
        st.sidebar.subheader("Información del archivo")
        st.sidebar.write(f"📄 Nombre: {uploaded_file.name}")
        st.sidebar.write(f"📅 Fecha carga: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.sidebar.write(f"📋 Hoja seleccionada: {selected_sheet}")
        st.sidebar.write(f"📊 Total filas: {len(df)}")
        st.sidebar.write(f"📈 Total columnas: {len(df.columns)}")

        # =================================================================
        # 🔢 SECCIÓN 1: KPIs DINÁMICOS (Con comprobación de columnas)
        # =================================================================
        st.subheader("📊 KPIs Clave")
        
        # Función segura para obtener el último valor
        def get_last_safe(series, default=0):
            try:
                return series.iloc[-1] if len(series) > 0 else default
            except:
                return default
        
        # Verificar y preparar columnas
        capital_col = 'Capital Invertido' if 'Capital Invertido' in df.columns else df.columns[0] if len(df.columns) > 0 else None
        ganancias_col = 'Ganancias Netas' if 'Ganancias Netas' in df.columns else df.columns[1] if len(df.columns) > 1 else capital_col
        aumento_col = 'Aumento Capital' if 'Aumento Capital' in df.columns else df.columns[2] if len(df.columns) > 2 else ganancias_col
        
        # Calcular KPIs con manejo seguro
        col1, col2, col3 = st.columns(3)
        
        with col1:
            capital_actual = get_last_safe(df[capital_col]) if capital_col else 0
            st.metric("Capital Invertido Actual", 
                     f"${capital_actual:,.2f}" if capital_col else "No disponible", 
                     help="Último valor registrado")
        
        with col2:
            ganancias_actual = get_last_safe(df[ganancias_col]) if ganancias_col else 0
            st.metric("Últimas Ganancias Netas", 
                     f"${ganancias_actual:,.2f}" if ganancias_col else "No disponible", 
                     help="Ganancias del último período")
        
        with col3:
            aumento_actual = get_last_safe(df[aumento_col]) if aumento_col else 0
            st.metric("Último Aumento Capital", 
                     f"${aumento_actual:,.2f}" if aumento_col else "No disponible", 
                     help="Inyección de capital más reciente")

        # =================================================================
        # 🚀 SECCIÓN 2: PROYECCIÓN ACUMULATIVA (Con validaciones)
        # =================================================================
        st.markdown("---")
        st.subheader("🔮 Proyección Acumulativa a 3 Años")
        
        # Configuración de parámetros con valores por defecto seguros
        col4, col5, col6 = st.columns(3)
        
        with col4:
            tasa_anual = st.slider("Tasa de crecimiento anual (%)", 
                                 min_value=0.0, 
                                 max_value=50.0, 
                                 value=10.0, 
                                 step=0.5)
        
        with col5:
            # Usar capital_actual si está disponible, de lo contrario permitir entrada manual
            capital_inicial = st.number_input("Capital inicial ($)", 
                                           min_value=0.0, 
                                           value=float(capital_actual) if capital_col else 10000.0,
                                           step=1000.0)
        
        with col6:
            aumento_anual = st.number_input("Aumento capital anual ($)", 
                                          min_value=0.0, 
                                          value=5000.0,
                                          step=1000.0)

        # Función de proyección mejorada con validaciones
        def proyeccion_acumulativa(capital_inicial, tasa_anual, meses, aumento_anual=0):
            try:
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
            except Exception as e:
                st.error(f"Error en proyección: {str(e)}")
                return pd.DataFrame()

        # Calcular proyecciones con manejo de errores
        meses_proyeccion = 36  # 3 años
        proyeccion_base = proyeccion_acumulativa(capital_inicial, tasa_anual, meses_proyeccion)
        proyeccion_aumento = proyeccion_acumulativa(capital_inicial, tasa_anual, meses_proyeccion, aumento_anual)
        
        if not proyeccion_base.empty and not proyeccion_aumento.empty:
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
                try:
                    final_values = df_proyeccion[df_proyeccion['Fecha'] == df_proyeccion['Fecha'].max()]
                    if len(final_values) >= 2:
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
                except Exception as e:
                    st.warning(f"No se pudo generar comparación: {str(e)}")

            with tab2:
                try:
                    st.dataframe(
                        df_proyeccion.style.format({
                            'Fecha': lambda x: x.strftime('%Y-%m-%d'),
                            'Capital Invertido': '${:,.2f}',
                            'Ganancias Netas': '${:,.2f}',
                            'Aumento Capital': '${:,.2f}'
                        }),
                        height=500
                    )
                except Exception as e:
                    st.error(f"Error al mostrar datos: {str(e)}")

        # =================================================================
        # 📌 SECCIÓN 3: ANÁLISIS DE DATOS ORIGINALES (Con validaciones)
        # =================================================================
        st.markdown("---")
        st.subheader("📌 Análisis de Datos Históricos")
        
        if st.checkbox("Mostrar datos originales"):
            try:
                # Formatear columnas numéricas si existen
                format_dict = {}
                for col in df.select_dtypes(include=['float64', 'int64']).columns:
                    format_dict[col] = '${:,.2f}'
                
                st.dataframe(df.style.format(format_dict), height=300)
                
                if 'Fecha' in df.columns:
                    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
                    if numeric_cols:
                        fig_historico = px.line(
                            df,
                            x='Fecha',
                            y=numeric_cols,
                            title='Evolución Histórica'
                        )
                        st.plotly_chart(fig_historico, use_container_width=True)
            except Exception as e:
                st.error(f"Error al mostrar datos históricos: {str(e)}")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.error("Por favor verifica que el archivo tenga el formato correcto y contenga datos válidos.")
else:
    st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")












