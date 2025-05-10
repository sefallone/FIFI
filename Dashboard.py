import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import seaborn as sns
from io import BytesIO

st.set_page_config(page_title="Dashboard Financiero", layout="wide")

# Función para exportar figuras
def exportar_figura(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    return buf

# Aquí comenzará la nueva lógica después de cargar el archivo Excel

archivo_excel = st.file_uploader("📁 Sube tu archivo CSV", type=["csv"])
if archivo_excel:
    df = pd.read_csv(archivo_excel, encoding="utf-8", sep=";")
    df.columns = df.columns.str.strip()
    st.subheader("📄 Vista previa de los datos cargados")
    st.dataframe(df.head(50))

    # KPIs básicos
    st.subheader("📌 Indicadores clave")
    try:
        df["Ganancias Netas"] = (
            df["Ganancias Netas"]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )

        df["Capital Invertido"] = (
            df["Capital Invertido"]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
            .astype(float)
        )
        total_invertido = df["Capital Invertido"].iloc[-1]  # Ya viene acumulado
        total_ganancias = df["Ganancias Netas"].sum()
        roi = (total_ganancias / total_invertido * 100) if total_invertido > 0 else 0

        # Rellenar NaN con ceros tras la conversión
        df["Capital Invertido"].fillna(0, inplace=True)
        df["Ganancias Netas"].fillna(0, inplace=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Invertido", f"{total_invertido:,.2f} €")
        col2.metric("📈 Ganancias Netas", f"{total_ganancias:,.2f} €")  # corregido
        col3.metric("📊 ROI", f"{roi:.2f} %")
    except Exception as e:
        st.warning(f"No se pudieron calcular los KPIs automáticamente: {e}")

    # Visualización: evolución de capital en el tiempo
    st.subheader("📈 Evolución del Capital Invertido")
    try:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df = df.dropna(subset=["Fecha"])
        df.sort_values("Fecha", inplace=True)

        df_agg = df.groupby("Fecha")["Capital Invertido"].sum().reset_index()
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        ax1.plot(df_agg["Fecha"], df_agg["Capital Invertido"], marker="o")
        ax1.set_title("Capital Invertido en el Tiempo")
        ax1.set_xlabel("Fecha")
        ax1.set_ylabel("€")
        st.pyplot(fig1)
    except Exception as e:
        st.warning(f"No se pudo generar la gráfica de capital invertido: {e}")

    # Visualización: ganancias netas en el tiempo
    st.subheader("💹 Ganancias Netas por Fecha")
    try:
        df_gan = df.groupby("Fecha")["Ganancias Netas"].sum().reset_index()
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ax2.bar(df_gan["Fecha"], df_gan["Ganancias Netas"], color="green")
        ax2.set_title("Ganancias Netas por Fecha")
        ax2.set_xlabel("Fecha")
        ax2.set_ylabel("€")
        st.pyplot(fig2)
    except Exception as e:
        st.warning(f"No se pudo generar la gráfica de ganancias netas: {e}")









