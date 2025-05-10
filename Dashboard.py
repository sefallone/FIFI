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

archivo_excel = st.file_uploader("📁 Sube tu archivo Excel", type=["xlsx"])
if archivo_excel:
    df = pd.read_excel(archivo_excel)
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

        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Invertido", f"{total_invertido:,.2f} €")
        col2.metric("📈 Ganancias Netas", f"{total_ganancias:,.2f} €")  # corregido
        col3.metric("📊 ROI", f"{roi:.2f} %")
    except Exception as e:
        st.warning(f"No se pudieron calcular los KPIs automáticamente: {e}")







