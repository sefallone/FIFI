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
            # 1. PRIMERO CALCULAR TODAS LAS VARIABLES NECESARIAS
            # =============================================
            
            # Cálculos para el HISTÓRICO COMPLETO (df_completo)
            capital_inicial_historico = df_completo["Aumento Capital"].dropna().iloc[0] if not df_completo["Aumento Capital"].dropna().empty else 0
            capital_invertido_historico = df_completo["Capital Invertido"].ffill().iloc[-1]
            inyeccion_total_historico = df_completo["Aumento Capital"].sum()
            total_retiros_historico = df_completo["Retiro de Fondos"].sum()
            ganancia_bruta_historico = df_completo["Ganacias/Pérdidas Brutas"].sum()
            ganancia_neta_historico = df_completo["Ganacias/Pérdidas Netas"].sum()
            comisiones_historico = df_completo["Comisiones Pagadas"].sum()
            
            # Rentabilidad histórica
            roi_historico = (ganancia_neta_historico / capital_inicial_historico) if capital_inicial_historico > 0 else 0
            años_total = (df_completo["Fecha"].max() - df_completo["Fecha"].min()).days / 365.25
            cagr_historico = ((capital_invertido_historico / capital_inicial_historico) ** (1 / años_total) - 1) if años_total > 0 else 0
            
            # Estadísticas adicionales históricas
            frecuencia_aportes_historico = df_completo[df_completo["Aumento Capital"] > 0].shape[0]
            frecuencia_retiros_historico = df_completo[df_completo["Retiro de Fondos"] > 0].shape[0]
            mejor_mes_historico = df_completo.loc[df_completo["Beneficio en %"].idxmax()]["Mes"] if "Beneficio en %" in df_completo.columns else "N/A"
            peor_mes_historico = df_completo.loc[df_completo["Beneficio en %"].idxmin()]["Mes"] if "Beneficio en %" in df_completo.columns else "N/A"
            promedio_rentabilidad_historico = df_completo["Beneficio en %"].mean() * 100 if "Beneficio en %" in df_completo.columns else 0
            
            # Cálculos para el PERÍODO FILTRADO (df)
            capital_invertido_filtrado = df.loc[df['Fecha'].idxmax(), 'Capital Invertido'] if not df.empty else 0
            capital_inicial_neto = (
                df_completo[df_completo['Fecha'] < fecha_inicio_sel]['Aumento Capital'].sum() - 
                df_completo[df_completo['Fecha'] < fecha_inicio_sel]['Retiro de Fondos'].sum()
            ) or capital_inicial_historico  # Fallback al capital inicial histórico
            
            inyeccion_total_filtrado = df["Aumento Capital"].sum()
            total_retiros_filtrado = df["Retiro de Fondos"].sum()
            ganancia_bruta_filtrado = df["Ganacias/Pérdidas Brutas"].sum()
            ganancia_neta_filtrado = df["Ganacias/Pérdidas Netas"].sum()
            comisiones_filtrado = df["Comisiones Pagadas"].sum()
            
            # Rentabilidad del período filtrado
            roi_filtrado = (ganancia_neta_filtrado / capital_inicial_neto) if capital_inicial_neto > 0 else 0
            años_filtrado = (df['Fecha'].max() - df['Fecha'].min()).days / 365.25
            cagr_filtrado = ((capital_invertido_filtrado / capital_inicial_neto) ** (1 / años_filtrado) - 1) if años_filtrado > 0 else 0
            
            # Estadísticas adicionales del período filtrado
            frecuencia_aportes_filtrado = df[df["Aumento Capital"] > 0].shape[0]
            frecuencia_retiros_filtrado = df[df["Retiro de Fondos"] > 0].shape[0]
            mejor_mes_filtrado = df.loc[df["Beneficio en %"].idxmax()]["Mes"] if "Beneficio en %" in df.columns else "N/A"
            peor_mes_filtrado = df.loc[df["Beneficio en %"].idxmin()]["Mes"] if "Beneficio en %" in df.columns else "N/A"
            promedio_rentabilidad_filtrado = df["Beneficio en %"].mean() * 100 if "Beneficio en %" in df.columns else 0
        
            # =============================================
            # 2. AHORA MOSTRAR LAS SECCIONES VISUALES
            # =============================================
            
            # Estilos CSS personalizados (los mismos que antes)
            st.markdown("""
            <style>
            .header-box {
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .historic-section {
                border-left: 5px solid #3f51b5;
                padding-left: 15px;
                margin: 20px 0;
                background-color: #f8f9fa;
                border-radius: 0 8px 8px 0;
            }
            .filtered-section {
                border-left: 5px solid #4caf50;
                padding-left: 15px;
                margin: 20px 0;
                background-color: #f1f8e9;
                border-radius: 0 8px 8px 0;
            }
            .kpi-card {
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 15px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            </style>
            """, unsafe_allow_html=True)
        
            # SECCIÓN HISTÓRICA
            with st.container():
                st.markdown('<div class="header-box"><h2 style="margin:0; color:#3f51b5;">📜 Histórico Completo</h2></div>', unsafe_allow_html=True)
                
                with st.markdown('<div class="historic-section">', unsafe_allow_html=True):
                    cols = st.columns(4)
                    with cols[0]:
                        st.markdown('<div class="kpi-card" style="background-color:#e3f2fd;">', unsafe_allow_html=True)
                        st.metric("Capital Inicial", f"${capital_inicial_historico:,.2f}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with cols[1]:
                        st.markdown('<div class="kpi-card" style="background-color:#e8f5e9;">', unsafe_allow_html=True)
                        st.metric("Capital Actual", f"${capital_invertido_historico:,.2f}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    # ... (continuar con el resto de KPIs históricos)
        
            # SECCIÓN FILTRADA
            with st.container():
                st.markdown(f'<div class="header-box"><h2 style="margin:0; color:#4caf50;">🔍 Período Seleccionado ({fecha_inicio_sel.date()} a {fecha_fin_sel.date()})</h2></div>', unsafe_allow_html=True)
                
                with st.markdown('<div class="filtered-section">', unsafe_allow_html=True):
                    cols = st.columns(4)
                    with cols[0]:
                        st.markdown('<div class="kpi-card" style="background-color:#e3f2fd;">', unsafe_allow_html=True)
                        st.metric("Capital Inicial Neto", f"${capital_inicial_neto:,.2f}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    with cols[1]:
                        st.markdown('<div class="kpi-card" style="background-color:#e8f5e9;">', unsafe_allow_html=True)
                        st.metric("Capital Final", f"${capital_invertido_filtrado:,.2f}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    # ... (continuar con el resto de KPIs filtrados)
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











    








