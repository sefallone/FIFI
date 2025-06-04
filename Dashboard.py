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

# Configuración de la página
st.set_page_config(page_title="Dashboard FIFI", layout="wide")

# Función para mostrar el logo
def mostrar_logo():
    try:
        logo = Image.open("Logo.jpg")
        st.markdown(f"""
            <div style='text-align: center;'>
                <img src='data:image/jpeg;base64,{base64.b64encode(open("Logo.jpg", "rb").read()).decode()}' 
                     style='width:200px;'/>
                <h3 style='margin-top:10px;'>Fallone Investments</h3>
            </div>
            """, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Logo no encontrado. Se mostrará sin imagen.")

# Función para KPIs comparativos
def styled_comparative_kpi(title, value_full, value_filtered, bg_color="#ffffff", text_color="#333", tooltip=""):
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
            <div style='display: flex; justify-content: space-between;'>
                <div style='flex: 1; border-right: 1px solid #eee; padding: 5px;'>
                    <div style='font-size:14px;'>Total</div>
                    <div style='font-size:24px; font-weight: bold;'>{value_full}</div>
                </div>
                <div style='flex: 1; padding: 5px;'>
                    <div style='font-size:14px;'>Período</div>
                    <div style='font-size:24px; font-weight: bold;'>{value_filtered}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Función para KPIs individuales
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

# Barra lateral para configuración
with st.sidebar:
    st.title("Configuración")
    uploaded_file = st.file_uploader("Sube el archivo Excel (.xlsx)", type=["xlsx"])

# Procesamiento principal cuando se carga un archivo
if uploaded_file:
    try:
        # Cargar y preparar los datos completos
        df_full = pd.read_excel(uploaded_file, sheet_name="Histórico")
        df_full["Fecha"] = pd.to_datetime(df_full["Fecha"], errors="coerce")
        df_full = df_full.dropna(subset=["Fecha"])
        
        # Validar columnas requeridas
        required_columns = [
            "Capital Invertido", "Aumento Capital", "Retiro de Fondos",
            "Ganacias/Pérdidas Netas", "Comisiones Pagadas", "Fecha"
        ]
        if not all(col in df_full.columns for col in required_columns):
            st.error("❌ El archivo no contiene las columnas requeridas.")
            st.stop()

        # Configurar filtros de fecha
        fecha_min = df_full["Fecha"].min().replace(day=1)
        fecha_max_original = df_full["Fecha"].max().replace(day=1)
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

            # Validar rango de fechas
            if fecha_inicio_sel < fecha_min:
                st.warning(f"⚠️ La fecha de inicio no puede ser anterior a {fecha_min.strftime('%B %Y')}.")
                st.stop()
            if fecha_fin_sel > fecha_max_limit + pd.offsets.MonthEnd(0):
                st.warning(f"⚠️ La fecha de fin no puede ser posterior a {fecha_max_limit.strftime('%B %Y')}.")
                st.stop()
            if fecha_inicio_sel > fecha_fin_sel:
                st.warning("⚠️ La fecha de inicio no puede ser mayor que la fecha final.")
                st.stop()

        # Filtrar DataFrame para el período seleccionado
        df_filtered = df_full[(df_full["Fecha"] >= fecha_inicio_sel) & (df_full["Fecha"] <= fecha_fin_sel)]
        if df_filtered.empty:
            st.warning("⚠️ No hay datos disponibles en el rango de fechas seleccionado.")
            st.stop()

        # Preprocesamiento para ambos datasets
        for df in [df_full, df_filtered]:
            df["Mes"] = df["Fecha"].dt.to_period("M")
            df["Acumulado"] = df["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
            df["MaxAcum"] = df["Acumulado"].cummax()
            df["Drawdown"] = df["Acumulado"] - df["MaxAcum"]

        # Navegación entre páginas
        pagina = st.sidebar.radio(
            "Selecciona la sección",
            ["📊 KPIs Comparativos", "📈 Evolución", "📉 Riesgo y Rendimiento", "⚙️ Configuración Avanzada"]
        )

        # --------------------------------------------
        # PÁGINA: KPIs COMPARATIVOS
        # --------------------------------------------
        if pagina == "📊 KPIs Comparativos":
            mostrar_logo()
            st.title("📊 KPIs Comparativos: Total vs Período Seleccionado")
            st.markdown("---")

            # Cálculos para todo el período histórico
            capital_inicial_full = df_full["Aumento Capital"].dropna().iloc[0] if not df_full["Aumento Capital"].dropna().empty else 0
            inyeccion_total_full = df_full["Aumento Capital"].sum(skipna=True)
            total_retiros_full = df_full["Retiro de Fondos"].sum(skipna=True)
            ganancia_neta_full = df_full["Ganacias/Pérdidas Netas"].sum(skipna=True)
            capital_final_full = df_full["Capital Invertido"].dropna().iloc[-1] if not df_full["Capital Invertido"].dropna().empty else 0
            
            capital_inicial_neto_full = capital_inicial_full + inyeccion_total_full - total_retiros_full
            roi_full = (ganancia_neta_full / capital_inicial_neto_full) if capital_inicial_neto_full > 0 else 0
            
            fecha_inicio_full = df_full["Fecha"].min()
            fecha_fin_full = df_full["Fecha"].max()
            años_inversion_full = (fecha_fin_full - fecha_inicio_full).days / 365.25
            cagr_full = ((capital_final_full / capital_inicial_neto_full) ** (1 / años_inversion_full) - 1 if años_inversion_full > 0 and capital_inicial_neto_full > 0 else 0

            # Cálculos para el período filtrado
            capital_inicial_filtered = capital_inicial_full  # Mismo capital inicial
            inyeccion_total_filtered = df_filtered["Aumento Capital"].sum(skipna=True)
            total_retiros_filtered = df_filtered["Retiro de Fondos"].sum(skipna=True)
            ganancia_neta_filtered = df_filtered["Ganacias/Pérdidas Netas"].sum(skipna=True)
            capital_final_filtered = df_filtered["Capital Invertido"].dropna().iloc[-1] if not df_filtered["Capital Invertido"].dropna().empty else 0
            
            capital_inicial_neto_filtered = capital_inicial_filtered + inyeccion_total_filtered - total_retiros_filtered
            roi_filtered = (ganancia_neta_filtered / capital_inicial_neto_filtered) if capital_inicial_neto_filtered > 0 else 0
            
            fecha_inicio_filtered = df_filtered["Fecha"].min()
            fecha_fin_filtered = df_filtered["Fecha"].max()
            años_inversion_filtered = (fecha_fin_filtered - fecha_inicio_filtered).days / 365.25
            cagr_filtered = ((capital_final_filtered / capital_inicial_neto_filtered) ** (1 / años_inversion_filtered) - 1 if años_inversion_filtered > 0 and capital_inicial_neto_filtered > 0 else 0

            # Sección 1: KPIs principales comparativos
            st.subheader("📈 Rendimiento Principal")
            col1, col2, col3 = st.columns(3)
            with col1:
                styled_comparative_kpi(
                    "ROI (Retorno)",
                    f"{roi_full:.2%}",
                    f"{roi_filtered:.2%}",
                    "#E3F2FD",
                    "Retorno sobre la inversión"
                )
            with col2:
                styled_comparative_kpi(
                    "CAGR",
                    f"{cagr_full:.2%}",
                    f"{cagr_filtered:.2%}",
                    "#E8F5E9",
                    "Tasa de crecimiento anual compuesto"
                )
            with col3:
                styled_comparative_kpi(
                    "Capital Final",
                    f"${capital_final_full:,.2f}",
                    f"${capital_final_filtered:,.2f}",
                    "#FFF3E0",
                    "Valor final del capital"
                )

            # Sección 2: Flujos de capital
            st.subheader("💰 Flujos de Capital")
            col4, col5, col6 = st.columns(3)
            with col4:
                styled_comparative_kpi(
                    "Inyección Total",
                    f"${inyeccion_total_full:,.2f}",
                    f"${inyeccion_total_filtered:,.2f}",
                    "#F1F8E9",
                    "Total aportado"
                )
            with col5:
                styled_comparative_kpi(
                    "Retiros Totales",
                    f"${total_retiros_full:,.2f}",
                    f"${total_retiros_filtered:,.2f}",
                    "#FFEBEE",
                    "Total retirado"
                )
            with col6:
                styled_comparative_kpi(
                    "Ganancia Neta",
                    f"${ganancia_neta_full:,.2f}",
                    f"${ganancia_neta_filtered:,.2f}",
                    "#E8F5E9",
                    "Ganancias después de comisiones"
                )

            # Sección 3: Métricas de eficiencia
            st.subheader("📊 Métricas de Eficiencia")
            col7, col8, col9 = st.columns(3)
            with col7:
                # Rentabilidad promedio mensual
                avg_return_full = df_full.groupby("Mes")["Beneficio en %"].mean().mean() * 100
                avg_return_filtered = df_filtered.groupby("Mes")["Beneficio en %"].mean().mean() * 100
                
                styled_comparative_kpi(
                    "Rent. Prom. Mensual",
                    f"{avg_return_full:.2f}%",
                    f"{avg_return_filtered:.2f}%",
                    "#E0F7FA",
                    "Rendimiento promedio mensual"
                )
            with col8:
                # Frecuencia de aportes
                aportes_full = (df_full["Aumento Capital"] > 0).sum()
                aportes_filtered = (df_filtered["Aumento Capital"] > 0).sum()
                
                styled_comparative_kpi(
                    "Frecuencia Aportes",
                    f"{aportes_full}",
                    f"{aportes_filtered}",
                    "#E3F2FD",
                    "Número de inyecciones"
                )
            with col9:
                # Frecuencia de retiros
                retiros_full = (df_full["Retiro de Fondos"] > 0).sum()
                retiros_filtered = (df_filtered["Retiro de Fondos"] > 0).sum()
                
                styled_comparative_kpi(
                    "Frecuencia Retiros",
                    f"{retiros_full}",
                    f"{retiros_filtered}",
                    "#FFEBEE",
                    "Número de retiros"
                )

            # Gráfico comparativo de evolución
            st.markdown("---")
            st.subheader("📊 Evolución Comparativa")
            
            # Preparar datos para el gráfico
            df_full_evolution = df_full.groupby(df_full["Fecha"].dt.to_period("M")).agg({
                "Capital Invertido": "last",
                "Ganacias/Pérdidas Netas Acumuladas": "last"
            }).reset_index()
            df_full_evolution["Tipo"] = "Histórico Completo"
            
            df_filtered_evolution = df_filtered.groupby(df_filtered["Fecha"].dt.to_period("M")).agg({
                "Capital Invertido": "last",
                "Ganacias/Pérdidas Netas Acumuladas": "last"
            }).reset_index()
            df_filtered_evolution["Tipo"] = "Período Seleccionado"
            
            df_evolution = pd.concat([df_full_evolution, df_filtered_evolution])
            df_evolution["Fecha"] = df_evolution["Fecha"].astype(str)

            # Gráfico de evolución del capital
            fig_capital = px.line(
                df_evolution, 
                x="Fecha", 
                y="Capital Invertido", 
                color="Tipo",
                title="Evolución del Capital Invertido",
                template="plotly_white",
                labels={"Capital Invertido": "Capital ($)", "Fecha": "Mes"}
            )
            st.plotly_chart(fig_capital, use_container_width=True)

            # Gráfico de ganancias acumuladas
            fig_ganancias = px.line(
                df_evolution, 
                x="Fecha", 
                y="Ganacias/Pérdidas Netas Acumuladas", 
                color="Tipo",
                title="Ganancias Netas Acumuladas",
                template="plotly_white",
                labels={"Ganacias/Pérdidas Netas Acumuladas": "Ganancias ($)", "Fecha": "Mes"}
            )
            st.plotly_chart(fig_ganancias, use_container_width=True)

        # --------------------------------------------
        # PÁGINA: RIESGO Y RENDIMIENTO
        # --------------------------------------------
        elif pagina == "📉 Riesgo y Rendimiento":
            mostrar_logo()
            st.title("📉 Análisis de Riesgo y Rendimiento")
            st.markdown("---")

            # Calcular métricas de riesgo para ambos períodos
            returns_full = df_full.groupby("Mes")["Beneficio en %"].mean()
            volatility_full = returns_full.std() * 100
            max_drawdown_full = df_full["Drawdown"].min()
            
            returns_filtered = df_filtered.groupby("Mes")["Beneficio en %"].mean()
            volatility_filtered = returns_filtered.std() * 100
            max_drawdown_filtered = df_filtered["Drawdown"].min()

            # Calcular ratio de Sharpe (simplificado)
            risk_free_rate = 0.03  # Supuesto del 3% anual
            sharpe_full = (returns_full.mean() * 12 - risk_free_rate) / (returns_full.std() * np.sqrt(12)) if returns_full.std() > 0 else 0
            sharpe_filtered = (returns_filtered.mean() * 12 - risk_free_rate) / (returns_filtered.std() * np.sqrt(12)) if returns_filtered.std() > 0 else 0

            # Sección 1: Métricas de riesgo
            st.subheader("📊 Métricas de Riesgo")
            col1, col2, col3 = st.columns(3)
            with col1:
                styled_comparative_kpi(
                    "Volatilidad",
                    f"{volatility_full:.2f}%",
                    f"{volatility_filtered:.2f}%",
                    "#FFEBEE",
                    "Desviación estándar de rendimientos"
                )
            with col2:
                styled_comparative_kpi(
                    "Máximo Drawdown",
                    f"${max_drawdown_full:,.2f}",
                    f"${max_drawdown_filtered:,.2f}",
                    "#FFCDD2",
                    "Pérdida máxima desde el pico"
                )
            with col3:
                styled_comparative_kpi(
                    "Ratio de Sharpe",
                    f"{sharpe_full:.2f}",
                    f"{sharpe_filtered:.2f}",
                    "#C8E6C9",
                    "Retorno ajustado al riesgo"
                )

            # Sección 2: Distribución de rendimientos
            st.subheader("📈 Distribución de Rendimientos")
            col4, col5 = st.columns(2)
            with col4:
                # Histograma para el período completo
                fig_hist_full = px.histogram(
                    x=returns_full * 100,
                    nbins=20,
                    title="Distribución de Rendimientos (Total)",
                    labels={"x": "Rendimiento Mensual (%)"},
                    template="plotly_white"
                )
                st.plotly_chart(fig_hist_full, use_container_width=True)
            with col5:
                # Histograma para el período filtrado
                fig_hist_filtered = px.histogram(
                    x=returns_filtered * 100,
                    nbins=20,
                    title="Distribución de Rendimientos (Período)",
                    labels={"x": "Rendimiento Mensual (%)"},
                    template="plotly_white"
                )
                st.plotly_chart(fig_hist_filtered, use_container_width=True)

            # Sección 3: Drawdowns
            st.subheader("📉 Evolución del Drawdown")
            fig_drawdown = px.line(
                df_filtered,
                x="Fecha",
                y="Drawdown",
                title="Drawdown a lo Largo del Tiempo",
                template="plotly_white",
                labels={"Drawdown": "Drawdown ($)", "Fecha": "Fecha"}
            )
            st.plotly_chart(fig_drawdown, use_container_width=True)

        # --------------------------------------------
        # PÁGINA: EVOLUCIÓN
        # --------------------------------------------
        elif pagina == "📈 Evolución":
            mostrar_logo()
            st.title("📈 Evolución Histórica")
            st.markdown("---")

            # Gráfico 1: Evolución del capital
            fig_capital = px.line(
                df_filtered,
                x="Fecha",
                y="Capital Invertido",
                title="Evolución del Capital Invertido",
                template="plotly_white"
            )
            st.plotly_chart(fig_capital, use_container_width=True)

            # Gráfico 2: Ganancias netas acumuladas
            fig_acumulado = px.line(
                df_filtered,
                x="Fecha",
                y="Ganacias/Pérdidas Netas Acumuladas",
                title="Ganancias Netas Acumuladas",
                template="plotly_white"
            )
            st.plotly_chart(fig_acumulado, use_container_width=True)

            # Gráfico 3: Rentabilidad mensual
            rentabilidad_mensual = df_filtered.groupby("Mes")["Beneficio en %"].mean().reset_index()
            rentabilidad_mensual["Mes"] = rentabilidad_mensual["Mes"].astype(str)
            rentabilidad_mensual["Beneficio en %"] *= 100

            fig_rentabilidad = px.bar(
                rentabilidad_mensual,
                x="Mes",
                y="Beneficio en %",
                title="Rentabilidad Mensual (%)",
                template="plotly_white"
            )
            st.plotly_chart(fig_rentabilidad, use_container_width=True)

            # Gráfico 4: Comisiones mensuales
            comisiones_mensuales = df_filtered.groupby("Mes")["Comisiones Pagadas"].sum().reset_index()
            comisiones_mensuales["Mes"] = comisiones_mensuales["Mes"].astype(str)
            fig_comisiones = px.bar(
                comisiones_mensuales,
                x="Mes",
                y="Comisiones Pagadas",
                title="Comisiones Mensuales",
                template="plotly_white"
            )
            st.plotly_chart(fig_comisiones, use_container_width=True)

        # --------------------------------------------
        # PÁGINA: CONFIGURACIÓN AVANZADA
        # --------------------------------------------
        elif pagina == "⚙️ Configuración Avanzada":
            mostrar_logo()
            st.title("⚙️ Configuración Avanzada")
            st.markdown("---")

            # Configuración de proyecciones
            st.subheader("📈 Parámetros de Proyección")
            capital_actual = float(df_filtered["Capital Invertido"].dropna().iloc[-1])
            
            col1, col2 = st.columns(2)
            with col1:
                aumento_opcion = st.selectbox(
                    "Aumento de capital inicial (%)",
                    [0, 5, 10, 20, 30, 50],
                    index=0
                )
            with col2:
                beneficio_mensual = st.slider(
                    "Beneficio mensual estimado (%)",
                    0.0, 15.0, 5.0, 0.5
                )
            
            meses_proyeccion = st.slider(
                "Horizonte de proyección (meses)",
                1, 60, 12
            )

            # Cálculos de proyección
            capital_proyectado = capital_actual * (1 + aumento_opcion / 100)
            proyeccion = [capital_proyectado * ((1 + beneficio_mensual / 100) ** i) for i in range(meses_proyeccion + 1)]
            
            # Mostrar resultados
            st.subheader("📊 Resultados de Proyección")
            col3, col4 = st.columns(2)
            with col3:
                styled_kpi("Capital Inicial", f"${capital_proyectado:,.2f}", "#E3F2FD")
            with col4:
                styled_kpi("Valor Final", f"${proyeccion[-1]:,.2f}", "#E8F5E9")

            # Gráfico de proyección
            fig_proy = px.line(
                x=range(meses_proyeccion + 1),
                y=proyeccion,
                title="Proyección de Crecimiento de Capital",
                labels={"x": "Meses", "y": "Capital ($)"},
                template="plotly_white"
            )
            st.plotly_chart(fig_proy, use_container_width=True)

            # Exportar datos
            st.subheader("📤 Exportar Datos")
            if st.button("Generar Reporte en Excel"):
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Hoja de resumen
                    resumen = pd.DataFrame({
                        "Métrica": [
                            "Capital Actual",
                            "Aumento de Capital (%)",
                            "Capital Proyectado",
                            "Beneficio Mensual Estimado (%)",
                            "Horizonte (meses)",
                            "Valor Final Proyectado"
                        ],
                        "Valor": [
                            f"${capital_actual:,.2f}",
                            f"{aumento_opcion}%",
                            f"${capital_proyectado:,.2f}",
                            f"{beneficio_mensual}%",
                            meses_proyeccion,
                            f"${proyeccion[-1]:,.2f}"
                        ]
                    })
                    resumen.to_excel(writer, sheet_name="Resumen", index=False)
                    
                    # Hoja de proyección detallada
                    proyeccion_df = pd.DataFrame({
                        "Mes": range(meses_proyeccion + 1),
                        "Capital": proyeccion
                    })
                    proyeccion_df.to_excel(writer, sheet_name="Proyección", index=False)
                    
                    # Hoja con datos filtrados
                    df_filtered.to_excel(writer, sheet_name="Datos Filtrados", index=False)
                
                excel_data = output.getvalue()
                st.download_button(
                    label="📥 Descargar Reporte Completo",
                    data=excel_data,
                    file_name="reporte_financiero.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
else:
    mostrar_logo()
    st.info("📂 Por favor, sube un archivo Excel desde la barra lateral para comenzar.")





