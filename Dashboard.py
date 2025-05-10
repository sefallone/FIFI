import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Financiero Completo",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("📊 Dashboard Financiero Integrado")

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
        st.sidebar.subheader("📋 Información del archivo")
        st.sidebar.write(f"📄 Nombre: {uploaded_file.name}")
        st.sidebar.write(f"📅 Fecha carga: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        st.sidebar.write(f"📌 Hoja seleccionada: {selected_sheet}")
        st.sidebar.write(f"📊 Total filas: {len(df)}")
        st.sidebar.write(f"📈 Total columnas: {len(df.columns)}")

        # =================================================================
        # 🔍 SECCIÓN 1: ANÁLISIS EXPLORATORIO
        # =================================================================
        st.header("🔍 Análisis Exploratorio")

        # Identificar columnas automáticamente
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

        # Pestañas para diferentes análisis
        tab1, tab2, tab3, tab4 = st.tabs(["📊 KPIs", "📈 Tendencia", "📌 Distribución", "🔍 Correlaciones"])

        with tab1:  # KPIs
            st.subheader("Indicadores Clave")
            
            if len(numeric_cols) >= 3:
                cols = st.columns(3)
                metrics = {
                    "Suma Total": df[numeric_cols[0]].sum(),
                    "Promedio Mensual": df[numeric_cols[0]].mean(),
                    "Máximo Registrado": df[numeric_cols[0]].max()
                }
                
                for (k, v), col in zip(metrics.items(), cols):
                    with col:
                        st.metric(
                            label=k,
                            value=f"${v:,.2f}" if isinstance(v, (int, float)) else str(v),
                            delta=None
                        )

        with tab2:  # Gráfico de tendencia
            st.subheader("Evolución Temporal")
            
            if len(date_cols) > 0:
                date_col = st.selectbox("Selecciona columna de fecha", date_cols)
                num_col = st.selectbox("Selecciona columna numérica", numeric_cols)
                
                fig = px.line(
                    df,
                    x=date_col,
                    y=num_col,
                    title=f"Evolución de {num_col}",
                    labels={num_col: "Valor ($)", date_col: "Fecha"}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No se encontraron columnas de fecha para análisis temporal")

        with tab3:  # Distribución
            st.subheader("Distribución de Valores")
            
            if len(numeric_cols) > 0:
                col = st.selectbox("Columna para histograma", numeric_cols)
                bins = st.slider("Número de bins", 5, 100, 20)
                
                fig = px.histogram(
                    df,
                    x=col,
                    nbins=bins,
                    title=f"Distribución de {col}",
                    labels={col: "Valor ($)"}
                )
                st.plotly_chart(fig, use_container_width=True)

        with tab4:  # Correlaciones
            st.subheader("Matriz de Correlación")
            
            if len(numeric_cols) >= 2:
                selected_cols = st.multiselect(
                    "Selecciona columnas para correlación",
                    numeric_cols,
                    default=numeric_cols[:3]
                )
                
                if len(selected_cols) >= 2:
                    corr_matrix = df[selected_cols].corr()
                    fig = px.imshow(
                        corr_matrix,
                        text_auto=True,
                        title="Correlación entre Variables",
                        color_continuous_scale='RdBu',
                        zmin=-1,
                        zmax=1
                    )
                    st.plotly_chart(fig, use_container_width=True)

        # =================================================================
        # 🚀 SECCIÓN 2: PROYECCIONES FINANCIERAS
        # =================================================================
        st.header("🚀 Proyección Financiera a 3 Años")
        
        # Configuración de parámetros
        col1, col2, col3 = st.columns(3)
        
        with col1:
            tasa_anual = st.slider(
                "Tasa de crecimiento anual (%)",
                min_value=0.0,
                max_value=50.0,
                value=10.0,
                step=0.5,
                key="tasa_proyeccion"
            )
        
        with col2:
            capital_inicial = st.number_input(
                "Capital inicial ($)",
                min_value=0.0,
                value=float(df[numeric_cols[0]].iloc[-1]) if len(numeric_cols) > 0 else 10000.0,
                step=1000.0,
                key="capital_inicial"
            )
        
        with col3:
            aumento_anual = st.number_input(
                "Aumento capital anual ($)",
                min_value=0.0,
                value=5000.0,
                step=1000.0,
                key="aumento_anual"
            )

        # Función de proyección mejorada
        def calcular_proyeccion(inicial, tasa, periodos, aumento=0):
            tasa_mensual = tasa / 100 / 12
            fechas = []
            capital = []
            ganancias = []
            aumentos = []
            
            actual = inicial
            for mes in range(periodos + 1):
                fecha = datetime.now() + timedelta(days=30*mes)
                fechas.append(fecha)
                
                # Calcular ganancias
                ganancia = actual * tasa_mensual
                
                # Aplicar aumento anual
                inyeccion = aumento if mes % 12 == 0 and mes != 0 else 0
                
                # Acumular
                actual += ganancia + inyeccion
                
                # Guardar valores
                capital.append(actual)
                ganancias.append(ganancia)
                aumentos.append(inyeccion)
            
            return pd.DataFrame({
                'Fecha': fechas,
                'Capital': capital,
                'Ganancias': ganancias,
                'Aumento': aumentos,
                'Escenario': 'Base' if aumento == 0 else f'Con +${aumento:,.0f}/año'
            })

        # Calcular proyecciones
        meses = 36  # 3 años
        base = calcular_proyeccion(capital_inicial, tasa_anual, meses)
        con_aumento = calcular_proyeccion(capital_inicial, tasa_anual, meses, aumento_anual)
        
        # Combinar resultados
        proyecciones = pd.concat([base, con_aumento])

        # Mostrar resultados
        st.subheader("Comparativa de Proyecciones")
        
        col4, col5 = st.columns(2)
        
        with col4:
            fig = px.line(
                proyecciones,
                x='Fecha',
                y='Capital',
                color='Escenario',
                title='Capital Acumulado Proyectado',
                labels={'Capital': 'Valor ($)'},
                hover_data=['Ganancias', 'Aumento']
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col5:
            fig2 = px.bar(
                proyecciones[proyecciones['Fecha'] == proyecciones['Fecha'].max()],
                x='Escenario',
                y='Capital',
                title='Valor Final (36 meses)',
                labels={'Capital': 'Valor ($)'},
                color='Escenario'
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Resumen comparativo
        st.subheader("📌 Resumen Comparativo")
        
        final_values = proyecciones[proyecciones['Fecha'] == proyecciones['Fecha'].max()].copy()
        final_values['Diferencia'] = final_values['Capital'] - final_values['Capital'].shift(1)
        
        st.dataframe(
            final_values.style.format({
                'Fecha': lambda x: x.strftime('%Y-%m-%d'),
                'Capital': '${:,.2f}',
                'Ganancias': '${:,.2f}',
                'Aumento': '${:,.2f}',
                'Diferencia': '${:,.2f}'
            }),
            column_order=['Escenario', 'Capital', 'Ganancias', 'Aumento', 'Diferencia'],
            hide_index=True
        )

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.error("Por favor verifica que el archivo tenga el formato correcto.")
else:
    st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")












