import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Financiero - Columnas Únicas",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Función para limpiar nombres de columnas duplicadas
def clean_duplicate_columns(df):
    """Renombra columnas duplicadas para hacerlas únicas"""
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique():
        cols[cols[cols == dup].index.values.tolist()] = [
            f"{dup}_{i}" if i != 0 else dup 
            for i in range(sum(cols == dup))
        ]
    df.columns = cols
    return df

# Función segura para formatear DataFrames
def safe_format_dataframe(df):
    """Formatea un DataFrame evitando errores con tipos de datos no numéricos"""
    formatted_df = df.copy()
    
    for col in formatted_df.columns:
        # Solo formatear columnas numéricas
        if pd.api.types.is_numeric_dtype(formatted_df[col]):
            try:
                # Formatear como moneda si el valor es grande
                if abs(formatted_df[col].max()) > 1000 or abs(formatted_df[col].min()) > 1000:
                    formatted_df[col] = formatted_df[col].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "")
                # Formatear como porcentaje si el nombre de columna contiene %
                elif '%' in col:
                    formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "")
                # Formatear números decimales normales
                else:
                    formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "")
            except:
                # Si falla el formateo, mantener el valor original
                pass
    
    return formatted_df

# Título principal
st.title("📊 Dashboard Financiero - Versión Estable")

# Cargar archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # Leer archivo Excel
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("Selecciona la hoja a analizar", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
        
        # Limpiar columnas duplicadas
        df = clean_duplicate_columns(df)
        
        # Mostrar advertencia si hubo columnas duplicadas
        if len(df.columns) != len(set(df.columns)):
            st.warning("⚠️ Se detectaron y corrigieron columnas con nombres duplicados")

        # Renombrar columnas según los nombres correctos
        column_mapping = {
            'Ganacias/Pérdidas Brutas': 'Ganancias/Pérdidas Brutas',
            'Ganacias/Pérdidas Brutas_1': 'Ganancias/Pérdidas Brutas Acumuladas',
            'Ganacias/Pérdidas Netas': 'Ganancias/Pérdidas Netas',
            'Ganacias/Pérdidas Netas_1': 'Ganancias/Pérdidas Netas Acumuladas',
            'Beneficio en %': 'Beneficio %',
            'Comisiones 10 %': 'Comisiones Pagadas',
            'Comisiones Pagadas_1': 'Comisiones Pagadas Acumuladas'
        }
        
        # Aplicar solo los mapeos que existen en el DataFrame
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

        # Verificar columnas críticas
        required_columns = ['Fecha', 'Capital Invertido', 'Aumento Capital']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            st.error(f"Error: Faltan columnas críticas: {', '.join(missing_cols)}")
            st.stop()

        # =================================================================
        # SECCIÓN 1: KPIs CON DATOS LIMPIOS
        # =================================================================
        st.header("📌 KPIs Financieros")

        # Función para mostrar KPIs de manera segura
        def display_kpi(title, value, is_currency=True, is_percentage=False):
            try:
                if pd.isna(value):
                    return "N/D"
                
                if is_currency:
                    return f"${value:,.2f}"
                elif is_percentage:
                    return f"{value:.2f}%"
                return str(value)
            except:
                return str(value)

        # Fila 1 de KPIs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Capital Invertido (Acumulado)", 
                     display_kpi("Capital", df['Capital Invertido'].iloc[-1]))
        
        with col2:
            st.metric("Suma Aumento Capital", 
                     display_kpi("Aumento", df['Aumento Capital'].sum()))
        
        with col3:
            st.metric("Capital Inicial", 
                     display_kpi("Inicial", df['Capital Invertido'].iloc[0]))

        # Fila 2 de KPIs
        col4, col5, col6 = st.columns(3)
        
        with col4:
            bruto = df['Ganancias/Pérdidas Brutas'].sum() if 'Ganancias/Pérdidas Brutas' in df.columns else None
            st.metric("Total Ganancias/Pérdidas Brutas", 
                     display_kpi("Bruto", bruto),
                     delta_color="inverse" if bruto and bruto < 0 else "normal")
        
        with col5:
            comisiones = df['Comisiones Pagadas'].sum() if 'Comisiones Pagadas' in df.columns else None
            st.metric("Total Comisiones Pagadas", 
                     display_kpi("Comisiones", comisiones))
        
        with col6:
            if 'Ganancias/Pérdidas Netas' in df.columns:
                neto = df['Ganancias/Pérdidas Netas'].sum()
            elif bruto is not None and comisiones is not None:
                neto = bruto - comisiones
            else:
                neto = None
                
            st.metric("Total Ganancias/Pérdidas Netas", 
                     display_kpi("Neto", neto),
                     delta_color="inverse" if neto and neto < 0 else "normal")

        # =================================================================
        # SECCIÓN 2: GRÁFICOS CON DATOS LIMPIOS
        # =================================================================
        st.header("📈 Visualización de Datos")

        # Gráfico 1: Aumento de Capital vs Fecha
        st.subheader("Aumento de Capital por Fecha")
        
        try:
            # Preparar datos para el gráfico
            plot_data = df[['Fecha', 'Aumento Capital']].copy()
            plot_data['Fecha'] = pd.to_datetime(plot_data['Fecha'], errors='coerce')
            plot_data = plot_data.dropna()
            
            if not plot_data.empty:
                fig = px.bar(
                    plot_data,
                    x='Fecha',
                    y='Aumento Capital',
                    title='Aumento de Capital por Fecha',
                    labels={'Aumento Capital': 'Monto ($)', 'Fecha': 'Fecha'}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No hay datos válidos para mostrar")
        except Exception as e:
            st.error(f"Error al generar gráfico: {str(e)}")

        # =================================================================
        # SECCIÓN 3: TABLA DE DATOS LIMPIA
        # =================================================================
        st.header("📋 Datos Financieros")
        
        # Mostrar nombres de columnas para diagnóstico
        with st.expander("Ver estructura de columnas"):
            st.write("Columnas disponibles:", list(df.columns))
        
        # Mostrar dataframe con formateo seguro
        try:
            st.dataframe(safe_format_dataframe(df), height=400)
        except Exception as e:
            st.error(f"Error al mostrar datos: {str(e)}")
            st.dataframe(df)  # Mostrar sin formateo si falla

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        st.error("Por favor verifica que el archivo tenga el formato correcto.")
else:
    st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")








