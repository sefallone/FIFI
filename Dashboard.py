
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# ====================
# Configuración Inicial
# ====================
st.set_page_config(page_title="Dashboard Fallone Investments", layout="wide", initial_sidebar_state="expanded")

# ====================
# Función segura para KPI
# ====================
def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False):
    try:
        if pd.isna(value):
            value_display = "N/D"
        elif is_currency:
            value_display = f"${value:,.2f}"
        elif is_percentage:
            value_display = f"{value:.2f}%"
        else:
            value_display = f"{value:.2f}"
    except:
        value_display = "N/D"
    st.markdown(f'''
        <div style="background-color:#1810ca; color:white; padding:12px;
                    border-radius:8px; margin-bottom:10px; box-shadow:0 2px 4px rgba(0,0,0,0.3);">
            <div style="font-weight:bold; font-size:14px;">{icon} {title}</div>
            <div style="font-size:24px; font-weight:bold;">{value_display}</div>
        </div>
    ''', unsafe_allow_html=True)

# ====================
# Cálculos Financieros
# ====================
def calculate_roi(df, capital_inicial):
    try:
        if capital_inicial > 0 and 'Ganancias/Pérdidas Netas' in df.columns:
            return (df['Ganancias/Pérdidas Netas'].sum() / capital_inicial) * 100
    except:
        pass
    return 0

def calculate_cagr(df, capital_inicial, current_capital):
    try:
        if capital_inicial > 0 and len(df) > 1:
            start = df['Fecha'].iloc[0]
            end = df['Fecha'].iloc[-1]
            months = (end.year - start.year) * 12 + (end.month - start.month)
            if months > 0:
                return ((current_capital / capital_inicial) ** (12 / months) - 1) * 100
    except:
        pass
    return 0

def calculate_max_drawdown(df):
    try:
        if 'Capital Invertido' in df.columns:
            df['Max'] = df['Capital Invertido'].cummax()
            df['Drawdown'] = (df['Capital Invertido'] - df['Max']) / df['Max']
            return df['Drawdown'].min() * 100
    except:
        pass
    return 0

# ====================
# Cargar Datos con Cache
# ====================
@st.cache_data
def load_excel(file):
    try:
        return pd.read_excel(file)
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return pd.DataFrame()

# ====================
# Visualizaciones
# ====================
def plot_line(df, x_col, y_col, title, y_label):
    try:
        fig = px.line(df, x=x_col, y=y_col, title=title, labels={y_col: y_label, x_col: "Fecha"}, template="plotly_dark")
        fig.update_layout(hovermode="x unified", height=400)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Error al mostrar gráfico: {e}")

def plot_bar(df, x_col, y_col, title, y_label):
    try:
        fig = px.bar(df, x=x_col, y=y_col, title=title, labels={y_col: y_label, x_col: "Fecha"}, template="plotly_dark",
                     color=y_col, color_continuous_scale=px.colors.sequential.Teal)
        fig.update_layout(hovermode="x unified", height=400)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Error al mostrar gráfico: {e}")

# ====================
# Interfaz Principal
# ====================
def main():
    st.title("📊 Dashboard Fallone Investments")
    uploaded_file = st.file_uploader("📥 Cargar archivo Excel", type=["xlsx"])

    if uploaded_file:
        df = load_excel(uploaded_file)
        if df.empty:
            return

        df.columns = df.columns.str.strip()
        df.rename(columns={
            'Ganacias/Pérdidas Brutas': 'Ganancias/Pérdidas Brutas',
            'Ganacias/Pérdidas Netas': 'Ganancias/Pérdidas Netas',
            'Comisiones 10 %': 'Comisiones Pagadas'
        }, inplace=True)

        if 'Fecha' not in df.columns:
            st.error("❌ La columna 'Fecha' es requerida.")
            return

        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df.dropna(subset=['Fecha'], inplace=True)

        capital_inicial = float(df['Aumento Capital'].dropna().values[0]) if 'Aumento Capital' in df.columns and not df['Aumento Capital'].dropna().empty else 0.0
        current_capital = df['Capital Invertido'].iloc[-1] if 'Capital Invertido' in df.columns else 0.0
        roi = calculate_roi(df, capital_inicial)
        cagr = calculate_cagr(df, capital_inicial, current_capital)
        drawdown = calculate_max_drawdown(df)

        # KPIs
        st.subheader("📌 Indicadores Clave")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            display_kpi("Capital Inicial", capital_inicial)
        with col2:
            display_kpi("Capital Actual", current_capital)
        with col3:
            display_kpi("ROI", roi, is_currency=False, is_percentage=True)
        with col4:
            display_kpi("CAGR Mensual", cagr, is_currency=False, is_percentage=True)

        col5, col6, col7, _ = st.columns(4)
        with col5:
            display_kpi("Drawdown Máximo", drawdown, is_currency=False, is_percentage=True)
        with col6:
            display_kpi("Ganancias Netas", df.get('Ganancias/Pérdidas Netas', pd.Series(dtype=float)).sum())
        with col7:
            display_kpi("Comisiones Pagadas", df.get('Comisiones Pagadas', pd.Series(dtype=float)).iloc[-1] if not df.get('Comisiones Pagadas', pd.Series(dtype=float)).empty else 0)

        # Visualizaciones
        st.subheader("📈 Evolución del Capital")
        if 'Capital Invertido' in df.columns:
            plot_line(df, 'Fecha', 'Capital Invertido', "Evolución del Capital Invertido", "Capital ($)")

        st.subheader("💰 Ganancias Brutas")
        if 'Ganancias/Pérdidas Brutas' in df.columns:
            plot_bar(df, 'Fecha', 'Ganancias/Pérdidas Brutas', "Ganancias/Pérdidas Brutas", "Ganancias ($)")

        st.subheader("💸 Comisiones Pagadas")
        if 'Comisiones Pagadas' in df.columns:
            plot_line(df, 'Fecha', 'Comisiones Pagadas', "Comisiones Pagadas (No Acumuladas)", "Comisiones ($)")

if __name__ == "__main__":
    main()

