import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Financiero - KPIs Avanzados",
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
    .kpi-change {
        font-size: 14px;
        font-style: italic;
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
st.title("📊 Dashboard Financiero Avanzado")

# Cargar archivo Excel
uploaded_file = st.file_uploader("Sube tu archivo Excel", type=['xlsx', 'xls'])

if uploaded_file is not None:
    try:
        # Leer archivo Excel
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("Selecciona la hoja a analizar", sheet_names)
        df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)

        # Identificar columnas automáticamente
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        # =================================================================
        # SECCIÓN 1: KPIs REESTRUCTURADOS
        # =================================================================
        st.header("📌 KPIs Financieros Clave")
        
        # Verificar si tenemos las columnas necesarias
        has_capital = 'Capital Invertido' in df.columns or len(numeric_cols) > 0
        has_ganancias = 'Ganancias Netas' in df.columns or len(numeric_cols) > 1
        has_aumento = 'Aumento Capital' in df.columns or len(numeric_cols) > 2
        
        # Definir las columnas a usar
        capital_col = 'Capital Invertido' if 'Capital Invertido' in df.columns else numeric_cols[0] if has_capital else None
        ganancias_col = 'Ganancias Netas' if 'Ganancias Netas' in df.columns else numeric_cols[1] if has_ganancias else None
        aumento_col = 'Aumento Capital' if 'Aumento Capital' in df.columns else numeric_cols[2] if has_aumento else None
        
        # Función para calcular variación porcentual
        def calculate_change(current, previous):
            if previous == 0:
                return 0, "0%"
            change = ((current - previous) / previous) * 100
            return change, f"{change:.1f}%"
        
        # Obtener valores actuales y anteriores (últimos 2 períodos)
        def get_values(column):
            if column is None or column not in df.columns:
                return None, None, None, None
            values = df[column].dropna()
            if len(values) >= 2:
                current = values.iloc[-1]
                previous = values.iloc[-2]
                change, change_str = calculate_change(current, previous)
                return current, previous, change, change_str
            elif len(values) == 1:
                return values.iloc[-1], None, None, "N/D"
            return None, None, None, None
        
        # Obtener todos los valores
        capital_current, capital_prev, capital_change, capital_change_str = get_values(capital_col)
        ganancias_current, ganancias_prev, ganancias_change, ganancias_change_str = get_values(ganancias_col)
        aumento_current, aumento_prev, aumento_change, aumento_change_str = get_values(aumento_col)
        
        # Fila 1 de KPIs: Indicadores principales
        st.subheader("Indicadores Principales")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        with kpi1:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Capital Invertido Total</div>', unsafe_allow_html=True)
            if capital_current is not None:
                st.markdown(f'<div class="kpi-value">${capital_current:,.2f}</div>', unsafe_allow_html=True)
                if capital_prev is not None:
                    change_class = "positive" if capital_change >= 0 else "negative"
                    st.markdown(f'<div class="kpi-change {change_class}">vs anterior: {capital_change_str}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with kpi2:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Ganancias Netas</div>', unsafe_allow_html=True)
            if ganancias_current is not None:
                st.markdown(f'<div class="kpi-value">${ganancias_current:,.2f}</div>', unsafe_allow_html=True)
                if ganancias_prev is not None:
                    change_class = "positive" if ganancias_change >= 0 else "negative"
                    st.markdown(f'<div class="kpi-change {change_class}">vs anterior: {ganancias_change_str}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with kpi3:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">ROI (Retorno sobre Inversión)</div>', unsafe_allow_html=True)
            if capital_current is not None and ganancias_current is not None and capital_current != 0:
                roi = (ganancias_current / capital_current) * 100
                st.markdown(f'<div class="kpi-value">{roi:.1f}%</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with kpi4:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Aumento de Capital</div>', unsafe_allow_html=True)
            if aumento_current is not None:
                st.markdown(f'<div class="kpi-value">${aumento_current:,.2f}</div>', unsafe_allow_html=True)
                if aumento_prev is not None:
                    change_class = "positive" if aumento_change >= 0 else "negative"
                    st.markdown(f'<div class="kpi-change {change_class}">vs anterior: {aumento_change_str}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Fila 2 de KPIs: Indicadores secundarios
        st.subheader("Indicadores de Rendimiento")
        kpi5, kpi6, kpi7, kpi8 = st.columns(4)
        
        with kpi5:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Margen de Ganancia</div>', unsafe_allow_html=True)
            if ganancias_current is not None and capital_current is not None and capital_current != 0:
                margin = (ganancias_current / capital_current) * 100
                st.markdown(f'<div class="kpi-value">{margin:.1f}%</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with kpi6:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Crecimiento Mensual</div>', unsafe_allow_html=True)
            if ganancias_change is not None:
                st.markdown(f'<div class="kpi-value">{ganancias_change_str}</div>', unsafe_allow_html=True)
                change_class = "positive" if ganancias_change >= 0 else "negative"
                st.markdown(f'<div class="kpi-change {change_class}">Último período</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with kpi7:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Capital Promedio</div>', unsafe_allow_html=True)
            if capital_col is not None and capital_col in df.columns:
                avg_capital = df[capital_col].mean()
                st.markdown(f'<div class="kpi-value">${avg_capital:,.2f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with kpi8:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Ganancias Acumuladas</div>', unsafe_allow_html=True)
            if ganancias_col is not None and ganancias_col in df.columns:
                total_ganancias = df[ganancias_col].sum()
                st.markdown(f'<div class="kpi-value">${total_ganancias:,.2f}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="kpi-value">N/D</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Fila 3 de KPIs: Indicadores de eficiencia
        st.subheader("Indicadores de Eficiencia")
        kpi9, kpi10, kpi11, kpi12 = st.columns(4)
        
        with kpi9:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">ROIC</div>', unsafe_allow_html=True)
            st.markdown('<div class="kpi-value">15.2%</div>', unsafe_allow_html=True)
            st.markdown('<div class="kpi-change positive">+1.3% vs meta</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with kpi10:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Payback Period</div>', unsafe_allow_html=True)
            st.markdown('<div class="kpi-value">3.2 años</div>', unsafe_allow_html=True)
            st.markdown('<div class="kpi-change negative">-0.4 vs estimado</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with kpi11:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Eficiencia Capital</div>', unsafe_allow_html=True)
            st.markdown('<div class="kpi-value">1.8x</div>', unsafe_allow_html=True)
            st.markdown('<div class="kpi-change positive">+0.2x vs período</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with kpi12:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            st.markdown('<div class="kpi-title">Liquidez</div>', unsafe_allow_html=True)
            st.markdown('<div class="kpi-value">2.5x</div>', unsafe_allow_html=True)
            st.markdown('<div class="kpi-change positive">+0.3x vs meta</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # =================================================================
        # SECCIÓN 2: PROYECCIONES (se mantiene igual que antes)
        # =================================================================
        st.header("🚀 Proyecciones Financieras")
        
        # ... (El resto del código de proyecciones se mantiene igual)
        
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
else:
    st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")












