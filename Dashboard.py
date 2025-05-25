import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Dashboard Fallone Investments", layout="wide", initial_sidebar_state="expanded")

# =====================
# FUNCIÓN DE KPIs
# =====================
def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False):
    if pd.isna(value) or value is None:
        value_display = "N/D"
    else:
        if is_currency:
            value_display = f"${float(value):,.2f}"
        elif is_percentage:
            value_display = f"{float(value):.2f}%"
        else:
            value_display = f"{value:.2f}"

    st.markdown(f"""
    <div style="background-color:#1810ca; color:white; padding:12px;
                border-radius:8px; margin-bottom:10px; box-shadow:0 2px 4px rgba(0,0,0,0.3);">
        <div style="font-weight:bold; font-size:14px;">{icon} {title}</div>
        <div style="font-size:24px; font-weight:bold;">{value_display}</div>
    </div>
    """, unsafe_allow_html=True)

# =====================
# CÁLCULOS FINANCIEROS
# =====================
def calculate_roi(df, capital_inicial):
    if 'Ganancias/Pérdidas Netas' in df.columns and capital_inicial > 0:
        return (df['Ganancias/Pérdidas Netas'].sum() / capital_inicial) * 100
    return 0

def calculate_cagr(df, capital_inicial, current_capital):
    if len(df) > 1 and capital_inicial > 0:
        start = df['Fecha'].iloc[0]
        end = df['Fecha'].iloc[-1]
        months = (end.year - start.year) * 12 + (end.month - start.month)
        if months > 0:
            return ((current_capital / capital_inicial) ** (12 / months) - 1) * 100
    return 0

def calculate_max_drawdown(df):
    if 'Capital Invertido' in df.columns:
        df['Max'] = df['Capital Invertido'].cummax()
        df['Drawdown'] = (df['Capital Invertido'] - df['Max']) / df['Max']
        return df['Drawdown'].min() * 100
    return 0

# =====================
# INTERFAZ PRINCIPAL
# =====================
st.title("📊 Dashboard Fallone Investments")

uploaded_file = st.file_uploader("📥 Cargar archivo Excel", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        df = df.loc[:, ~df.columns.duplicated()]
        df.rename(columns={
            'Ganacias/Pérdidas Brutas': 'Ganancias/Pérdidas Brutas',
            'Ganacias/Pérdidas Netas': 'Ganancias/Pérdidas Netas',
            'Comisiones 10 %': 'Comisiones Pagadas'
        }, inplace=True)

        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')

        capitales = df['Aumento Capital'].dropna()
        capital_inicial = float(capitales.iloc[0]) if not capitales.empty else 0.0
        current_capital = df['Capital Invertido'].iloc[-1] if 'Capital Invertido' in df.columns else 0.0

        roi = calculate_roi(df, capital_inicial)
        cagr = calculate_cagr(df, capital_inicial, current_capital)
        drawdown = calculate_max_drawdown(df)

        ganancias_brutas = df['Ganancias/Pérdidas Brutas'].sum() if 'Ganancias/Pérdidas Brutas' in df.columns else 0.0
        ganancias_netas = df['Ganancias/Pérdidas Netas'].sum() if 'Ganancias/Pérdidas Netas' in df.columns else 0.0
        comisiones = df['Comisiones Pagadas'].iloc[-1] if 'Comisiones Pagadas' in df.columns else 0.0
        retiros = df['Retiro de Fondos'].sum() if 'Retiro de Fondos' in df.columns else 0.0

        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            display_kpi("Capital Inicial", capital_inicial)
        with col2:
            display_kpi("Capital Actual", current_capital)
        with col3:
            display_kpi("Ganancias Brutas", ganancias_brutas)
        with col4:
            display_kpi("Ganancias Netas", ganancias_netas)

        col5, col6, col7, col8 = st.columns(4)
        with col5:
            display_kpi("Comisiones Pagadas", comisiones)
        with col6:
            display_kpi("Retiros", retiros)
        with col7:
            display_kpi("ROI", roi, is_currency=False, is_percentage=True)
        with col8:
            display_kpi("CAGR Mensual", cagr, is_currency=False, is_percentage=True)

        col9, _, _, _ = st.columns(4)
        with col9:
            display_kpi("Drawdown Máximo", drawdown, is_currency=False, is_percentage=True)

        # =====================
        # GRÁFICOS
        # =====================
        st.markdown("---")
        st.subheader("📈 Evolución del Capital Invertido")
        fig1 = px.line(df, x='Fecha', y='Capital Invertido')
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader("💰 Ganancias Brutas")
        fig2 = px.bar(df, x='Fecha', y='Ganancias/Pérdidas Brutas')
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("↘️ Retiros")
        fig3 = px.bar(df, x='Fecha', y='Retiro de Fondos')
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("💸 Comisiones Pagadas")
        fig4 = px.area(
            df,
            x='Fecha',
            y='Comisiones Pagadas',
            title='Comisiones Pagadas Acumuladas',
            labels={'Comisiones Pagadas': 'Monto ($)', 'Fecha': 'Fecha'},
            template="plotly_dark"
        )
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
else:
    st.info("📂 Sube un archivo Excel para comenzar.")
