import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# Configuración general
st.set_page_config(page_title="Dashboard FIFI", layout="wide")
st.sidebar.title("Configuración")

# Subida de archivo
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

        # Preprocesamiento
        df["Mes"] = df["Fecha"].dt.to_period("M")
        df["Acumulado"] = df["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
        df["MaxAcum"] = df["Acumulado"].cummax()
        df["Drawdown"] = df["Acumulado"] - df["MaxAcum"]
        df["Capital Acumulado"] = df["Capital Invertido"].fillna(0).cumsum()

        # Navegación multipágina
        pagina = st.sidebar.radio("Selecciona la sección", ["📌 KPIs", "📊 Gráficos", "📈 Proyecciones", "⚖️ Comparaciones"])

        # KPI estilizado profesional
        def styled_kpi(title, value, bg_color="#ffffff", text_color="#333"):
            st.markdown(f"""
            <div style="
                background-color: {bg_color};
                color: {text_color};
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                text-align: center;
                margin-bottom: 15px;">
                <div style='font-size:18px; font-weight: 600;'>{title}</div>
                <div style='font-size:28px; font-weight: bold;'>{value}</div>
            </div>
            """, unsafe_allow_html=True)

        # =========================
        # 📌 KPIs
        # =========================
        if pagina == "📌 KPIs":
            st.title("📌 Indicadores Clave de Desempeño (KPIs)")
            st.markdown("---")

            # KPIs actualizados
            capital_invertido = df["Capital Invertido"].dropna().iloc[-1]
            capital_inicial = df["Aumento Capital"].dropna().iloc[0]
            inyeccion_total = df["Aumento Capital"].sum(skipna=True)
            inversionista = df["ID Inv"].dropna().iloc[0]
            total_retiros = df["Retiro de Fondos"].sum(skipna=True)
            ganancia_bruta = df["Ganacias/Pérdidas Brutas"].sum(skipna=True)
            ganancia_neta = df["Ganacias/Pérdidas Netas"].sum(skipna=True)
            comisiones = df["Comisiones Pagadas"].dropna().iloc[-1]
            fecha_ingreso = df["Fecha"].dropna().iloc[0].date()

            capital_base = capital_invertido - total_retiros
            roi = ganancia_neta / capital_base if capital_base > 0 else 0

            monthly_returns = df.groupby("Mes")["Ganacias/Pérdidas Netas"].sum()
            monthly_avg_return_pct = monthly_returns.pct_change().mean()

            months = (df["Fecha"].max() - df["Fecha"].min()).days / 30.0
            cagr_mensual = (1 + roi) ** (1 / months) - 1 if months > 0 else 0

            max_drawdown = df["Drawdown"].min()

            # Mostrar KPIs con estilo
            col1, col2, col3, col4 = st.columns(4)
            with col1: styled_kpi("🧑 Inversionista", f"{inversionista}", "#D7F9F1")
            with col2: styled_kpi("💼 Capital Inicial", f"${capital_inicial:,.2f}", "#E8F0FE")
            with col3: styled_kpi("💰 Capital Invertido", f"${capital_invertido:,.2f}", "#E6F4EA")
            with col4: styled_kpi("💵 Inyección Capital Total", f"${inyeccion_total:,.2f}", "#FFF9E5")

            col5, col6, col7, col8 = st.columns(4)
            with col5: styled_kpi("💸 Retiros", f"${total_retiros:,.2f}", "#FFE5EC")
            with col6: styled_kpi("📉 Ganancia Bruta", f"${ganancia_bruta:,.2f}", "#F0F4C3")
            with col7: styled_kpi("📈 Ganancia Neta", f"${ganancia_neta:,.2f}", "#E1F5FE")
            with col8: styled_kpi("🧾 Comisiones Pagadas", f"${comisiones:,.2f}", "#F3E5F5")

            col9, col10, col11 = st.columns(3)
            with col9: styled_kpi("📅 Fecha Ingreso", f"{fecha_ingreso.strftime('%d/%m/%Y')}", "#FFEBEE")
            with col10: styled_kpi("📊 ROI Total", f"{roi:.2%}", "#DDEBF7")
            with col11: styled_kpi("📈 CAGR Mensual", f"{cagr_mensual:.2%}", "#F0F0F0")

            st.markdown("---")
            styled_kpi("📆 Rentabilidad Promedio Mensual", f"{monthly_avg_return_pct:.2%}", "#F1F8E9")

        # =========================
        # 📊 GRÁFICOS
        # =========================
        elif pagina == "📊 Gráficos":
            st.title("📊 Visualizaciones Financieras")

            fig1 = px.line(df, x="Fecha", y="Ganacias/Pérdidas Netas Acumuladas", title="Ganancia Neta Acumulada", template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)

            fig2 = px.line(df, x="Fecha", y=["Ganacias/Pérdidas Brutas", "Ganacias/Pérdidas Netas"], title="Bruta vs Neta", template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)

            ganancias_mensuales = df.groupby(df["Fecha"].dt.to_period("M"))["Ganacias/Pérdidas Netas"].sum().reset_index()
            ganancias_mensuales["Fecha"] = ganancias_mensuales["Fecha"].astype(str)
            fig3 = px.bar(ganancias_mensuales, x="Fecha", y="Ganacias/Pérdidas Netas", title="Ganancia Neta Mensual", template="plotly_white")
            st.plotly_chart(fig3, use_container_width=True)

            comisiones_mensuales = df.groupby(df["Fecha"].dt.to_period("M"))["Comisiones Pagadas"].sum().reset_index()
            comisiones_mensuales["Fecha"] = comisiones_mensuales["Fecha"].astype(str)
            fig4 = px.bar(comisiones_mensuales, x="Fecha", y="Comisiones Pagadas", title="Comisiones Mensuales", template="plotly_white")
            st.plotly_chart(fig4, use_container_width=True)

            fig5 = px.line(df, x="Fecha", y="Capital Acumulado", title="Capital Invertido Acumulado", template="plotly_white")
            st.plotly_chart(fig5, use_container_width=True)

            rentabilidad = df.groupby("Mes")["Beneficio en %"].mean().reset_index()
            rentabilidad["Mes"] = rentabilidad["Mes"].astype(str)
            fig6 = px.bar(rentabilidad, x="Mes", y="Beneficio en %", title="Rentabilidad Mensual (%)", template="plotly_white")
            st.plotly_chart(fig6, use_container_width=True)

        # =========================
        # 📈 PROYECCIONES
        # =========================
        elif pagina == "📈 Proyecciones":
            st.title("📈 Proyecciones de Crecimiento")

            capital_inicial_proy = st.number_input("Capital Inicial", value=float(df["Capital Acumulado"].iloc[-1]), step=100.0)
            tasa_mensual = monthly_avg_return_pct if not np.isnan(monthly_avg_return_pct) else 0.02
            tasa = st.slider("Tasa de crecimiento mensual (%)", min_value=-10.0, max_value=10.0, value=float(tasa_mensual * 100))
            meses = st.slider("Meses a proyectar", 1, 60, 12)

            proyeccion = [capital_inicial_proy * ((1 + tasa / 100) ** i) for i in range(meses + 1)]
            df_proj = pd.DataFrame({"Mes": list(range(meses + 1)), "Proyección": proyeccion})

            fig_proj = px.line(df_proj, x="Mes", y="Proyección", title="Proyección de Capital Futuro", template="plotly_white")
            st.plotly_chart(fig_proj, use_container_width=True)

        # =========================
        # ⚖️ COMPARACIONES
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
                              barmode="group", title="Ganancias Brutas vs Netas", template="plotly_white")
            st.plotly_chart(fig_cmp1, use_container_width=True)

            fig_cmp2 = px.bar(comparacion, x="Mes", y="Comisiones Pagadas", title="Comisiones por Mes", template="plotly_white")
            st.plotly_chart(fig_cmp2, use_container_width=True)

            fig_cmp3 = px.line(comparacion, x="Mes", y="Beneficio en %", title="Rentabilidad Promedio Mensual (%)", template="plotly_white")
            st.plotly_chart(fig_cmp3, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
else:
    st.info("📂 Por favor, sube un archivo Excel desde la barra lateral para comenzar.")



