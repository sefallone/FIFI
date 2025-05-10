import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Financiero FIFI",
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
    .header-style {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.title("📊 Dashboard Financiero FALLONE INVESTMENT")

# Cargar archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # Leer archivo Excel
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("Selecciona la hoja a analizar", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

        # Verificar columnas requeridas
        required_columns = ['Capital Invertido', 'Aumento Capital', 'Ganacias/Pérdidas Brutas', 
                          'Comisiones Pagadas', 'Ganacias/Pérdidas Netas', 'Beneficio en %']
        
        # Mostrar advertencia si faltan columnas
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.warning(f"⚠️ Faltan columnas: {', '.join(missing_cols)}. Algunos KPIs no se podrán calcular.")

        # =================================================================
        # SECCIÓN 1: KPIs ESPECÍFICOS SOLICITADOS
        # =================================================================
        st.header("📌 KPIs Financieros", anchor="kpis")

        # Fila 1 de KPIs
        col1, col2, col3, col4 = st.columns(4)
        
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
                capital_inicial = df['Aumento Capital'].iloc[0]
                st.markdown(f'<div class="kpi-value">${capital_inicial:,.2f}</div>', unsafe_allow_html=True)
            elif 'Aumento Capital' in df.columns and len(df) > 0:
                capital_inicial = df['Aumento Capital'].iloc[0]
                st.markdown(f'<div class="kpi-value">${capital_inicial:,.2f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col4:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Total Ganancias/Pérdidas Brutas</div>', unsafe_allow_html=True)
            if 'Ganancias/Pérdidas Brutas' in df.columns:
                total_bruto = df['Ganacias/Pérdidas Brutas'].sum()
                color_class = "positive" if total_bruto >= 0 else "negative"
                st.markdown(f'<div class="kpi-value {color_class}">${total_bruto:,.2f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Fila 2 de KPIs
        col5, col6, col7, col8 = st.columns(4)
        
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
                total_neto = df['Ganacias/Pérdidas Netas'].sum()
                color_class = "positive" if total_neto >= 0 else "negative"
                st.markdown(f'<div class="kpi-value {color_class}">${total_neto:,.2f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col7:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Promedio Beneficio %</div>', unsafe_allow_html=True)
            if 'Beneficio %' in df.columns:
                avg_beneficio = df['Beneficio en %'].mean()
                color_class = "positive" if avg_beneficio >= 0 else "negative"
                st.markdown(f'<div class="kpi-value {color_class}">{avg_beneficio:.2f}%</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col8:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">ROI (Retorno sobre Inversión)</div>', unsafe_allow_html=True)
            if 'Capital Invertido' in df.columns and 'Ganancias/Pérdidas Netas' in df.columns and len(df) > 0:
                roi = (df['Ganancias/Pérdidas Netas'].sum() / df['Capital Invertido'].iloc[0]) * 100
                color_class = "positive" if roi >= 0 else "negative"
                st.markdown(f'<div class="kpi-value {color_class}">{roi:.2f}%</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Fila 3 de KPIs (adicionales)
        col9, col10, col11, col12 = st.columns(4)
        
        with col9:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Promedio Mensual Ganancias</div>', unsafe_allow_html=True)
            if 'Ganancias/Pérdidas Brutas' in df.columns and len(df) > 0:
                avg_mensual = df['Ganancias/Pérdidas Brutas'].mean()
                color_class = "positive" if avg_mensual >= 0 else "negative"
                st.markdown(f'<div class="kpi-value {color_class}">${avg_mensual:,.2f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col10:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Meses con Ganancias</div>', unsafe_allow_html=True)
            if 'Ganancias/Pérdidas Brutas' in df.columns:
                meses_positivos = (df['Ganancias/Pérdidas Brutas'] >= 0).sum()
                total_meses = len(df)
                st.markdown(f'<div class="kpi-value">{meses_positivos}/{total_meses}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col11:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Ratio Comisiones/Ganancias</div>', unsafe_allow_html=True)
            if 'Comisiones Pagadas' in df.columns and 'Ganancias/Pérdidas Brutas' in df.columns and df['Ganancias/Pérdidas Brutas'].sum() != 0:
                ratio = df['Comisiones Pagadas'].sum() / abs(df['Ganancias/Pérdidas Brutas'].sum()) * 100
                st.markdown(f'<div class="kpi-value">{ratio:.2f}%</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col12:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Crecimiento Capital</div>', unsafe_allow_html=True)
            if 'Capital Invertido' in df.columns and len(df) > 1:
                crecimiento = (df['Capital Invertido'].iloc[-1] - df['Capital Invertido'].iloc[0]) / df['Capital Invertido'].iloc[0] * 100
                color_class = "positive" if crecimiento >= 0 else "negative"
                st.markdown(f'<div class="kpi-value {color_class}">{crecimiento:.2f}%</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # =================================================================
        # SECCIÓN 2: GRÁFICOS CORREGIDOS
        # =================================================================
        st.header("📈 Visualización de Datos")
        
        # Gráfico de Aumento de Capital vs Fecha (corregido)
        if 'Fecha' in df.columns and 'Aumento Capital' in df.columns:
            st.subheader("Evolución del Aumento de Capital")
            
            # Convertir fecha si es necesario
            if not pd.api.types.is_datetime64_any_dtype(df['Fecha']):
                df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
            
            # Filtrar fechas válidas
            df_fechas_validas = df.dropna(subset=['Fecha'])
            
            if not df_fechas_validas.empty:
                fig = px.bar(
                    df_fechas_validas,
                    x='Fecha',
                    y='Aumento Capital',
                    title='Aumento de Capital por Período',
                    labels={'Aumento Capital': 'Monto ($)', 'Fecha': 'Período'},
                    color='Aumento Capital',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No hay fechas válidas para graficar")
        else:
            st.warning("No se encontraron columnas de Fecha y/o Aumento Capital para graficar")

        # Gráfico de composición de ganancias
        if 'Ganancias/Pérdidas Brutas' in df.columns and 'Comisiones Pagadas' in df.columns:
            st.subheader("Composición de Ganancias Netas")
            
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

        # =================================================================
        # SECCIÓN 3: PROYECCIONES (se mantiene similar al anterior)
        # =================================================================
        st.header("🚀 Proyecciones Financieras")
        
        # ... (Código de proyecciones anterior)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
else:
    st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")











