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

def calculate_max_drawdown(df
