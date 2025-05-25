import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# Configuración de página
st.set_page_config(page_title="Dashboard FIFI", layout="wide")

# =========================
# 📁 Subida de archivo
# =========================
st.sidebar.title("Configuración")

uploaded_file = st.sidebar.file_uploader("Sube el archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Histórico")
        df = df.dropna(subset=["Fecha"])
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df = df.sort_values("Fecha")

        # Filtro de fechas
        st.sidebar.markdown("### Filtros por Fecha")
        fecha_min = df["Fecha"].min()
        fecha_max = df["Fecha"].max()
        fecha_inicio, fecha_fin = st.sidebar.date_input(
            "Selecciona el rango de fechas",
            [fecha_min, fecha_max],
            min_value=fecha_min,
            max_value=fecha_max
        )

        if fecha_inicio > fecha_fin:
            st.warning("⚠️ La fecha de inicio es mayor que la fecha final.")
        else:
            df = df[(df["Fecha"] >= pd.to_datetime(fecha_inicio)) & (df["Fecha"] <= pd.to_datetime(fecha_fin))]

        # Procesamiento base
        df["Mes"] = df["Fecha"].dt.to_period("M")
        df["Acumulado"] = df["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
        df["MaxAcum"] = df["Acumulado"].cummax()
        df["Drawdown"] = df["Acumulado"] - df["MaxAcum"]
        df["Capital Acumulado"] = df["Capital Invertido"].fillna(0).cumsum()

        # Página seleccionada
        pagina = st.sidebar.radio("Selecciona la sección", ["📌 KPIs", "📊 Gráficos"])

        # =========================
        # 📌 Página de KPIs
        # =========================
        if pagina == "📌 KPIs":
            st.title("📌 Indicadores Clave de Desempeño (KPIs)")

            total_invertido = df["Capital Invertido"].sum(skipna=True)
            total_aumento = df["Aumento Capital"].sum(skipna=True)
            total_retiros = df["Retiro de Fondos"].sum(skipna=True)
            ganancia_bruta = df["Ganacias/Pérdidas Brutas"].sum(skipna=True)
            ganancia_neta = df["Ganacias/Pérdidas Netas"].sum(skipna=True)
            comisiones = df["Comisiones Pagadas"].sum(skipna=True)

            capital_base = total_invertido + total_aumento - total_retiros
            roi = ganancia_neta / capital_base if capital_base > 0 else 0

            monthly_returns = df.groupby("Mes")["Ganacias/Pérdidas Netas"].sum()
            monthly_avg_return_pct = monthly_returns.pct_change().mean()

            if len(df) > 1:
                months = (df["Fecha"].max() - df["Fecha"].min()).days / 30.0
                cagr_mensual = (1 + roi) ** (1 / months) - 1 if months > 0 else 0
            else:
                cagr_mensual = 0

            max_drawdown = df["Drawdown"].min()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("💰 Capital Invertido", f"${total_invertido:,.2f}")
            col2.metric("📈 Aumento de Capital", f"${total_aumento:,.2f}")
            col3.metric("💸 Retiros", f"${total_retiros:,.2f}")
            col4.metric("📊 ROI Total", f"{roi:.2%}")

            col5, col6, col7, col8 = st.columns(4)
            col5.metric("📉 Ganancia Bruta", f"${ganancia_bruta:,.2f}")
            col6.metric("📈 Ganancia Neta", f"${ganancia_neta:,.2f}")
            col7.metric("🧾 Comisiones Pagadas", f"${comisiones:,.2f}")
            col8.metric("📆 Rentab. Mensual Prom.", f"{monthly_avg_return_pct:.2%}")

            col9, col10 = st.columns(2)
            col9.metric("📈 CAGR Mensual", f"{cagr_mensual:.2%}")
            col10.metric("📉 Drawdown Máximo", f"${max_drawdown:,.2f}")

        # =========================
        # 📊 Página de Gráficos
        # =========================
        elif pagina == "📊 Gráficos":
            st.title("📊 Visualizaciones Financieras")

            # 1. Línea: Ganancia Neta Acumulada
            fig1 = px.line(df, x="Fecha", y="Ganacias/Pérdidas Netas Acumuladas", title="Ganancia Neta Acumulada")
            st.plotly_chart(fig1, use_container_width=True)

            # 2. Línea: Ganancia Bruta vs Neta
            fig2 = px.line(df, x="Fecha", y=["Ganacias/Pérdidas Brutas", "Ganacias/Pérdidas Netas"], title="Bruta vs Neta")
            st.plotly_chart(fig2, use_container_width=True)

            # 3. Barras: Ganancia Neta mensual
            ganancias_mensuales = df.groupby(df["Fecha"].dt.to_period("M"))["Ganacias/Pérdidas Netas"].sum().reset_index()
            ganancias_mensuales["Fecha"] = ganancias_mensuales["Fecha"].astype(str)
            fig3 = px.bar(ganancias_mensuales, x="Fecha", y="Ganacias/Pérdidas Netas", title="Ganancia Neta Mensual")
            st.plotly_chart(fig3, use_container_width=True)

            # 4. Barras: Comisiones mensuales
            comisiones_mensuales = df.groupby(df["Fecha"].dt.to_period("M"))["Comisiones Pagadas"].sum().reset_index()
            comisiones_mensuales["Fecha"] = comisiones_mensuales["Fecha"].astype(str)
            fig4 = px.bar(comisiones_mensuales, x="Fecha", y="Comisiones Pagadas", title="Comisiones Mensuales")
            st.plotly_chart(fig4, use_container_width=True)

            # 5. Línea: Capital acumulado
            fig5 = px.line(df, x="Fecha", y="Capital Acumulado", title="Capital Invertido Acumulado")
            st.plotly_chart(fig5, use_container_width=True)

            # 6. Barras: Rentabilidad mensual %
            rentabilidad = df.groupby("Mes")["Beneficio en %"].mean().reset_index()
            rentabilidad["Mes"] = rentabilidad["Mes"].astype(str)
            fig6 = px.bar(rentabilidad, x="Mes", y="Beneficio en %", title="Rentabilidad Mensual (%)")
            st.plotly_chart(fig6, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")

else:
    st.info("📂 Por favor, sube un archivo Excel desde la barra lateral para comenzar.")

