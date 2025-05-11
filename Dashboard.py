import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Financiero - Nombres Corregidos",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .kpi-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 5px solid #3498db;
    }
    .kpi-title {
        font-size: 16px;
        font-weight: 600;
        color: #2c3e50;
        margin-bottom: 10px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 700;
        color: #3498db;
    }
    .positive {
        color: #2ecc71;
    }
    .negative {
        color: #e74c3c;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.title("📊 Dashboard Financiero - Versión Corregida")

# Cargar archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # Leer archivo Excel
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("Selecciona la hoja a analizar", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

        # Renombrar columnas según los nombres correctos proporcionados
        column_mapping = {
            'Ganacias/Pérdidas Brutas': 'Ganancias/Pérdidas Brutas',
            'Ganacias/Pérdidas Netas': 'Ganancias/Pérdidas Netas',
            'Beneficio en %': 'Beneficio %',
            'Comisiones 10 %': 'Comisiones Pagadas'
        }
        
        df = df.rename(columns=column_mapping)

        # Verificar columnas críticas
        required_columns = [
            'Fecha', 'Capital Invertido', 'Aumento Capital',
            'Ganancias/Pérdidas Brutas', 'Ganancias/Pérdidas Netas',
            'Comisiones Pagadas', 'Beneficio %'
        ]
        
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            st.warning(f"⚠️ Columnas faltantes: {', '.join(missing_cols)}. Algunos KPIs no se podrán calcular.")

        # Función segura para cálculos
        def safe_divide(a, b):
            return a / b if b != 0 else 0

        # =================================================================
        # SECCIÓN 1: KPIs CON NOMBRES CORREGIDOS
        # =================================================================
        st.header("📌 KPIs Financieros")

        # Fila 1 de KPIs
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Capital Invertido (Acumulado)</div>', unsafe_allow_html=True)
            if 'Capital Invertido' in df.columns:
                capital_invertido = df['Capital Invertido'].iloc[-1]
                st.markdown(f'<div class="kpi-value">${capital_invertido:,.2f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Suma Aumento Capital</div>', unsafe_allow_html=True)
            if 'Aumento Capital' in df.columns:
                suma_aumento = df['Aumento Capital'].sum()
                st.markdown(f'<div class="kpi-value">${suma_aumento:,.2f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Capital Inicial</div>', unsafe_allow_html=True)
            if 'Capital Invertido' in df.columns and len(df) > 0:
                capital_inicial = df['Capital Invertido'].iloc[0]
                st.markdown(f'<div class="kpi-value">${capital_inicial:,.2f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Fila 2 de KPIs
        col4, col5, col6 = st.columns(3)
        
        with col4:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Total Ganancias/Pérdidas Brutas</div>', unsafe_allow_html=True)
            if 'Ganancias/Pérdidas Brutas' in df.columns:
                total_bruto = df['Ganancias/Pérdidas Brutas'].sum()
                color_class = "positive" if total_bruto >= 0 else "negative"
                st.markdown(f'<div class="kpi-value {color_class}">${total_bruto:,.2f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col5:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Total Comisiones Pagadas</div>', unsafe_allow_html=True)
            if 'Comisiones Pagadas' in df.columns:
                total_comisiones = df['Comisiones Pagadas'].sum()
                st.markdown(f'<div class="kpi-value">${total_comisiones:,.2f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col6:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Total Ganancias/Pérdidas Netas</div>', unsafe_allow_html=True)
            if 'Ganancias/Pérdidas Netas' in df.columns:
                total_neto = df['Ganancias/Pérdidas Netas'].sum()
                color_class = "positive" if total_neto >= 0 else "negative"
                st.markdown(f'<div class="kpi-value {color_class}">${total_neto:,.2f}</div>', unsafe_allow_html=True)
            else:
                # Calcular si no existe la columna
                if 'Ganancias/Pérdidas Brutas' in df.columns and 'Comisiones Pagadas' in df.columns:
                    total_neto = df['Ganancias/Pérdidas Brutas'].sum() - df['Comisiones Pagadas'].sum()
                    color_class = "positive" if total_neto >= 0 else "negative"
                    st.markdown(f'<div class="kpi-value {color_class}">${total_neto:,.2f} (Calculado)</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Fila 3 de KPIs
        col7, col8, col9 = st.columns(3)
        
        with col7:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Promedio Beneficio %</div>', unsafe_allow_html=True)
            if 'Beneficio %' in df.columns:
                avg_beneficio = df['Beneficio %'].mean()
                color_class = "positive" if avg_beneficio >= 0 else "negative"
                st.markdown(f'<div class="kpi-value {color_class}">{avg_beneficio:.2f}%</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col8:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Promedio Mensual Ganancias</div>', unsafe_allow_html=True)
            if 'Ganancias/Pérdidas Brutas' in df.columns and len(df) > 0:
                avg_mensual = df['Ganancias/Pérdidas Brutas'].mean()
                color_class = "positive" if avg_mensual >= 0 else "negative"
                st.markdown(f'<div class="kpi-value {color_class}">${avg_mensual:,.2f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col9:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">ROI (Retorno sobre Inversión)</div>', unsafe_allow_html=True)
            if 'Capital Invertido' in df.columns and len(df) > 0 and 'Ganancias/Pérdidas Netas' in df.columns:
                roi = safe_divide(df['Ganancias/Pérdidas Netas'].sum(), df['Capital Invertido'].iloc[0]) * 100
                color_class = "positive" if roi >= 0 else "negative"
                st.markdown(f'<div class="kpi-value {color_class}">{roi:.2f}%</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # =================================================================
        # SECCIÓN 2: GRÁFICOS CON NOMBRES CORREGIDOS
        # =================================================================
        st.header("📈 Visualización de Datos")
        
        # Gráfico 1: Aumento de Capital vs Fecha
        if 'Fecha' in df.columns and 'Aumento Capital' in df.columns:
            st.subheader("Aumento de Capital por Fecha")
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
        else:
            st.warning("Se requieren columnas 'Fecha' y 'Aumento Capital' para este gráfico")

        # Gráfico 2: Evolución de Ganancias/Pérdidas
        if 'Fecha' in df.columns and 'Ganancias/Pérdidas Netas' in df.columns:
            st.subheader("Evolución de Ganancias/Pérdidas Netas")
            try:
                plot_data = df.dropna(subset=['Fecha', 'Ganancias/Pérdidas Netas'])
                
                if not plot_data.empty:
                    fig = px.line(
                        plot_data,
                        x='Fecha',
                        y='Ganancias/Pérdidas Netas',
                        title='Evolución de Ganancias/Pérdidas Netas',
                        labels={'Ganancias/Pérdidas Netas': 'Monto ($)', 'Fecha': 'Fecha'},
                        color_discrete_sequence=['#2ecc71']
                    )
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error al generar gráfico: {str(e)}")

        # Gráfico 3: Composición de Ganancias
        if 'Ganancias/Pérdidas Brutas' in df.columns and 'Comisiones Pagadas' in df.columns:
            st.subheader("Composición de Ganancias")
            try:
                df_composicion = pd.DataFrame({
                    'Concepto': ['Ganancias Brutas', 'Comisiones'],
                    'Monto': [
                        df['Ganancias/Pérdidas Brutas'].sum(),
                        -abs(df['Comisiones Pagadas'].sum())
                    ]
                })
                
                fig = px.bar(
                    df_composicion,
                    x='Concepto',
                    y='Monto',
                    title='Desglose de Ganancias Netas',
                    labels={'Monto': 'Valor ($)'},
                    color='Concepto',
                    text='Monto'
                )
                fig.update_traces(texttemplate='$%{y:,.2f}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error al generar gráfico: {str(e)}")

    except Exception as e:
        st.error(f"Error crítico al procesar el archivo: {str(e)}")
else:
    st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")










