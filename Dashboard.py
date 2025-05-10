import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(page_title="Dashboard Financiero", layout="wide")

# Cargar datos desde Excel
archivo_excel = st.file_uploader("Sube tu archivo de Excel", type=["xlsx"])
if archivo_excel:
    df = pd.read_excel(archivo_excel)

    # Limpieza de columnas
    df.columns = df.columns.str.strip()
    df = df.dropna(how="all", axis=1)  # Quita columnas vacías

    # Mostrar columnas disponibles para debug
    st.write("Columnas disponibles:", df.columns.tolist())

    # Conversión de fechas
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce')
    df = df.dropna(subset=["Fecha"])
    df = df.sort_values("Fecha")

    # Conversión de números con coma
    columnas_a_convertir = ["Capital Invertido", "Aumento Capital", "Retiro de Fondos", 
                            "Ganancias/Pérdidas Brutas", "Comisiones 10 %", "Ganancias Netas"]

    for col in columnas_a_convertir:
        if col in df.columns:
            df[col] = (df[col].astype(str)
                            .str.replace(".", "", regex=False)
                            .str.replace(",", ".", regex=False)
                            .astype(float))

    # Capital acumulado en el tiempo
    if all(c in df.columns for c in ["Capital Invertido", "Aumento Capital", "Retiro de Fondos"]):
        df["Capital Total"] = df["Capital Invertido"] + df["Aumento Capital"] - df["Retiro de Fondos"].fillna(0)
        df["Capital Acumulado"] = df.groupby("Nombre Inversionista")["Capital Total"].cumsum()

    st.title("📈 Dashboard Financiero Interactivo")

    # Filtros
    inversionistas = df["Nombre Inversionista"].unique()
    inversionista_seleccionado = st.selectbox("Selecciona un inversionista", options=["Todos"] + list(inversionistas))

    if inversionista_seleccionado != "Todos":
        df_filtrado = df[df["Nombre Inversionista"] == inversionista_seleccionado]
    else:
        df_filtrado = df

    # Visualización 1: Evolución del capital
    st.subheader("📊 Evolución del capital en el tiempo")
    fig1, ax1 = plt.subplots()
    if "Capital Acumulado" in df_filtrado.columns:
        df_plot = df_filtrado.groupby("Fecha")["Capital Acumulado"].sum().reset_index()
        ax1.plot(df_plot["Fecha"], df_plot["Capital Acumulado"], marker='o')
        ax1.set_title("Capital acumulado en el tiempo")
        ax1.set_xlabel("Fecha")
        ax1.set_ylabel("Capital acumulado")
        st.pyplot(fig1)

    # Visualización 2: Ganancias netas por mes
    st.subheader("📈 Ganancias netas por período")
    if "Ganancias Netas" in df_filtrado.columns:
        df_plot2 = df_filtrado.groupby("Fecha")["Ganancias Netas"].sum().reset_index()
        fig2, ax2 = plt.subplots()
        ax2.bar(df_plot2["Fecha"], df_plot2["Ganancias Netas"])
        ax2.set_title("Ganancias netas por fecha")
        st.pyplot(fig2)

    # Visualización 3: Proyecciones con interés compuesto
    st.subheader("🧮 Proyección de interés compuesto")
    if "Capital Acumulado" in df_filtrado.columns:
        capital_inicial = df_filtrado["Capital Acumulado"].iloc[-1]
        tasa = st.slider("Tasa de interés anual (%)", min_value=0.0, max_value=100.0, value=10.0) / 100
        anios = st.slider("Número de años", min_value=1, max_value=10, value=5)

        fechas = pd.date_range(start=datetime.today(), periods=anios + 1, freq='Y')
        proyeccion = [capital_inicial * ((1 + tasa) ** n) for n in range(anios + 1)]

        fig3, ax3 = plt.subplots()
        ax3.plot(fechas, proyeccion, marker='o')
        ax3.set_title("Proyección de capital con interés compuesto")
        st.pyplot(fig3)

else:
    st.info("Por favor, sube un archivo Excel con tus datos financieros.")
