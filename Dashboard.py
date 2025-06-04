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

# Configuración general con modo oscuro opcional
st.set_page_config(
    page_title="Dashboard FIFI",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# CSS personalizado con modo oscuro
st.markdown("""
    <style>
    /* Configuración base */
    :root {
        --primary: #1a3a8f;
        --secondary: #0d1b3e;
        --text: #2c3e50;
        --text-light: #7f8c8d;
        --positive: #27ae60;
        --negative: #e74c3c;
        --bg: #ffffff;
        --card-bg: #ffffff;
        --sidebar-bg: linear-gradient(180deg, var(--primary) 0%, var(--secondary) 100%);
        --border: 1px solid rgba(0,0,0,0.1);
        --shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Modo oscuro */
    @media (prefers-color-scheme: dark) {
        :root {
            --text: #ecf0f1;
            --text-light: #bdc3c7;
            --bg: #121212;
            --card-bg: #1e1e1e;
            --sidebar-bg: linear-gradient(180deg, #0d1b3e 0%, #050a16 100%);
            --border: 1px solid rgba(255,255,255,0.1);
            --shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        }
    }
    
    /* Estructura base */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: var(--text);
        background-color: var(--bg);
    }
    
    /* Sidebar profesional */
    [data-testid="stSidebar"] {
        background: var(--sidebar-bg);
        color: white;
    }
    [data-testid="stSidebar"] .st-eb {
        color: white !important;
    }
    [data-testid="stSidebar"] .st-cb {
        background-color: rgba(255,255,255,0.1);
    }
    
    /* Tarjetas KPIs profesionales con animación */
    .kpi-card {
        background: var(--card-bg);
        border-radius: 10px;
        padding: 20px;
        box-shadow: var(--shadow);
        border-left: 4px solid var(--primary);
        margin-bottom: 15px;
        transition: all 0.3s ease;
        border: var(--border);
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .kpi-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-light);
        margin-bottom: 5px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .kpi-value {
        font-size: 24px;
        font-weight: 700;
        color: var(--text);
    }
    .positive {
        color: var(--positive) !important;
    }
    .negative {
        color: var(--negative) !important;
    }
    
    /* Títulos de sección */
    h1, h2, h3 {
        color: var(--primary);
        border-bottom: 2px solid rgba(0,0,0,0.1);
        padding-bottom: 10px;
        margin-top: 1.5rem;
    }
    @media (prefers-color-scheme: dark) {
        h1, h2, h3 {
            border-bottom: 2px solid rgba(255,255,255,0.1);
        }
    }
    
    /* Filtros en sidebar */
    .stSelectbox, .stSlider, .stRadio {
        margin-bottom: 15px;
    }
    
    /* Gráficos con animación de carga */
    .stPlotlyChart {
        border-radius: 10px;
        box-shadow: var(--shadow);
        border: var(--border);
        transition: opacity 0.5s ease;
        opacity: 0;
        animation: fadeIn 0.5s ease forwards;
    }
    @keyframes fadeIn {
        to { opacity: 1; }
    }
    
    /* Logo header con animación sutil */
    .logo-header {
        text-align: center;
        margin-bottom: 30px;
        animation: slideDown 0.7s ease;
    }
    @keyframes slideDown {
        from { transform: translateY(-20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    
    /* Tooltips personalizados */
    [data-testid="stTooltip"] {
        background: var(--card-bg) !important;
        color: var(--text) !important;
        border: var(--border) !important;
        box-shadow: var(--shadow) !important;
        border-radius: 8px !important;
    }
    
    /* Transición para cambios de datos */
    .element-container {
        transition: all 0.3s ease;
    }
    
    /* Mejoras para tabs */
    [data-testid="stHorizontalBlock"] {
        gap: 1rem;
    }
    
    /* Botones con estilo profesional */
    .stButton button {
        background-color: var(--primary) !important;
        color: white !important;
        border-radius: 8px !important;
        transition: all 0.2s !important;
    }
    .stButton button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }
    </style>
    """, unsafe_allow_html=True)

# Logo en página principal con animación
st.markdown("""
    <div class="logo-header">
        <h1 style='color:var(--primary);margin-bottom:5px;'>Fallone Investments</h1>
        <p style='color:var(--text-light);font-size:16px;'>Dashboard de Performance Financiera</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar config
with st.sidebar:
    st.title("Configuración")
    st.markdown("---")
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

        # Función para KPIs estilizados (versión profesional)
        def styled_kpi(title, value, icon=None, delta=None, tooltip=""):
            color_class = ""
            if isinstance(value, str):
                if "%" in value and "-" not in value:
                    color_class = "positive"
                elif "%" in value and "-" in value:
                    color_class = "negative"
            elif isinstance(value, (int, float)):
                if value >= 0 and "Retiro" not in title and "Comisión" not in title:
                    color_class = "positive"
                else:
                    color_class = "negative"
            
            icon_html = f"<span style='font-size:20px;'>{icon}</span>" if icon else ""
            delta_html = f"<div style='font-size:14px;color:var(--text-light);margin-top:5px;'>{delta}</div>" if delta else ""
            
            st.markdown(f"""
                <div title="{tooltip}" class="kpi-card">
                    <div class="kpi-title">
                        {icon_html}
                        {title}
                    </div>
                    <div class="kpi-value {color_class}">{value}</div>
                    {delta_html}
                </div>
            """, unsafe_allow_html=True)

        # Navegación entre páginas con estilo mejorado
        st.sidebar.markdown("---")
        pagina = st.sidebar.radio("Selecciona la sección", 
                                ["📌 KPIs", "📊 Gráficos", "📈 Proyecciones", "⚖️ Comparaciones"],
                                label_visibility="collapsed")

        # --------------------------------------------
        # PÁGINA: KPIs (versión profesional)
        # --------------------------------------------
        if pagina == "📌 KPIs":
            st.title("📌 Indicadores Clave de Desempeño")
            st.markdown("---")

            # CAPITAL INICIAL: Primer valor histórico (sin filtrar)
            capital_inicial = df_completo["Aumento Capital"].dropna().iloc[0] if not df_completo["Aumento Capital"].dropna().empty else 0
            
            # INYECCIÓN TOTAL: Suma de aportes en el período filtrado
            inyeccion_total = df["Aumento Capital"].sum(skipna=True)
            
            # Resto de KPIs con datos filtrados
            capital_invertido = df["Capital Invertido"].dropna().iloc[-1] if not df["Capital Invertido"].dropna().empty else 0
            inversionista = df["ID Inv"].dropna().iloc[0] if "ID Inv" in df.columns and not df["ID Inv"].dropna().empty else "N/A"
            total_retiros = df["Retiro de Fondos"].sum(skipna=True)
            ganancia_bruta = df["Ganacias/Pérdidas Brutas"].sum(skipna=True)
            ganancia_neta = df["Ganacias/Pérdidas Netas"].sum(skipna=True)
            comisiones = df["Comisiones Pagadas"].sum(skipna=True)
            fecha_ingreso = df_completo["Fecha"].min().date()

            # ROI y CAGR con los cambios solicitados
            capital_inicial_neto = capital_inicial + inyeccion_total - total_retiros
            roi = (ganancia_neta / capital_inicial_neto) if capital_inicial_neto > 0 else 0
            
            fecha_inicio = df["Fecha"].min()
            fecha_fin = df["Fecha"].max()
            años_inversion = (fecha_fin - fecha_inicio).days / 365.25
            cagr = ((capital_invertido / capital_inicial_neto) ** (1 / años_inversion) - 1) if años_inversion > 0 and capital_inicial_neto > 0 else 0

            # Layout de KPIs profesional
            col1, col2, col3, col4 = st.columns(4)
            with col1: 
                styled_kpi("Inversionista", f"{inversionista}", "👤", "ID único")
            with col2: 
                styled_kpi("Capital Inicial", f"${capital_inicial:,.2f}", "💰", "Primer aporte")
            with col3: 
                styled_kpi("Capital Actual", f"${capital_invertido:,.2f}", "💼", "Valor actual")
            with col4: 
                styled_kpi("Inyección Total", f"${inyeccion_total:,.2f}", "📥", "Aportes totales")

            col5, col6, col7, col8 = st.columns(4)
            with col5: 
                styled_kpi("Retiros", f"${total_retiros:,.2f}", "📤", "Total retirado")
            with col6: 
                styled_kpi("Ganancia Bruta", f"${ganancia_bruta:,.2f}", "📊", "Antes de comisiones")
            with col7: 
                styled_kpi("Ganancia Neta", f"${ganancia_neta:,.2f}", "📈", "Después de comisiones")
            with col8: 
                styled_kpi("Comisiones", f"${comisiones:,.2f}", "🧾", "Total pagado")

            col9, col10, col11 = st.columns(3)
            with col9: 
                styled_kpi("Fecha Ingreso", f"{fecha_ingreso}", "📅", "Inicio de operaciones")
            with col10: 
                styled_kpi("ROI Total", f"{roi:.2%}", "📊", "Retorno sobre inversión")
            with col11: 
                styled_kpi("CAGR Mensual", f"{cagr:.2%}", "📈", "Tasa anual compuesta")

            st.markdown("---")
            
            # KPIs adicionales con estilo profesional
            promedio_mensual_ganancias_pct = df.groupby("Mes")["Beneficio en %"].mean().mean() * 100
            styled_kpi("Rentabilidad Promedio", f"{promedio_mensual_ganancias_pct:.2f}%", "📈", 
                      "Media mensual", "Rendimiento promedio mensual en porcentaje")

            col12, col13, col14 = st.columns(3)
            with col12:
                frecuencia_aportes = df[df["Aumento Capital"] > 0].shape[0]
                styled_kpi("Frecuencia Aportes", f"{frecuencia_aportes}", "🔄", 
                          "Total operaciones", "Número de veces que se realizaron aportes")
            with col13:
                frecuencia_retiros = df[df["Retiro de Fondos"] > 0].shape[0]
                styled_kpi("Frecuencia Retiros", f"{frecuencia_retiros}", "📥", 
                          "Total operaciones", "Número de veces que se retiraron fondos")
            with col14:
                mejor_mes = df.loc[df["Beneficio en %"].idxmax()]["Mes"]
                styled_kpi("Mejor Mes", f"{mejor_mes}", "🚀", 
                          "Máximo rendimiento", "Mes con el mejor porcentaje de beneficio")

            col15 = st.columns(1)[0]
            with col15:
                peor_mes = df.loc[df["Beneficio en %"].idxmin()]["Mes"]
                styled_kpi("Peor Mes", f"{peor_mes}", "⚠️", 
                          "Mínimo rendimiento", "Mes con el peor porcentaje de beneficio")

        # --------------------------------------------
        # PÁGINAS RESTANTES (CON ESTILO PROFESIONAL)
        # --------------------------------------------
        elif pagina == "📊 Gráficos":
            st.title("📊 Visualizaciones Financieras")
            st.markdown("---")

            df_plot = df.copy()
            df_plot["Retiros"] = df_plot["Retiro de Fondos"].fillna(0)

            with st.expander("📌 Capital Invertido vs Retiros", expanded=True):
                fig_capital = px.bar(df_plot, x="Fecha", y="Retiros", 
                                    title="Capital Invertido y Retiros", 
                                    template="plotly_white")
                fig_capital.add_scatter(
                    x=df_plot["Fecha"],
                    y=df_plot["Capital Invertido"],
                    mode='lines+markers',
                    name="Capital Invertido",
                    line=dict(color="#1a3a8f")
                )
                fig_capital.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    hovermode="x unified"
                )
                st.plotly_chart(fig_capital, use_container_width=True)

            with st.expander("📈 Ganancia Neta Acumulada", expanded=True):
                fig1 = px.line(
                    df,
                    x="Fecha",
                    y="Ganacias/Pérdidas Netas Acumuladas",
                    title="Ganancia Neta Acumulada",
                    template="plotly_white"
                )
                fig1.update_traces(line_color="#27ae60")
                fig1.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    hovermode="x unified"
                )
                st.plotly_chart(fig1, use_container_width=True)

            with st.expander("📊 Rentabilidad Mensual", expanded=True):
                rentabilidad = df.groupby("Mes")["Beneficio en %"].mean().reset_index()
                rentabilidad["Mes"] = rentabilidad["Mes"].astype(str)
                rentabilidad["Beneficio en %"] *= 100

                fig6 = px.bar(
                    rentabilidad,
                    x="Mes",
                    y="Beneficio en %",
                    title="Rentabilidad Mensual (%)",
                    template="plotly_white",
                    color_discrete_sequence=["#1a3a8f"]
                )
                fig6.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    hovermode="x unified",
                    yaxis_title="Rentabilidad (%)"
                )
                st.plotly_chart(fig6, use_container_width=True)

        elif pagina == "📈 Proyecciones":
            st.title("📈 Proyección de Inversión")
            st.markdown("---")

            capital_actual = float(df["Capital Invertido"].dropna().iloc[-1])
            
            col_config1, col_config2 = st.columns(2)
            with col_config1:
                aumento_opcion = st.selectbox("Porcentaje de aumento de capital", 
                                           [0, 5, 10, 20, 30, 50],
                                           help="Selecciona el porcentaje de aumento sobre el capital actual")
            with col_config2:
                promedio_mensual_ganancias = (df["Beneficio en %"].sum(skipna=True) / len(df["Beneficio en %"]))
                styled_kpi("Rentabilidad Histórica", f"{promedio_mensual_ganancias:.2%}", "📊", 
                          "Promedio mensual", "Rentabilidad promedio histórica")

            col_slider1, col_slider2 = st.columns(2)
            with col_slider1:
                beneficio_mensual = st.slider("Beneficio mensual estimado (%)", 
                                            min_value=0.0, max_value=15.0, 
                                            value=5.0, step=0.5,
                                            help="Proyección de rendimiento mensual esperado")
            with col_slider2:
                meses_proyeccion = st.slider("Duración de la inversión (meses)", 
                                           min_value=1, max_value=60, value=12,
                                           help="Período de tiempo para la proyección")

            capital_proyectado = capital_actual * (1 + aumento_opcion / 100)
            proyeccion = [capital_proyectado * ((1 + beneficio_mensual / 100) ** i) for i in range(meses_proyeccion + 1)]
            df_proy = pd.DataFrame({"Mes": list(range(meses_proyeccion + 1)), "Proyección": proyeccion})

            st.markdown("---")
            col_resumen1, col_resumen2, col_resumen3 = st.columns(3)
            with col_resumen1:
                styled_kpi("Capital Inicial", f"${capital_proyectado:,.2f}", "💰", 
                          f"{aumento_opcion}% sobre actual", "Capital inicial proyectado")
            with col_resumen2:
                styled_kpi("Valor Final", f"${proyeccion[-1]:,.2f}", "📈", 
                          f"{((proyeccion[-1]/capital_proyectado-1)*100:.1f}% total", "Valor estimado al final del período")
            with col_resumen3:
                capital_comp_anual = capital_proyectado * ((1 + beneficio_mensual / 100) ** 12)
                styled_kpi("Proyección Anual", f"${capital_comp_anual:,.2f}", "📅", 
                          f"{((capital_comp_anual/capital_proyectado-1)*100):.1f}%", "Valor estimado a 12 meses")

            with st.expander("📊 Gráfico de Proyección", expanded=True):
                fig = px.line(df_proy, x="Mes", y="Proyección", 
                             title="Proyección de Crecimiento de Capital", 
                             template="plotly_white")
                fig.update_traces(line_color="#1a3a8f", mode="lines+markers")
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    hovermode="x unified",
                    yaxis_title="Valor Proyectado (USD)"
                )
                st.plotly_chart(fig, use_container_width=True)

            with st.expander("📄 Detalle Mes a Mes", expanded=False):
                st.dataframe(df_proy.style.format({"Proyección": "${:,.2f}"}), 
                            use_container_width=True,
                            height=300)

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
            st.download_button("📥 Descargar Proyección Completa", 
                              data=excel_data, 
                              file_name="proyeccion_fallone.xlsx", 
                              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              help="Descargar el detalle completo de la proyección en formato Excel")

        elif pagina == "⚖️ Comparaciones":
            st.title("⚖️ Comparaciones por Año")
            st.markdown("---")

            df['Año'] = df['Fecha'].dt.year
            df['MesNombre'] = df['Fecha'].dt.strftime('%b')
            df['MesOrden'] = df['Fecha'].dt.month

            años_disponibles = df['Año'].dropna().unique().tolist()
            años_seleccionados = st.multiselect("Selecciona los años a comparar", 
                                              sorted(años_disponibles), 
                                              default=sorted(años_disponibles),
                                              help="Selecciona uno o más años para comparar")

            comparacion_anual = df[df['Año'].isin(años_seleccionados)].groupby(['Año', 'MesNombre', 'MesOrden']).agg({
                "Ganacias/Pérdidas Brutas": "sum",
                "Ganacias/Pérdidas Netas": "sum",
                "Comisiones Pagadas": "sum",
                "Beneficio en %": "mean"
            }).reset_index().sort_values("MesOrden")

            comparacion_anual["Beneficio en %"] *= 100

            with st.expander("📊 Rentabilidad Mensual por Año", expanded=True):
                fig_cmp3 = px.bar(
                    comparacion_anual,
                    x="MesNombre",
                    y="Beneficio en %",
                    color="Año",
                    barmode="group",
                    title="Rentabilidad Mensual por Año (%)",
                    template="plotly_white",
                    color_discrete_sequence=px.colors.qualitative.Prism
                )
                fig_cmp3.update_traces(
                    text=comparacion_anual["Beneficio en %"].round(1),
                    textposition="outside",
                    hovertemplate='Mes: %{x}<br>Rentabilidad: %{y:.1f}%<br>Año: %{customdata}',
                    customdata=comparacion_anual["Año"]
                )
                fig_cmp3.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    hovermode="x unified",
                    yaxis_title="Rentabilidad (%)",
                    xaxis_title="Mes"
                )
                st.plotly_chart(fig_cmp3, use_container_width=True)

            with st.expander("📈 Ganancia Neta Anual", expanded=True):
                ganancia_anual = df[df['Año'].isin(años_seleccionados)].groupby("Año")["Ganacias/Pérdidas Netas"].sum().reset_index()
                fig_gan_anual = px.bar(
                    ganancia_anual,
                    x="Año",
                    y="Ganacias/Pérdidas Netas",
                    title="Ganancia Neta por Año (USD)",
                    template="plotly_white",
                    color="Año",
                    color_discrete_sequence=px.colors.qualitative.Prism
                )
                fig_gan_anual.update_traces(
                    texttemplate='%{y:,.2f}',
                    textposition='outside',
                    hovertemplate='Año: %{x}<br>Ganancia: %{y:,.2f} USD'
                )
                fig_gan_anual.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    hovermode="x unified",
                    yaxis_tickformat=",",
                    yaxis_title="Ganancia Neta (USD)",
                    showlegend=False
                )
                st.plotly_chart(fig_gan_anual, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
else:
    st.info("📂 Por favor, sube un archivo Excel desde la barra lateral para comenzar.")

