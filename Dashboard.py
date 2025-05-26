import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.graph_objs import Scatter
from datetime import datetime
from PIL import Image
import base64
from io import BytesIO
import calendar

# Configuración general
st.set_page_config(page_title="Dashboard FIFI", layout="wide")
# Logo en página principal
logo = Image.open("Logo.jpg")
st.markdown("""
    <div style='text-align: center;'>
        <img src='data:image/jpeg;base64,{}' style='width:200px;'/>
        <h3 style='margin-top:10px;'>Fallone Investments</h3>
    </div>
    """.format(base64.b64encode(open("Logo.jpg", "rb").read()).decode()), unsafe_allow_html=True)

# Sidebar config
with st.sidebar:
    st.title("Configuración")
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
            if df.empty:
                st.warning("⚠️ No hay datos disponibles en el rango de fechas seleccionado.")
                st.stop()


        # Preprocesamiento
        df["Mes"] = df["Fecha"].dt.to_period("M")
        df["Acumulado"] = df["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
        df["MaxAcum"] = df["Acumulado"].cummax()
        df["Drawdown"] = df["Acumulado"] - df["MaxAcum"]
        df["Capital Acumulado"] = df["Capital Invertido"]

        pagina = st.sidebar.radio("Selecciona la sección", ["📌 KPIs", "📊 Gráficos", "📈 Proyecciones", "⚖️ Comparaciones"])

        def styled_kpi(title, value, bg_color="#ffffff", text_color="#333", tooltip=""):
            st.markdown(f"""
            <div title="{tooltip}" style="
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



        if pagina == "📌 KPIs":
            st.title("📌 Indicadores Clave de Desempeño (KPIs)")
            st.markdown("---")

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

            col1, col2, col3, col4 = st.columns(4)
            with col1: styled_kpi("🧑 Inversionista", f"{inversionista}", "#D7F9F1", tooltip="ID del inversionista.")
            with col2: styled_kpi("💼 Capital Inicial", f"${capital_inicial:,.2f}", "#E8F0FE", tooltip="Capital Inicial Invertido.")
            with col3: styled_kpi("💰 Capital Invertido", f"${capital_invertido:,.2f}", "#E6F4EA", tooltip="Capital Actual invertido'.")
            with col4: styled_kpi("💵 Inyección Capital Total", f"${inyeccion_total:,.2f}", "#FFF9E5", tooltip="Capital Total Inyectado.")

            col5, col6, col7, col8 = st.columns(4)
            with col5: styled_kpi("💸 Retiros", f"${total_retiros:,.2f}", "#FFE5EC", tooltip="Total de los retiros de fondos.")
            with col6: styled_kpi("📉 Ganancia Bruta", f"${ganancia_bruta:,.2f}", "#F0F4C3", tooltip="Ganancias antes de deducir comisiones.")
            with col7: styled_kpi("📈 Ganancia Neta", f"${ganancia_neta:,.2f}", "#E1F5FE", tooltip="Ganancias luego de deducir comisiones.")
            with col8: styled_kpi("🧾 Comisiones Pagadas", f"${comisiones:,.2f}", "#F3E5F5", tooltip="Valor acumulado de comisiones pagadas.")

            col9, col10, col11 = st.columns(3)
            with col9: styled_kpi("📅 Fecha Ingreso", f"{fecha_ingreso.strftime('%d/%m/%Y')}", "#FFEBEE", tooltip="Fecha de Ingreso al Fondo.")
            with col10: styled_kpi("📊 ROI Total", f"{roi:.2%}", "#DDEBF7", tooltip="Retorno total sobre el capital neto invertido.")
            with col11: styled_kpi("📈 CAGR Mensual", f"{cagr_mensual:.2%}", "#F0F0F0", tooltip="Tasa de crecimiento promedio mensual compuesto.")

            st.markdown("---")
            styled_kpi("📆 Rentabilidad Promedio Mensual", f"{monthly_avg_return_pct:.2%}", "#F1F8E9", tooltip="Promedio mensual de retornos netos relativos.")

            # Nuevos KPIs adicionales
            col12, col13, col14 = st.columns(3)
            with col12:
                frecuencia_aportes = df[df["Aumento Capital"] > 0].shape[0]
                styled_kpi("🔁 Frecuencia de Aportes", f"{frecuencia_aportes}", "#E3F2FD", tooltip="Número de registros con aumentos de capital.")
            with col13:
                frecuencia_retiros = df[df["Retiro de Fondos"] > 0].shape[0]
                styled_kpi("📤 Frecuencia de Retiros", f"{frecuencia_retiros}", "#FFF3E0", tooltip="Número de registros con retiros de fondos.")
            with col14:
                mejor_mes = df.loc[df["Beneficio en %"].idxmax()]["Mes"]
                styled_kpi("📈 Mejor Mes en %", f"{mejor_mes}", "#E8F5E9", tooltip="Mes con mayor rentabilidad porcentual.")

            col15 = st.columns(1)[0]
            with col15:
                peor_mes = df.loc[df["Beneficio en %"].idxmin()]["Mes"]
                styled_kpi("📉 Peor Mes en %", f"{peor_mes}", "#FFEBEE", tooltip="Mes con menor rentabilidad porcentual.")

            # Mejor Mes Promedio entre años
            col16 = st.columns(1)[0]
            with col16:
                df_mes_anio = df.copy()
                df_mes_anio["Año"] = df_mes_anio["Fecha"].dt.year
                promedio_meses = df_mes_anio.groupby(["Año", df_mes_anio["Fecha"].dt.month])["Ganacias/Pérdidas Brutas"].sum().reset_index()
                meses_comunes = promedio_meses.groupby("Fecha").count()["Año"] == promedio_meses["Año"].nunique()
                comunes = promedio_meses[promedio_meses["Fecha"].isin(meses_comunes[meses_comunes].index)]
                mejor_mes_inv = comunes.groupby("Fecha")["Ganacias/Pérdidas Brutas"].mean().idxmax()
                styled_kpi("🌟 Mejor Mes (Inversión)", f"{calendar.month_name[mejor_mes_inv]}", "#FFF3F3", tooltip="Mes con mejor desempeño promedio considerando solo los meses en común entre todos los años.")

        elif pagina == "📊 Gráficos":
            st.title("📊 Visualizaciones Financieras")

            df_plot = df.copy()
            df_plot["Retiros"] = df_plot["Retiro de Fondos"].fillna(0)

            fig_capital = px.bar(df_plot, x="Fecha", y="Retiros", title="Capital Invertido y Retiros", template="plotly_white")
            fig_capital.add_scatter(x=df_plot["Fecha"], y=df_plot["Capital Invertido"], mode='lines+markers', name="Capital Invertido", line=dict(color="blue"))
            st.plotly_chart(fig_capital, use_container_width=True)

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

            rentabilidad = df.groupby("Mes")["Beneficio en %"].mean().reset_index()
            rentabilidad["Mes"] = rentabilidad["Mes"].astype(str)
            fig6 = px.bar(rentabilidad, x="Mes", y="Beneficio en %", title="Rentabilidad Mensual (%)", template="plotly_white")
            st.plotly_chart(fig6, use_container_width=True)

        elif pagina == "📈 Proyecciones":
            st.title("📈 Proyección de Inversión Personalizada")

            capital_actual = float(df["Capital Invertido"].dropna().iloc[-1])
            aumento_opcion = st.selectbox("Selecciona porcentaje de aumento de capital", [0, 5, 10, 20, 30, 50])
            promedio_mensual_ganancias = (df["Beneficio en %"].sum(skipna=True) / len(df["Beneficio en %"]) )
            col_kpi = st.columns(1)[0]
            with col_kpi:
                styled_kpi("📆 Promedio Mensual de Ganancias", f"{promedio_mensual_ganancias:.2%}", "#E0F7FA", tooltip="Promedio mensual de las ganancias brutas en porcentaje sobre el capital actual.")

            beneficio_mensual = st.slider("Beneficio mensual estimado (%)", min_value=0.0, max_value=15.0, value=5.0, step=0.5)
            meses_proyeccion = st.slider("Duración de la inversión (meses)", min_value=1, max_value=60, value=12)

            capital_proyectado = capital_actual * (1 + aumento_opcion / 100)
            proyeccion = [capital_proyectado * ((1 + beneficio_mensual / 100) ** i) for i in range(meses_proyeccion + 1)]
            df_proy = pd.DataFrame({"Mes": list(range(meses_proyeccion + 1)), "Proyección": proyeccion})

            st.markdown("---")
            col1, _ = st.columns(2)
            col1, col2, col3 = st.columns(3)
            with col1:
                styled_kpi("💼 Capital Inicial Proyectado", f"${capital_proyectado:,.2f}", "#E8F0FE")
            with col2:
                styled_kpi("📈 Valor Estimado Final", f"${proyeccion[-1]:,.2f}", "#E6F4EA")
            with col3:
                capital_comp_anual = capital_proyectado * ((1 + beneficio_mensual / 100) ** 12)
                styled_kpi("📈 Capital Compuesto Anual", f"${capital_comp_anual:,.2f}", "#F0F4C3")
                st.caption("Proyección de capital al final de un año con interés compuesto mensual.")            

            fig = px.line(df_proy, x="Mes", y="Proyección", title="Proyección de Crecimiento de Capital", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📄 Detalle de Proyección (mes a mes)")
            st.dataframe(df_proy.style.format({"Proyección": "${:,.2f}"}), use_container_width=True)

            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
              resumen = pd.DataFrame({
                    "Descripción": [
                    "Capital Actual",
                    "% Aumento",
                    "Capital Proyectado",
                    "% Beneficio Mensual",
                    "Meses de Proyección",
                    "Valor Final Estimado",
                    "Capital Compuesto Anual"
                ],
                "Valor": [
                    capital_actual,
                    f"{aumento_opcion}%",
                    capital_proyectado,
                    f"{beneficio_mensual}%",
                    meses_proyeccion,
                    proyeccion[-1],
                    capital_proyectado * ((1 + beneficio_mensual / 100) ** 12)
                ]
              })
              resumen.to_excel(writer, index=False, sheet_name="Resumen")
              df_proy.to_excel(writer, index=False, sheet_name="Proyección")
            excel_data = output.getvalue()
            st.download_button("📥 Descargar proyección en Excel", data=excel_data, file_name="proyeccion.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        elif pagina == "⚖️ Comparaciones":
            st.title("⚖️ Comparaciones por Año")
            df['Año'] = df['Fecha'].dt.year
            df['MesNombre'] = df['Fecha'].dt.strftime('%b')
            df['MesOrden'] = df['Fecha'].dt.month

            años_disponibles = df['Año'].dropna().unique().tolist()
            años_seleccionados = st.multiselect("Selecciona los años a comparar", sorted(años_disponibles), default=sorted(años_disponibles))

            comparacion_anual = df[df['Año'].isin(años_seleccionados)].groupby(['Año', 'MesNombre', 'MesOrden']).agg({
                "Ganacias/Pérdidas Brutas": "sum",
                "Ganacias/Pérdidas Netas": "sum",
                "Comisiones Pagadas": "sum",
                "Beneficio en %": "mean"
            }).reset_index().sort_values("MesOrden")

            st.markdown("### 📊 Ganancias Brutas vs Netas")
            fig_cmp1 = px.bar(
                comparacion_anual,
                x="MesNombre",
                y=["Ganacias/Pérdidas Brutas", "Ganacias/Pérdidas Netas"],
                color="Año",
                barmode="group",
                title="Ganancias Brutas vs Netas por Mes y Año",
                template="plotly_white"
            )
            st.plotly_chart(fig_cmp1, use_container_width=True)

            st.markdown("### 💸 Comisiones por Mes")
            fig_cmp2 = px.bar(
                comparacion_anual,
                x="MesNombre",
                y="Comisiones Pagadas",
                color="Año",
                barmode="group",
                title="Comisiones por Mes y Año",
                template="plotly_white"
            )
            st.plotly_chart(fig_cmp2, use_container_width=True)

            st.markdown("### 📈 Rentabilidad Promedio Mensual (%)")
            fig_cmp3 = px.line(
                comparacion_anual,
                x="MesNombre",
                y="Beneficio en %",
                color="Año",
                title="Rentabilidad Promedio Mensual por Año",
                template="plotly_white"
            )
            st.plotly_chart(fig_cmp3, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
else:
    st.info("📂 Por favor, sube un archivo Excel desde la barra lateral para comenzar.")




