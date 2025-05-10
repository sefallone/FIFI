import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Excel", layout="wide")

# Título del dashboard
st.title("Dashboard Interactivo desde Excel")

# Cargar el archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    # Leer el archivo Excel
    try:
        df = pd.read_excel(uploaded_file)
        
        # Mostrar los datos crudos
        if st.checkbox("Mostrar datos crudos"):
            st.subheader("Datos crudos")
            st.write(df)
        
        # Selección de columnas para análisis
        st.subheader("Análisis de datos")
        columns = df.columns.tolist()
        selected_columns = st.multiselect("Selecciona columnas para analizar", columns, default=columns[:2])
        
        if len(selected_columns) > 0:
            # Mostrar estadísticas básicas
            st.write("Estadísticas descriptivas:")
            st.write(df[selected_columns].describe())
            
            # Gráfico interactivo
            chart_type = st.selectbox("Selecciona el tipo de gráfico", 
                                    ["Línea", "Barras", "Dispersión", "Histograma"])
            
            if chart_type == "Línea":
                fig = px.line(df, x=selected_columns[0], y=selected_columns[1:])
            elif chart_type == "Barras":
                fig = px.bar(df, x=selected_columns[0], y=selected_columns[1:])
            elif chart_type == "Dispersión":
                if len(selected_columns) >= 2:
                    fig = px.scatter(df, x=selected_columns[0], y=selected_columns[1])
                else:
                    st.warning("Se necesitan al menos 2 columnas para gráfico de dispersión")
            elif chart_type == "Histograma":
                fig = px.histogram(df, x=selected_columns[0])
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Filtros interactivos
            st.subheader("Filtrar datos")
            for col in selected_columns:
                if df[col].dtype in ['float64', 'int64']:
                    min_val = float(df[col].min())
                    max_val = float(df[col].max())
                    selected_range = st.slider(f"Rango para {col}", min_val, max_val, (min_val, max_val))
                    df = df[(df[col] >= selected_range[0]) & (df[col] <= selected_range[1])]
                
            st.write("Datos filtrados:", df[selected_columns])
    
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
else:
    st.info("Por favor, sube un archivo Excel para comenzar.")














