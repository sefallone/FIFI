import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.graph_objs import Scatter
from datetime import datetime
from PIL import Image
import base64
import calendar
from io import BytesIO

# Configuración general
st.set_page_config(page_title="Dashboard FIFI", layout="wide")

# Logo
logo = Image.open("Logo.jpg")
st.markdown("""
    <div style='text-align: center;'>
        <img src='data:image/jpeg;base64,{}' style='width:200px;'/><h3 style='margin-top:10px;'>Fallone Investments</h3>
    </div>
""".format(base64.b64encode(open("Logo.jpg", "rb").read()).decode()), unsafe_allow_html=True)

with st.sidebar:
    st.title("Configuración")

uploaded_file = st.sidebar.file_uploader("Sube el archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Histórico")
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df = df.dropna(subset=["Fecha"])

        fecha_min = df["Fecha"].min().replace(day=1)
        fecha_max_original = df["Fecha"].max().replace(day=1)
        fecha_max_limit = fecha_max_original - pd.DateOffset(months=1)

        años_disponibles = list(range(fecha_min.year, fecha_max_limit.year + 1))
        meses_disponibles = list(range(1, 13))

        st.sidebar.markdown("### Filtro por Mes y Año")
        col1, col2 = st.sidebar.columns(2)
        anio_inicio = col1.selectbox("Año inicio", años_disponibles, index=0)
        mes_inicio = col2.selectbox("Mes inicio", meses_disponibles, index=min(fecha_min.month - 1, 11), format_func=lambda m: calendar.month_name[m])

        col3, col4 = st.sidebar.columns(2)
        index_anio_fin = min(len(años_disponibles) - 1, años_disponibles.index(fecha_max_limit.year))
        index_mes_fin = min(fecha_max_limit.month - 1, 11)
        anio_fin = col3.selectbox("Año fin", años_disponibles, index=index_anio_fin)
        mes_fin = col4.selectbox("Mes fin", meses_disponibles, index=index_mes_fin, format_func=lambda m: calendar.month_name[m])

        fecha_inicio_sel = pd.Timestamp(anio_inicio, mes_inicio, 1)
        fecha_fin_sel = pd.Timestamp(anio_fin, mes_fin, 1) + pd.offsets.MonthEnd(0)

        if fecha_inicio_sel < fecha_min:
            st.warning(f"⚠️ La fecha de inicio no puede ser anterior a {fecha_min.strftime('%B %Y')}.")
            st.stop()
        if fecha_fin_sel > fecha_max_limit + pd.offsets.MonthEnd(0):
            st.warning(f"⚠️ La fecha de fin no puede ser posterior a {fecha_max_limit.strftime('%B %Y')}.")
            st.stop()
        if fecha_inicio_sel > fecha_fin_sel:
            st.warning("⚠️ La fecha de inicio no puede ser mayor que la fecha final.")
            st.stop()

        df = df[(df["Fecha"] >= fecha_inicio_sel) & (df["Fecha"] <= fecha_fin_sel)]
        if df.empty:
            st.warning("⚠️ No hay datos disponibles en el rango de fechas seleccionado.")
            st.stop()

        df["Mes"] = df["Fecha"].dt.to_period("M")
        df["Acumulado"] = df["Ganancias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
        df["MaxAcum"] = df["Acumulado"].cummax()
        df["Drawdown"] = df["Acumulado"] - df["MaxAcum"]
        df["Capital Acumulado"] = df["Capital Invertido"]

        pagina = st.sidebar.radio("Selecciona la sección", ["📌 KPIs", "📊 Gráficos", "📈 Proyecciones", "⚖️ Comparaciones"])

        if pagina == "📌 KPIs":
            st.title("📌 Indicadores Clave de Desempeño (KPIs)")
            st.markdown("---")
            capital_invertido = df["Capital Invertido"].dropna().iloc[-1] if not df["Capital Invertido"].dropna().empty else 0
            capital_inicial = df["Aumento Capital"].dropna().iloc[0] if not df["Aumento Capital"].dropna().empty else 0
            inyeccion_total = df["Aumento Capital"].sum(skipna=True)
            inversionista = df["ID Inv"].dropna().iloc[0] if not df["ID Inv"].dropna().empty else "Desconocido"
            total_retiros = df["Retiro de Fondos"].sum(skipna=True)
            ganancia_bruta = df["Ganancias/Pérdidas Brutas"].sum(skipna=True)
            ganancia_neta = df["Ganancias/Pérdidas Netas"].sum(skipna=True)
            comisiones = df["Comisiones Pagadas"].dropna().iloc[-1] if not df["Comisiones Pagadas"].dropna().empty else 0
            fecha_ingreso = df["Fecha"].dropna().iloc[0].date() if not df["Fecha"].dropna().empty else "Sin fecha"

            capital_base = capital_invertido - total_retiros
            roi = ganancia_neta / capital_base if capital_base > 0 else 0

            monthly_returns = df.groupby("Mes")["Ganancias/Pérdidas Netas"].sum()
            monthly_avg_return_pct = monthly_returns.pct_change().mean()

            months = (df["Fecha"].max() - df["Fecha"].min()).days / 30.0
            cagr_mensual = (1 + roi) ** (1 / months) - 1 if months > 0 else 0

            max_drawdown = df["Drawdown"].min()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Inversionista", inversionista)
            col2.metric("💼 Capital Inicial", f"${capital_inicial:,.2f}")
            col3.metric("💰 Capital Invertido", f"${capital_invertido:,.2f}")
            col4.metric("💵 Inyección Capital Total", f"${inyeccion_total:,.2f}")

            col5, col6, col7, col8 = st.columns(4)
            col5.metric("💸 Retiros", f"${total_retiros:,.2f}")
            col6.metric("📉 Ganancia Bruta", f"${ganancia_bruta:,.2f}")
            col7.metric("📈 Ganancia Neta", f"${ganancia_neta:,.2f}")
            col8.metric("🧾 Comisiones Pagadas", f"${comisiones:,.2f}")

            col9, col10, col11 = st.columns(3)
            col9.metric("📅 Fecha Ingreso", str(fecha_ingreso))
            col10.metric("📊 ROI Total", f"{roi:.2%}")
            col11.metric("📈 CAGR Mensual", f"{cagr_mensual:.2%}")

            promedio_mensual_ganancias_pct = df.groupby("Mes")["Beneficio en %"].mean().mean()
            st.metric("📈 Promedio Mensual de Ganancias", f"{promedio_mensual_ganancias_pct * 100:.2f}%")

        elif pagina == "📊 Gráficos":
            st.title("📊 Visualizaciones Financieras")
            df_plot = df.copy()
            df_plot["Retiros"] = df_plot["Retiro de Fondos"].fillna(0)
            fig_capital = px.bar(df_plot, x="Fecha", y="Retiros", title="Capital Invertido y Retiros", template="plotly_white")
            fig_capital.add_scatter(x=df_plot["Fecha"], y=df_plot["Capital Invertido"], mode='lines+markers', name="Capital Invertido", line=dict(color="blue"))
            st.plotly_chart(fig_capital, use_container_width=True)
            fig1 = px.line(df, x="Fecha", y="Ganancias/Pérdidas Netas Acumuladas", title="Ganancia Neta Acumulada", template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)

        elif pagina == "📈 Proyecciones":
            st.title("📈 Proyección de Inversión Personalizada")
            capital_actual = float(df["Capital Invertido"].dropna().iloc[-1])
            aumento_opcion = st.selectbox("Selecciona porcentaje de aumento de capital", [0, 5, 10, 20, 30, 50])
            promedio_mensual_ganancias = df["Beneficio en %"].mean()
            st.metric("📆 Promedio Mensual de Ganancias", f"{promedio_mensual_ganancias:.2%}")
            beneficio_mensual = st.slider("Beneficio mensual estimado (%)", min_value=0.0, max_value=15.0, value=5.0, step=0.5)
            meses_proyeccion = st.slider("Duración de la inversión (meses)", min_value=1, max_value=60, value=12)
            capital_proyectado = capital_actual * (1 + aumento_opcion / 100)
            proyeccion = [capital_proyectado * ((1 + beneficio_mensual / 100) ** i) for i in range(meses_proyeccion + 1)]
            df_proy = pd.DataFrame({"Mes": list(range(meses_proyeccion + 1)), "Proyección": proyeccion})
            col1, col2, col3 = st.columns(3)
            col1.metric("💼 Capital Inicial Proyectado", f"${capital_proyectado:,.2f}")
            col2.metric("📈 Valor Estimado Final", f"${proyeccion[-1]:,.2f}")
            capital_comp_anual = capital_proyectado * ((1 + beneficio_mensual / 100) ** 12)
            col3.metric("📈 Capital Compuesto Anual", f"${capital_comp_anual:,.2f}")
            fig = px.line(df_proy, x="Mes", y="Proyección", title="Proyección de Crecimiento de Capital", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df_proy.style.format({"Proyección": "${:,.2f}"}), use_container_width=True)

        elif pagina == "⚖️ Comparaciones":
            st.title("⚖️ Comparaciones por Año")
            df['Año'] = df['Fecha'].dt.year
            df['MesNombre'] = df['Fecha'].dt.strftime('%b')
            df['MesOrden'] = df['Fecha'].dt.month
            años_disponibles = df['Año'].dropna().unique().tolist()
            años_seleccionados = st.multiselect("Selecciona los años a comparar", sorted(años_disponibles), default=sorted(años_disponibles))
            comparacion_anual = df[df['Año'].isin(años_seleccionados)].groupby(['Año', 'MesNombre', 'MesOrden']).agg({
                "Ganancias/Pérdidas Brutas": "sum",
                "Ganancias/Pérdidas Netas": "sum",
                "Comisiones Pagadas": "sum",
                "Beneficio en %": "mean"
            }).reset_index().sort_values("MesOrden")
            comparacion_anual["Beneficio en %"] *= 100
            fig_cmp3 = px.bar(comparacion_anual, x="MesNombre", y="Beneficio en %", color="Año", barmode="group", title="Rentabilidad Promedio Mensual por Año", template="plotly_white")
            fig_cmp3.update_layout(yaxis_title="Rentabilidad (%)")
            st.plotly_chart(fig_cmp3, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
else:
    st.info("📂 Por favor, sube un archivo Excel desde la barra lateral para comenzar.")





