import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard Financiero Básico", layout="wide")

st.title("📊 Dashboard Financiero")

# Cargar archivo
archivo = st.file_uploader("📁 Sube tu archivo Excel", type="xlsx")
if archivo:
    df = pd.read_excel(archivo)
    df.columns = df.columns.str.strip()
    st.write("🔎 Columnas detectadas:", df.columns.tolist())

    # Conversión de datos
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    columnas_numericas = ["Capital Invertido", "Aumento Capital", "Retiro de Fondos", "Ganacias Netas"]
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)

    df = df.dropna(subset=["Fecha"])
    df.sort_values("Fecha", inplace=True)

    # Capital acumulado
    if all(c in df.columns for c in ["Capital Invertido", "Aumento Capital", "Retiro de Fondos"]):
        df["Capital Total"] = df["Capital Invertido"] + df["Aumento Capital"] - df["Retiro de Fondos"].fillna(0)
        df["Capital Acumulado"] = df.groupby("Nombre Inversionista")["Capital Total"].cumsum()

    # KPIs
    st.subheader("📌 Indicadores clave")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Invertido", f"{df['Capital Invertido'].sum():,.2f} €")
    col2.metric("📈 Ganancias", f"{df['Ganacias Netas'].sum():,.2f} €")
    col3.metric("🏦 Capital actual", f"{df['Capital Acumulado'].iloc[-1]:,.2f} €")
    roi = df["Ganacias Netas"].sum() / df["Capital Invertido"].sum() * 100
    col4.metric("📊 ROI", f"{roi:.2f} %")

    # Evolución del capital
    st.subheader("📈 Evolución del capital en el tiempo")
    df_plot = df.groupby("Fecha")["Capital Acumulado"].sum().reset_index()
    fig, ax = plt.subplots()
    ax.plot(df_plot["Fecha"], df_plot["Capital Acumulado"], marker="o")
    ax.set_title("Capital acumulado")
    ax.set_xlabel("Fecha"_



