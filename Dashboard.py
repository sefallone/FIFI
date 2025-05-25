import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# Configuración general de página
st.set_page_config(page_title="Dashboard FIFI", layout="wide")

st.sidebar.title("Configuración")

# =========================
# 📁 Subida de archivo
# =========================
uploaded_file = st.sidebar.file_uploader("Sube el archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Histórico")
        df = df.dropna(subset=["Fecha"])
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df = df.sort_values("Fecha")

        # =========================
        # 🔍 Filtro de fechas
        # =========================
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
            st.warning("⚠️ La fecha de inicio es mayor que la final.")
        else:
            df = df[(df["Fecha"] >= pd.to_datetime(fecha_inicio)) & (df["Fecha"] <= pd.to_datetime(fecha_fin))]

        # =========================
        # 🧮 Preprocesamiento base
        # =========================
        df["Mes"] = df["Fecha"].dt.to_period("M")
        df["Acumulado"] = df["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
        df["MaxAcum"] = df["Acumulado"].cummax()
        df["Drawdown"] = df["Acumulado"] - df["MaxAcum"]
        df["Capital Acumulado"] = df["Capital Invertido"].fillna(0).cumsum()

        # =========================
        # 🚀 Navegación multipágina
        # =========================
        pagina = st.sidebar.radio("Selecciona la sección", ["📌 KPIs", "📊 Gráficos", "📈 Proyecciones", "⚖️ Comparaciones"])

        # =========================
        # 📌 KPIs estilizados
        # =========================
        if pagina == "📌 KPIs":
            st.title("📌 Indicadores Clave de Desempeño (KPIs)")
            st.markdown("---")

            # Cálculos
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

            months = (df["Fecha"].max() - df["Fecha"].min()).days / 30.0
            cagr_mensual = (1 + roi) ** (1 / months) - 1 if months > 0 else 0

            max_drawdown = df["Drawdown"].min()

            # Función para KPI estilizado
            def styled_kpi(title, value, color):
                st.markdown(f"""
                <div style='padding:15px; border-radius:12px; background-color:{color}; margin-bottom:10px;'>
                    <h5 style='margin:0; color:white;'>{title}</h5>
                    <h3 style='margin:0; color:white;'>{value}</h3>
                </div>
                """, unsafe_allow_html=True)

            # KPIs en tarjetas
            col1, col2, col3, col4 = st.columns(4)
            with col1: styled_kpi("💰 Capital Invertido", f"${total_invertido:,.2f}", "#1f77b4")
            with col2: styled_kpi("📈 Aumento de Capital", f"${total_aumento:,.2f}", "#2ca02c")
            with col3: styled_kpi("💸 Retiros", f"${total_retiros:,.2f}", "#ff7f0e")
            with col4: styled_kpi("📊 ROI Total", f"{roi:.2%}", "#d62728")

            col5, col6, col7, col8 = st.columns(4)
            with col5: styled_kpi("📉 Ganancia Bruta", f"${ganancia_bruta:,.2f}", "#9467bd")
            with col6: styled_kpi("📈 Ganancia Neta", f"${ganancia_neta:,.2f}", "#17becf")
            with col7: styled_kpi("🧾 Comisiones Pagadas", f"${comisiones:,.2f}", "#8c564b")
            with col8: styled_kpi("📆 Rentab. Mensual Prom.", f"{monthly_avg_return_pct:.2%}", "#e377c2")

            col9, col10 = st.columns(2)
            with col9: styled_kpi("📈 CAGR Mensual", f"{cagr_mensual:.2%}", "#7f7f7f")
            with col10: styled_kpi("📉 Drawdown Máximo", f"${max_drawdown:,.2f}", "#bcbd22")

        # =========================
        # 📊 Visualizaciones
        # =========================
        elif pagina == "📊 Gráficos":
            st.title("📊 Visualizaciones Financieras")

            fig1 = px.line(df, x="Fecha", y="Ganacias/Pérdidas Netas Acumuladas", title="Ganancia Neta Acumulada")
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = px.line(df, x="Fecha", y=["Ganacias/Pérdidas Brutas", "Ganacias/Pérdidas Netas"], title="Bruta vs Neta")
            st.plotly_chart(fig2, use_container_width=True)

            ganancias_mensuales = df.groupby(df["Fecha"].dt.to_period("M"))["Ganacias/Pérdidas Netas"].sum().reset_index()
            ganancias_mensuales["Fecha"] = ganancias_mensuales["Fecha"].astype(str)
            fig3 = px.bar(ganancias_mensuales, x="Fecha", y="Ganacias/Pérdidas Netas", title="Ganancia Neta Mensual")
            st.plotly_chart(fig3, use_container_width=True)

            comisiones_mensuales = df.groupby(df["Fecha"].dt.to_period("M"))["Comisiones Pagadas"].sum().reset_index()
            comisiones_mensuales["Fecha"] = comisiones_mensuales["Fecha"].astype(str)
            fig4 = px.bar(comisiones_mensuales, x="Fecha", y="Comisiones Pagadas", title="Comisiones Mensuales")
            st.plotly_chart(fig4, use_container_width=True)

            fig5 = px.line(df, x="Fecha", y="Capital Acumulado", title="Capital Invertido Acumulado")
            st.plotly_chart(fig5, use_container_width=True)

            rentabilidad = df.groupby("Mes")["Beneficio en %"].mean().reset_index()
            rentabilidad["Mes"] = rentabilidad["Mes"].astype(str)
            fig6 = px.bar(rentabilidad, x="Mes", y="Beneficio en %", title="Rentabilidad Mensual (%)")
            st.plotly_chart(fig6, use_container_width=True)

        # =========================
        # 📈 Proyecciones
        # =========================
        elif pagina == "📈 Proyecciones":
            st.title("📈 Proyecciones de Crecimiento")

            capital_inicial = st.number_input("Capital Inicial", value=float(df["Capital Acumulado"].iloc[-1]), step=100.0)
            tasa_mensual = monthly_avg_return_pct if not np.isnan(monthly_avg_return_pct) else 0.02
            tasa = st.slider("Tasa de crecimiento mensual (%)", min_value=-10.0, max_value=10.0, value=float(tasa_mensual * 100))
            meses = st.slider("Meses a proyectar", 1, 60, 12)

            proyeccion = [capital_inicial * ((1 + tasa / 100) ** i) for i in range(meses + 1)]
            df_proj = pd.DataFrame({"Mes": list(range(meses + 1)), "Proyección": proyeccion})

            fig_proj = px.line(df_proj, x="Mes", y="Proyección", title="Proyección de Capital Futuro")
            st.plotly_chart(fig_proj, use_container_width=True)

        # =========================
        # ⚖️ Comparaciones
        # =========================
        elif pagina == "⚖️ Comparaciones":
            st.title("⚖️ Comparativa Mensual")

            comparacion = df.groupby("Mes").agg({
                "Ganacias/Pérdidas Brutas": "sum",
                "Ganacias/Pérdidas Netas": "sum",
                "Comisiones Pagadas": "sum",
                "Beneficio en %": "mean"
            }).reset_index()

            comparacion["Mes"] = comparacion["Mes"].astype(str)

            fig_cmp1 = px.bar(comparacion, x="Mes", y=["Ganacias/Pérdidas Brutas", "Ganacias/Pérdidas Netas"],
                              barmode="group", title="Ganancias Brutas vs Netas")
            st.plotly_chart(fig_cmp1, use_container_width=True)

            fig_cmp2 = px.bar(comparacion, x="Mes", y="Comisiones Pagadas", title="Comisiones por Mes")
            st.plotly_chart(fig_cmp2, use_container_width=True)

            fig_cmp3 = px.line(comparacion, x="Mes", y="Beneficio en %", title="Rentabilidad Promedio Mensual (%)")
            st.plotly_chart(fig_cmp3, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")

else:
    st.info("📂 Por favor, sube un archivo Excel desde la barra lateral para comenzar.")



