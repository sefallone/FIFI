import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from PIL import Image
import base64
import calendar
from io import BytesIO
from dateutil.relativedelta import relativedelta

# Configuración general
st.set_page_config(page_title="Dashboard FIFI", layout="wide")

# Logo en página principal
try:
    logo = Image.open("Logo.jpg")
    st.markdown("""
        <div style='text-align: center;'>
            <img src='data:image/jpeg;base64,{}' style='width:200px;'/>
            <h3 style='margin-top:10px;'>Fallone Investments</h3>
        </div>
        """.format(base64.b64encode(open("Logo.jpg", "rb").read()).decode()), unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Logo no encontrado. Se mostrará sin imagen.")

# Sidebar config
with st.sidebar:
    st.title("Configuración")
    uploaded_file = st.file_uploader("Sube el archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Cargar el archivo completo (sin filtrar)
        df_completo = pd.read_excel(uploaded_file, sheet_name="Histórico")
        df_completo["Fecha"] = pd.to_datetime(df_completo["Fecha"], errors="coerce")
        df_completo = df_completo.dropna(subset=["Fecha"])

        # Validar columnas requeridas
        required_columns = ["Capital Invertido", "Aumento Capital", "Retiro de Fondos", 
                          "Ganacias/Pérdidas Netas", "Comisiones Pagadas", "Fecha"]
        if not all(col in df_completo.columns for col in required_columns):
            st.error("❌ El archivo no contiene las columnas requeridas.")
            st.stop()

        # Configuración de filtros de fecha
        fecha_min = df_completo["Fecha"].min().replace(day=1)
        fecha_max_original = df_completo["Fecha"].max().replace(day=1)
        fecha_max_limit = fecha_max_original - pd.DateOffset(months=1)

        años_disponibles = list(range(fecha_min.year, fecha_max_limit.year + 1))
        meses_disponibles = list(range(1, 13))

        with st.sidebar:
            st.markdown("### Filtro por Mes y Año")
            col1, col2 = st.columns(2)
            anio_inicio = col1.selectbox("Año inicio", años_disponibles, index=0)
            mes_inicio = col2.selectbox("Mes inicio", meses_disponibles, 
                                      index=fecha_min.month - 1,
                                      format_func=lambda m: calendar.month_name[m])

            col3, col4 = st.columns(2)
            anio_fin = col3.selectbox("Año fin", años_disponibles, 
                                     index=len(años_disponibles) - 1)
            mes_fin = col4.selectbox("Mes fin", meses_disponibles, 
                                    index=fecha_max_limit.month - 1,
                                    format_func=lambda m: calendar.month_name[m])

            fecha_inicio_sel = pd.Timestamp(anio_inicio, mes_inicio, 1)
            fecha_fin_sel = pd.Timestamp(anio_fin, mes_fin, 1) + pd.offsets.MonthEnd(0)

            # Validaciones de rango de fechas
            if fecha_inicio_sel < fecha_min:
                st.warning(f"⚠️ La fecha de inicio no puede ser anterior a {fecha_min.strftime('%B %Y')}.")
                st.stop()
            if fecha_fin_sel > fecha_max_limit + pd.offsets.MonthEnd(0):
                st.warning(f"⚠️ La fecha de fin no puede ser posterior a {fecha_max_limit.strftime('%B %Y')}.")
                st.stop()
            if fecha_inicio_sel > fecha_fin_sel:
                st.warning("⚠️ La fecha de inicio no puede ser mayor que la fecha final.")
                st.stop()

        # Filtrar DataFrame
        df = df_completo[(df_completo["Fecha"] >= fecha_inicio_sel) & (df_completo["Fecha"] <= fecha_fin_sel)]
        if df.empty:
            st.warning("⚠️ No hay datos disponibles en el rango de fechas seleccionado.")
            st.stop()

        # Preprocesamiento adicional
        df["Mes"] = df["Fecha"].dt.to_period("M")
        df["Acumulado"] = df["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
        df["MaxAcum"] = df["Acumulado"].cummax()
        df["Drawdown"] = df["Acumulado"] - df["MaxAcum"]

        # Función para KPIs estilizados
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

        # Navegación entre páginas
        pagina = st.sidebar.radio("Selecciona la sección", 
                                ["📌 KPIs", "📊 Gráficos", "📈 Proyecciones", "⚖️ Comparaciones"])

        if pagina == "📌 KPIs":
    st.title("📌 Indicadores Clave de Desempeño (KPIs)")
    
    # =============================================
    # SECCIÓN 1: RESUMEN FINANCIERO (2 columnas)
    # =============================================
    st.markdown("---")
    st.subheader("📋 Resumen Financiero")
    st.markdown("""
    <style>
    .section-box {
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        background-color: #f9f9f9;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor principal de 2 columnas
    col_resumen1, col_resumen2 = st.columns(2)
    
    with col_resumen1:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.markdown("**💼 Capital y Movimientos**")
        
        # Fila 1 (3 KPIs)
        col1, col2, col3 = st.columns(3)
        with col1:
            styled_kpi("Capital Inicial", f"${capital_inicial_neto:,.2f}", "#E3F2FD")
        with col2:
            styled_kpi("Capital Actual", f"${capital_invertido:,.2f}", "#E3F2FD")
        with col3:
            styled_kpi("Inyección Total", f"${inyeccion_total:,.2f}", "#BBDEFB")
        
        # Fila 2 (2 KPIs)
        col4, col5 = st.columns(2)
        with col4:
            styled_kpi("Retiros Totales", f"${total_retiros:,.2f}", "#FFCDD2")
        with col5:
            styled_kpi("Comisiones", f"${comisiones:,.2f}", "#FFCDD2")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_resumen2:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.markdown("**📈 Rentabilidad**")
        
        # Fila 1 (3 KPIs)
        col6, col7, col8 = st.columns(3)
        with col6:
            styled_kpi("ROI Total", f"{roi:.2%}", "#C8E6C9")
        with col7:
            styled_kpi("CAGR", f"{cagr:.2%}", "#C8E6C9")
        with col8:
            styled_kpi("Rent. Prom.", f"{promedio_mensual_ganancias_pct:.2f}%", "#C8E6C9")
        
        # Fila 2 (2 KPIs)
        col9, col10 = st.columns(2)
        with col9:
            styled_kpi("Mejor Mes", f"{mejor_mes}", "#DCEDC8")
        with col10:
            styled_kpi("Peor Mes", f"{peor_mes}", "#FFEBEE")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # =============================================
    # SECCIÓN 2: ESTADÍSTICAS OPERATIVAS (Full width)
    # =============================================
    st.markdown("---")
    st.subheader("📊 Estadísticas Operativas")
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    
    # Fila 1 (4 KPIs)
    col11, col12, col13, col14 = st.columns(4)
    with col11:
        styled_kpi("Inversionista", inversionista, "#F5F5F5")
    with col12:
        styled_kpi("Fecha Ingreso", f"{fecha_ingreso}", "#F5F5F5")
    with col13:
        styled_kpi("Frec. Aportes", f"{frecuencia_aportes}", "#E1BEE7")
    with col14:
        styled_kpi("Frec. Retiros", f"{frecuencia_retiros}", "#D1C4E9")
    
    # Fila 2 (3 KPIs)
    col15, col16, col17 = st.columns(3)
    with col15:
        styled_kpi("Ganancia Bruta", f"${ganancia_bruta:,.2f}", "#B3E5FC")
    with col16:
        styled_kpi("Ganancia Neta", f"${ganancia_neta:,.2f}", "#B3E5FC")
    with col17:
        styled_kpi("Duración", f"{años_inversion:.1f} años", "#F5F5F5")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # =============================================
    # SECCIÓN OPCIONAL: DEBUG (solo en desarrollo)
    # =============================================
    if False:  # Cambiar a True para depuración
        st.markdown("---")
        st.subheader("🔍 Datos de Depuración")
        st.write(f"Capital inicial neto calculado: ${capital_inicial_neto:,.2f}")
        st.write(f"Período analizado: {fecha_inicio.date()} a {fecha_fin.date()}")
        st.write("Últimos 3 registros:", df[['Fecha', 'Capital Invertido']].tail(3))        # --------------------------------------------
        # PÁGINAS RESTANTES (ORIGINALES SIN MODIFICAR)
        # --------------------------------------------
        elif pagina == "📊 Gráficos":
            st.title("📊 Visualizaciones Financieras")

            df_plot = df.copy()
            df_plot["Retiros"] = df_plot["Retiro de Fondos"].fillna(0)

            fig_capital = px.bar(df_plot, x="Fecha", y="Retiros", title="Capital Invertido y Retiros", template="plotly_white")
            fig_capital.add_scatter(
                x=df_plot["Fecha"],
                y=df_plot["Capital Invertido"],
                mode='lines+markers',
                name="Capital Invertido",
                line=dict(color="blue")
            )
            st.plotly_chart(fig_capital, use_container_width=True)

            fig1 = px.line(
                df,
                x="Fecha",
                y="Ganacias/Pérdidas Netas Acumuladas",
                title="Ganancia Neta Acumulada",
                template="plotly_white"
            )
            st.plotly_chart(fig1, use_container_width=True)

            ganancia_bruta_mensual = df.groupby(df["Fecha"].dt.to_period("M"))["Ganacias/Pérdidas Brutas"].sum().reset_index()
            ganancia_bruta_mensual["Fecha"] = ganancia_bruta_mensual["Fecha"].astype(str)
            fig2 = px.bar(
                ganancia_bruta_mensual,
                x="Fecha",
                y="Ganacias/Pérdidas Brutas",
                title="Ganancia Bruta Mensual",
                template="plotly_white"
            )
            st.plotly_chart(fig2, use_container_width=True)

            comisiones_mensuales = df.groupby(df["Fecha"].dt.to_period("M"))["Comisiones 10 %"].sum().reset_index()
            comisiones_mensuales["Fecha"] = comisiones_mensuales["Fecha"].astype(str)
            fig4 = px.bar(
                comisiones_mensuales,
                x="Fecha",
                y="Comisiones 10 %",
                title="Comisiones Mensuales (10%)",
                template="plotly_white"
            )
            fig4.update_traces(hovertemplate='Fecha: %{x}<br>Comisión: %{y:.1f}')
            st.plotly_chart(fig4, use_container_width=True)

            rentabilidad = df.groupby("Mes")["Beneficio en %"].mean().reset_index()
            rentabilidad["Mes"] = rentabilidad["Mes"].astype(str)
            rentabilidad["Beneficio en %"] *= 100

            fig6 = px.bar(
                rentabilidad,
                x="Mes",
                y="Beneficio en %",
                title="Rentabilidad Mensual (%)",
                template="plotly_white"
            )
            st.plotly_chart(fig6, use_container_width=True)

        elif pagina == "📈 Proyecciones":
            st.title("📈 Proyección de Inversión Personalizada")

            capital_actual = float(df["Capital Invertido"].dropna().iloc[-1])
            aumento_opcion = st.selectbox("Selecciona porcentaje de aumento de capital", [0, 5, 10, 20, 30, 50])
            promedio_mensual_ganancias = (df["Beneficio en %"].sum(skipna=True) / len(df["Beneficio en %"]))
            
            col_kpi = st.columns(1)[0]
            with col_kpi:
                styled_kpi("📆 Promedio Mensual de Ganancias", f"{promedio_mensual_ganancias:.2%}", "#E0F7FA")

            beneficio_mensual = st.slider("Beneficio mensual estimado (%)", min_value=0.0, max_value=15.0, value=5.0, step=0.5)
            meses_proyeccion = st.slider("Duración de la inversión (meses)", min_value=1, max_value=60, value=12)

            capital_proyectado = capital_actual * (1 + aumento_opcion / 100)
            proyeccion = [capital_proyectado * ((1 + beneficio_mensual / 100) ** i) for i in range(meses_proyeccion + 1)]
            df_proy = pd.DataFrame({"Mes": list(range(meses_proyeccion + 1)), "Proyección": proyeccion})

            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                styled_kpi("💼 Capital Inicial Proyectado", f"${capital_proyectado:,.2f}", "#E8F0FE")
            with col2:
                styled_kpi("📈 Valor Estimado Final", f"${proyeccion[-1]:,.2f}", "#E6F4EA")
            with col3:
                capital_comp_anual = capital_proyectado * ((1 + beneficio_mensual / 100) ** 12)
                styled_kpi("📈 Capital Compuesto Anual", f"${capital_comp_anual:,.2f}", "#F0F4C3")

            fig = px.line(df_proy, x="Mes", y="Proyección", title="Proyección de Crecimiento de Capital", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### 📄 Detalle de Proyección (mes a mes)")
            st.dataframe(df_proy.style.format({"Proyección": "${:,.2f}"}), use_container_width=True)

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
                        capital_comp_anual
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

            comparacion_anual["Beneficio en %"] *= 100

            st.markdown("### 📊 Rentabilidad Promedio Mensual por Año")
            fig_cmp3 = px.bar(
                comparacion_anual,
                x="MesNombre",
                y="Beneficio en %",
                color="Año",
                barmode="group",
                title="Rentabilidad Promedio Mensual por Año",
                template="plotly_white"
            )
            fig_cmp3.update_traces(
                text=comparacion_anual["Beneficio en %"].round(1),
                textposition="outside",
                hovertemplate='Mes: %{x}<br>Rentabilidad: %{y:.1f}%'
            )
            fig_cmp3.update_layout(yaxis_title="Rentabilidad (%)")
            st.plotly_chart(fig_cmp3, use_container_width=True)
            st.markdown("---")

            st.markdown("### 📊 Ganancia Neta Total por Año")
            ganancia_anual = df[df['Año'].isin(años_seleccionados)].groupby("Año")["Ganacias/Pérdidas Netas"].sum().reset_index()
            fig_gan_anual = px.bar(
                ganancia_anual,
                x="Año",
                y="Ganacias/Pérdidas Netas",
                title="Ganancia Neta Total por Año",
                template="plotly_white"
            )
            fig_gan_anual.update_traces(
                texttemplate='%{y:,.2f}',
                textposition='outside',
                marker_color='green',
                hovertemplate='Año: %{x}<br>Ganancia: %{y:,.2f} USD'
            )
            fig_gan_anual.update_layout(yaxis_tickformat=",", yaxis_title="Ganancia Neta (USD)")
            st.plotly_chart(fig_gan_anual, use_container_width=True)
            st.markdown("---")

            st.markdown("### 📉 Drawdown Máximo por Año")
            drawdown_anual = df[df['Año'].isin(años_seleccionados)].groupby("Año")["Drawdown"].min().reset_index()
            fig_drawdown = px.line(
                drawdown_anual,
                x="Año",
                y="Drawdown",
                title="Drawdown Máximo por Año",
                template="plotly_white"
            )
            fig_drawdown.update_traces(
                mode="lines+markers+text",
                line_color='red',
                text=drawdown_anual["Drawdown"].round(2),
                textposition="top center",
                hovertemplate='Año: %{x}<br>Drawdown: %{y:,.2f} USD'
            )
            fig_drawdown.update_layout(yaxis_title="Drawdown ($)")
            st.plotly_chart(fig_drawdown, use_container_width=True)
            st.markdown("---")

            st.markdown("### 🔁 Cantidad de Aportes vs Retiros por Año")
            aport_retiro_anual = df[df['Año'].isin(años_seleccionados)].groupby("Año").agg({
                "Aumento Capital": lambda x: (x > 0).sum(),
                "Retiro de Fondos": lambda x: (x > 0).sum()
            }).reset_index()
            aport_retiro_anual = aport_retiro_anual.rename(columns={
                "Aumento Capital": "Aportes",
                "Retiro de Fondos": "Retiros"
            })
            fig_aportes_retiros = px.bar(
                aport_retiro_anual.melt(id_vars="Año", value_vars=["Aportes", "Retiros"]),
                x="Año",
                y="value",
                color="variable",
                barmode="group",
                title="Cantidad de Aportes vs Retiros por Año",
                template="plotly_white",
                labels={"value": "Cantidad", "variable": "Tipo"}
            )
            fig_aportes_retiros.update_traces(texttemplate='%{y}', textposition='outside')
            st.plotly_chart(fig_aportes_retiros, use_container_width=True)

            st.markdown("### 💵 Total Aportado y Retirado por Año (USD)")
            montos_aporte_retiro = df[df['Año'].isin(años_seleccionados)].groupby("Año").agg({
                "Aumento Capital": "sum",
                "Retiro de Fondos": "sum"
            }).reset_index()
            montos_aporte_retiro = montos_aporte_retiro.rename(columns={
                "Aumento Capital": "Monto Aportado",
                "Retiro de Fondos": "Monto Retirado"
            })

            fig_montos = px.bar(
                montos_aporte_retiro.melt(id_vars="Año", value_vars=["Monto Aportado", "Monto Retirado"]),
                x="Año",
                y="value",
                color="variable",
                barmode="group",
                title="Montos Aportados vs Retirados por Año",
                template="plotly_white",
                labels={"value": "USD", "variable": "Tipo"}
            )
            fig_montos.update_traces(texttemplate='%{y:,.2f}', textposition='outside')
            fig_montos.update_layout(yaxis_tickformat=",.2f", yaxis_title="Monto (USD)")
            st.plotly_chart(fig_montos, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
else:
    st.info("📂 Por favor, sube un archivo Excel desde la barra lateral para comenzar.")











    








