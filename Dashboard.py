import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# ========== CONFIGURACIÓN DE LA PÁGINA ==========
st.set_page_config(page_title="Dashboard Fallone Investments", layout="wide")

# ========== CARGA Y LIMPIEZA DE DATOS ==========
@st.cache_data
def load_data(file, sheet_name):
    df = pd.read_excel(file, sheet_name=sheet_name)

    rename_dict = {
        'Ganacias/Pérdidas Brutas': 'Ganancias/Pérdidas Brutas',
        'Ganacias/Pérdidas Netas': 'Ganancias/Pérdidas Netas',
        'Comisiones 10 %': 'Comisiones Pagadas',
        'Beneficio en %': 'Beneficio %'
    }
    df = df.rename(columns={k: v for k, v in rename_dict.items() if k in df.columns})
    df = df.loc[:, ~df.columns.duplicated()]
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    return df

# ========== VALIDACIONES ==========
def validar_columnas(df, columnas_requeridas):
    faltantes = [col for col in columnas_requeridas if col not in df.columns]
    if faltantes:
        st.error(f"❌ Faltan columnas esenciales: {faltantes}")
        st.stop()

# ========== CÁLCULO DE MÉTRICAS ==========
def calcular_kpis(df):
    capital_inicial = df['Aumento Capital'].dropna().iloc[0] if not df['Aumento Capital'].dropna().empty else 0
    capital_actual = df['Capital Invertido'].iloc[-1]
    total_retiros = df['Retiro de Fondos'].sum()
    ganancias_netas = df['Ganancias/Pérdidas Netas'].sum()
    ganancias_brutas = df['Ganancias/Pérdidas Brutas'].sum()
    comisiones = df['Comisiones Pagadas'].iloc[-1]

    meses = (df['Fecha'].iloc[-1].year - df['Fecha'].iloc[0].year) * 12 + \
            (df['Fecha'].iloc[-1].month - df['Fecha'].iloc[0].month)
    cagr = ((capital_actual / capital_inicial) ** (12 / meses) - 1) * 100 if meses > 0 else 0
    roi = (ganancias_netas / capital_inicial) * 100 if capital_inicial else 0

    return {
        "Capital Inicial": capital_inicial,
        "Capital Actual": capital_actual,
        "Ganancias Netas": ganancias_netas,
        "Ganancias Brutas": ganancias_brutas,
        "Comisiones Pagadas": comisiones,
        "Retiros": total_retiros,
        "ROI (%)": roi,
        "CAGR (%)": cagr
    }

# ========== PROYECCIÓN A 3 AÑOS ==========
def generar_proyecciones(df):
    last = df.iloc[-1]
    cap_actual = last['Capital Invertido']
    gan_actual = last['Ganancias/Pérdidas Brutas']

    df['Crec Capital'] = df['Capital Invertido'].pct_change().rolling(3, min_periods=1).mean()
    df['Crec Ganancias'] = df['Ganancias/Pérdidas Brutas'].pct_change().rolling(3, min_periods=1).mean()
    g_cap = df['Crec Capital'].iloc[-6:].mean()
    g_gan = df['Crec Ganancias'].iloc[-6:].mean()

    g_cap = 0.02 if not np.isfinite(g_cap) else g_cap
    g_gan = 0.03 if not np.isfinite(g_gan) else g_gan

    future_dates = pd.date_range(start=df['Fecha'].max() + pd.DateOffset(months=1), periods=36, freq='M')
    escenarios = {
        "Conservador": (g_cap, g_gan),
        "Moderado": (g_cap * 1.25, g_gan * 1.25),
        "Óptimo": (g_cap * 1.5, g_gan * 1.5)
    }
    proyecciones = []

    for tipo, (gc, gg) in escenarios.items():
        s = pd.DataFrame({'Fecha': future_dates})
        s['Capital Invertido'] = cap_actual * (1 + gc) ** np.arange(1, 37)
        s['Ganancias/Pérdidas Brutas'] = gan_actual * (1 + gg) ** np.arange(1, 37)
        s['Escenario'] = tipo
        proyecciones.append(s)

    combinado = pd.concat([df.assign(Escenario='Histórico'), *proyecciones])
    return combinado[['Fecha', 'Capital Invertido', 'Ganancias/Pérdidas Brutas', 'Escenario']]

# ========== VISUALIZACIONES ==========
def mostrar_kpis(kpis):
    st.subheader("📌 KPIs Financieros")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Capital Inicial", f"${kpis['Capital Inicial']:,.2f}")
    col2.metric("Capital Actual", f"${kpis['Capital Actual']:,.2f}")
    col3.metric("Ganancias Netas", f"${kpis['Ganancias Netas']:,.2f}")
    col4.metric("Ganancias Brutas", f"${kpis['Ganancias Brutas']:,.2f}")

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Comisiones Pagadas", f"${kpis['Comisiones Pagadas']:,.2f}")
    col6.metric("Retiros", f"${kpis['Retiros']:,.2f}")
    col7.metric("ROI", f"{kpis['ROI (%)']:.2f}%")
    col8.metric("CAGR", f"{kpis['CAGR (%)']:.2f}%")

def graficos(df):
    st.subheader("📊 Gráficos de Rendimiento")
    st.plotly_chart(px.line(df, x='Fecha', y='Capital Invertido', title='📈 Capital Invertido'), use_container_width=True)
    st.plotly_chart(px.bar(df, x='Fecha', y='Ganancias/Pérdidas Brutas', title='💰 Ganancias Brutas'), use_container_width=True)
    st.plotly_chart(px.bar(df, x='Fecha', y='Retiro de Fondos', title='↘️ Retiros'), use_container_width=True)

def graficos_proyeccion(proj_df):
    st.subheader("🔮 Proyección a 3 años")

    fig1 = px.line(
        proj_df, x='Fecha', y='Capital Invertido', color='Escenario',
        title="Proyección de Capital Invertido", template="plotly_dark"
    )
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.line(
        proj_df, x='Fecha', y='Ganancias/Pérdidas Brutas', color='Escenario',
        title="Proyección de Ganancias Brutas", template="plotly_dark"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ========== APLICACIÓN PRINCIPAL ==========
st.title("💼 Dashboard de Inversión - Fallone Investments")

uploaded_file = st.file_uploader("📥 Carga tu archivo Excel", type=['xlsx'])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        sheet = st.selectbox("📄 Selecciona una hoja", xls.sheet_names)
        df = load_data(uploaded_file, sheet)

        columnas_requeridas = ['Fecha', 'ID Inv', 'Capital Invertido',
                               'Aumento Capital', 'Retiro de Fondos',
                               'Ganancias/Pérdidas Brutas', 'Ganancias/Pérdidas Netas',
                               'Comisiones Pagadas']
        validar_columnas(df, columnas_requeridas)

        st.success("✅ Archivo cargado correctamente.")
        st.dataframe(df.head(), use_container_width=True)

        kpis = calcular_kpis(df)
        mostrar_kpis(kpis)

        graficos(df)

        st.markdown("---")
        proj_df = generar_proyecciones(df)
        graficos_proyeccion(proj_df)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
else:
    st.info("📂 Sube un archivo Excel para comenzar.")

