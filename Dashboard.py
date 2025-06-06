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

# ==============================================
# CONFIGURACIÓN GENERAL MEJORADA
# ==============================================
st.set_page_config(
    page_title="Dashboard FIFI Pro",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# ==============================================
# ESTILOS AVANZADOS
# ==============================================
st.markdown("""
    <style>
    /* Main Theme */
    :root {
        --primary: #1a3a8f;
        --secondary: #0d1b3e;
        --success: #27ae60;
        --danger: #e74c3c;
        --warning: #f39c12;
        --info: #3498db;
        --light: #f8f9fa;
        --dark: #343a40;
    }
    
    /* Improved KPI Cards */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.05);
        border-left: 5px solid var(--primary);
        transition: all 0.3s ease;
        margin-bottom: 20px;
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .kpi-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 5px;
        background: linear-gradient(90deg, var(--primary), #4a90e2);
    }
    .kpi-title {
        font-size: 16px;
        font-weight: 600;
        color: #7f8c8d;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: var(--dark);
    }
    .positive {
        color: var(--success) !important;
    }
    .negative {
        color: var(--danger) !important;
    }
    .kpi-delta {
        font-size: 14px;
        margin-top: 8px;
        font-weight: 500;
    }
    
    /* Improved Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--primary) 0%, var(--secondary) 100%);
    }
    [data-testid="stSidebar"] .st-eb {
        color: white !important;
    }
    
    /* Better Charts Container */
    .stPlotlyChart {
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
        background: white;
        padding: 15px;
    }
    
    /* Improved Tabs */
    .st-bd {
        border-bottom: 2px solid var(--primary) !important;
    }
    .st-at {
        background-color: var(--primary) !important;
    }
    
    /* Logo Header */
    .logo-header {
        text-align: center;
        margin-bottom: 30px;
    }
    .logo-header h1 {
        color: var(--primary);
        margin-bottom: 5px;
    }
    .logo-header p {
        color: #7f8c8d;
        font-size: 16px;
    }
    
    /* Responsive Grid */
    @media (max-width: 768px) {
        .kpi-card {
            padding: 15px;
        }
        .kpi-value {
            font-size: 22px;
        }
    }
    </style>
""", unsafe_allow_html=True)

# Configuración de gráficos Plotly
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = ["#1a3a8f", "#27ae60", "#e74c3c", "#f39c12", "#3498db"]
px.defaults.width = None

# ==============================================
# COMPONENTES REUTILIZABLES
# ==============================================
def styled_kpi(title, value, bg_color="#ffffff", text_color="#333", tooltip="", icon=""):
            full_title = f"{icon} {title}" if icon else title
            return f"""
                <div title="{tooltip}" style="
                    background-color: {bg_color};
                    color: {text_color};
                    padding: 20px;
                    border-radius: 15px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    text-align: center;
                    margin-bottom: 15px;">
                    <div style='font-size:18px; font-weight: 600;'>{full_title}</div>
                    <div style='font-size:28px; font-weight: bold;'>{value}</div>
                </div>
            """

def create_profit_chart(df):
    fig = px.line(
        df,
        x="Fecha",
        y="Ganacias/Pérdidas Netas Acumuladas",
        title="<b>Ganancia Neta Acumulada</b>",
        labels={"Ganacias/Pérdidas Netas Acumuladas": "Ganancia Acumulada (USD)"},
        hover_data={"Fecha": "|%B %d, %Y"},
        height=500
    )
    
    fig.update_layout(
        hovermode="x unified",
        xaxis_title=None,
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    fig.update_traces(
        line_width=3,
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>$%{y:,.2f}"
    )
    
    return fig

def create_excel_report(df, kpis):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Raw data sheet
        df.to_excel(writer, sheet_name='Datos Históricos', index=False)
        
        # KPIs sheet
        kpi_df = pd.DataFrame.from_dict(kpis, orient='index', columns=['Valor'])
        kpi_df.to_excel(writer, sheet_name='Indicadores Clave')
        
        # Charts sheet
        workbook = writer.book
        worksheet = workbook.add_worksheet('Resumen Visual')
        
        # Add some basic charts to Excel
        chart = workbook.add_chart({'type': 'line'})
        chart.add_series({
            'name': 'Ganancias',
            'categories': 'Datos Históricos!$B$2:$B${}'.format(len(df)+1),
            'values': 'Datos Históricos!$E$2:$E${}'.format(len(df)+1),
        })
        worksheet.insert_chart('B2', chart)
    
    return output.getvalue()

def calcular_kpis_globales(df, df_completo):
    """Calcula todos los KPIs y los devuelve como diccionario"""
    # Cálculo de KPIs
    capital_inicial = df_completo["Aumento Capital"].dropna().iloc[0] if not df_completo["Aumento Capital"].dropna().empty else 0
    inyeccion_total = df["Aumento Capital"].sum(skipna=True)
    capital_invertido = df["Capital Invertido"].dropna().iloc[-1] if not df["Capital Invertido"].dropna().empty else 0
    inversionista = df["ID Inv"].dropna().iloc[0] if "ID Inv" in df.columns and not df["ID Inv"].dropna().empty else "N/A"
    total_retiros = df["Retiro de Fondos"].sum(skipna=True)
    ganancia_bruta = df["Ganacias/Pérdidas Brutas"].sum(skipna=True)
    ganancia_neta = df["Ganacias/Pérdidas Netas"].sum(skipna=True)
    comisiones = df["Comisiones Pagadas"].sum(skipna=True)
    fecha_ingreso = df_completo["Fecha"].min().date()

    # ROI y CAGR
    capital_inicial_neto = capital_inicial + inyeccion_total - total_retiros
    roi = (ganancia_neta / capital_inicial_neto) if capital_inicial_neto > 0 else 0
    
    fecha_inicio = df["Fecha"].min()
    fecha_fin = df["Fecha"].max()
    años_inversion = (fecha_fin - fecha_inicio).days / 365.25
    cagr = ((capital_invertido / capital_inicial_neto) ** (1 / años_inversion) - 1) if años_inversion > 0 and capital_inicial_neto > 0 else 0

    # KPIs de rendimiento adicionales
    sharpe_ratio = ganancia_neta / (df["Beneficio en %"].std() * np.sqrt(12)) if len(df) > 1 else 0
    max_drawdown = df["Drawdown"].min()
    win_rate = (df["Beneficio en %"] > 0).mean()
    promedio_mensual_ganancias_pct = df.groupby("Mes")["Beneficio en %"].mean().mean() * 100
    frecuencia_aportes = df[df["Aumento Capital"] > 0].shape[0]
    frecuencia_retiros = df[df["Retiro de Fondos"] > 0].shape[0]
    mejor_mes = df.loc[df["Beneficio en %"].idxmax()]["Mes"]
    peor_mes = df.loc[df["Beneficio en %"].idxmin()]["Mes"]

    return {
        "Inversionista": inversionista,
        "Capital Inicial": capital_inicial,
        "Capital Actual": capital_invertido,
        "Inyección Total": inyeccion_total,
        "Retiros Totales": total_retiros,
        "Ganancia Bruta": ganancia_bruta,
        "Ganancia Neta": ganancia_neta,
        "Comisiones": comisiones,
        "Fecha Ingreso": fecha_ingreso,
        "ROI": roi,
        "CAGR": cagr,
        "Sharpe Ratio": sharpe_ratio,
        "Máx Drawdown": max_drawdown,
        "Win Rate": win_rate,
        "Promedio Mensual (%)": promedio_mensual_ganancias_pct,
        "Frecuencia Aportes": frecuencia_aportes,
        "Frecuencia Retiros": frecuencia_retiros,
        "Mejor Mes": str(mejor_mes),
        "Peor Mes": str(peor_mes)
    }

# ==============================================
# INTERFAZ PRINCIPAL
# ==============================================
# Logo en página principal
try:
    logo = Image.open("Logo.jpg")
    st.markdown("""
        <div class="logo-header">
            <img src='data:image/jpeg;base64,{}' style='width:200px;'/>
            <h1>Fallone Investments</h1>
            <p>Dashboard de Performance Financiera</p>
        </div>
        """.format(base64.b64encode(open("Logo.jpg", "rb").read()).decode()), unsafe_allow_html=True)
except FileNotFoundError:
    st.markdown("""
        <div class="logo-header">
            <h1>Fallone Investments</h1>
            <p>Dashboard de Performance Financiera</p>
        </div>
    """, unsafe_allow_html=True)

# Sidebar config
with st.sidebar:
    st.title("⚙️ Configuración")
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

        # Configuración mejorada de filtros de fecha
        with st.sidebar:
            st.markdown("### 🗓️ Filtro de Fechas")
            
            # Get min/max dates from data
            min_date = df_completo["Fecha"].min().date()
            max_date = (df_completo["Fecha"].max() - pd.DateOffset(months=1)).date()
            
            # Create date range slider
            date_range = st.date_input(
                "Seleccione rango de fechas",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                format="YYYY/MM/DD"
            )
            
            # Validate selection
            if len(date_range) != 2:
                st.warning("Por favor seleccione un rango completo de fechas")
                st.stop()
            
            start_date, end_date = date_range
            if start_date > end_date:
                st.warning("La fecha de inicio no puede ser mayor que la fecha final")
                st.stop()

        # Filtrar DataFrame
        df = df_completo[
            (df_completo["Fecha"].dt.date >= start_date) & 
            (df_completo["Fecha"].dt.date <= end_date)
        ].copy()
        
        if df.empty:
            st.warning("⚠️ No hay datos disponibles en el rango de fechas seleccionado.")
            st.stop()

        # Preprocesamiento adicional
        df["Mes"] = df["Fecha"].dt.to_period("M")
        df["Acumulado"] = df["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
        df["MaxAcum"] = df["Acumulado"].cummax()
        df["Drawdown"] = df["Acumulado"] - df["MaxAcum"]
        df['Año'] = df['Fecha'].dt.year
        df['MesNombre'] = df['Fecha'].dt.strftime('%b')
        df['MesOrden'] = df['Fecha'].dt.month

        # Calcular KPIs globales (para usar en todas las páginas)
        kpis_globales = calcular_kpis_globales(df, df_completo)

        # Navegación entre páginas
        pagina = st.sidebar.radio("Secciones", 
                                ["📌 KPIs", "📊 Gráficos", "📈 Proyecciones", "⚖️ Comparaciones", "📊 Reportes"])

        # ==============================================
        # PÁGINA: KPIs
        # ==============================================
        if pagina == "📌 KPIs":
            st.title("📌 Indicadores Clave de Desempeño")
            st.markdown("---")

            # Layout de KPIs mejorado
            col1, col2, col3, col4 = st.columns(4)
            with col1: 
                styled_kpi("👤 Inversionista", f"{kpis_globales['Inversionista']}", 
                         icon="person", help_text="Identificador único del inversionista")
            with col2: 
                styled_kpi("💰 Capital Inicial", f"${kpis_globales['Capital Inicial']:,.2f}", 
                         icon="account_balance", help_text="Primer aporte realizado")
            with col3: 
                styled_kpi("💼 Capital Actual", f"${kpis_globales['Capital Actual']:,.2f}", 
                         icon="show_chart", help_text="Valor actual del capital invertido")
            with col4: 
                styled_kpi("📥 Inyección Total", f"${kpis_globales['Inyección Total']:,.2f}", 
                         icon="savings", help_text="Total de aportes realizados")

            col5, col6, col7, col8 = st.columns(4)
            with col5: 
                styled_kpi("📤 Retiros Totales", f"${kpis_globales['Retiros Totales']:,.2f}", 
                         icon="money_off", help_text="Total retirado durante el período")
            with col6: 
                styled_kpi("📊 Ganancia Bruta", f"${kpis_globales['Ganancia Bruta']:,.2f}", 
                         delta=f"{(kpis_globales['Ganancia Bruta']/(kpis_globales['Capital Inicial'] + kpis_globales['Inyección Total'] - kpis_globales['Retiros Totales'])):.1%} del capital" if (kpis_globales['Capital Inicial'] + kpis_globales['Inyección Total'] - kpis_globales['Retiros Totales']) > 0 else None,
                         icon="trending_up", help_text="Ganancias antes de comisiones")
            with col7: 
                styled_kpi("📈 Ganancia Neta", f"${kpis_globales['Ganancia Neta']:,.2f}", 
                         delta=f"{(kpis_globales['Ganancia Neta']/(kpis_globales['Capital Inicial'] + kpis_globales['Inyección Total'] - kpis_globales['Retiros Totales'])):.1%} del capital" if (kpis_globales['Capital Inicial'] + kpis_globales['Inyección Total'] - kpis_globales['Retiros Totales']) > 0 else None,
                         icon="bar_chart", help_text="Ganancias después de comisiones")
            with col8: 
                styled_kpi("🧾 Comisiones", f"${kpis_globales['Comisiones']:,.2f}", 
                         delta=f"{(kpis_globales['Comisiones']/kpis_globales['Ganancia Bruta']):.1%} de ganancias" if kpis_globales['Ganancia Bruta'] > 0 else None,
                         icon="receipt", help_text="Total pagado en comisiones")

            st.markdown("---")
            
            # Sección de métricas de rendimiento
            st.markdown("### 📊 Métricas de Rendimiento")
            col9, col10, col11 = st.columns(3)
            with col9: 
                styled_kpi("📅 Fecha Ingreso", f"{kpis_globales['Fecha Ingreso']}", 
                         icon="event", help_text="Fecha del primer aporte")
            with col10: 
                styled_kpi("📊 ROI Total", f"{kpis_globales['ROI']:.1%}", 
                         delta=f"${kpis_globales['Ganancia Neta']:,.0f} absolutos",
                         icon="donut_large", help_text="Retorno sobre la inversión total")
            with col11: 
                styled_kpi("📈 CAGR Anual", f"{kpis_globales['CAGR']:.1%}", 
                         icon="timeline", help_text="Tasa de crecimiento anual compuesta")

            col12, col13, col14 = st.columns(3)
            with col12: 
                styled_kpi("⚖️ Sharpe Ratio", f"{kpis_globales['Sharpe Ratio']:.2f}", 
                         icon="balance", help_text="Rendimiento ajustado al riesgo")
            with col13: 
                styled_kpi("📉 Máx Drawdown", f"${kpis_globales['Máx Drawdown']:,.0f}", 
                         icon="waterfall_chart", help_text="Peor pérdida desde el máximo")
            with col14: 
                styled_kpi("✅ Win Rate", f"{kpis_globales['Win Rate']:.0%}", 
                         icon="check_circle", help_text="Porcentaje de meses positivos")

            st.markdown("---")
            
            # Sección de estadísticas mensuales
            st.markdown("### 📅 Estadísticas Mensuales")
            col15, col16, col17 = st.columns(3)
            with col15: 
                styled_kpi("📈 Prom. Mensual", f"{kpis_globales['Promedio Mensual (%)']:.1f}%", 
                         icon="calendar_today", help_text="Rentabilidad promedio mensual")
            with col16: 
                styled_kpi("🔁 Aportes", f"{kpis_globales['Frecuencia Aportes']}", 
                         delta=f"${kpis_globales['Inyección Total']/kpis_globales['Frecuencia Aportes']:,.0f} c/u" if kpis_globales['Frecuencia Aportes'] > 0 else None,
                         icon="repeat", help_text="Frecuencia de aportes")
            with col17: 
                styled_kpi("📤 Retiros", f"{kpis_globales['Frecuencia Retiros']}", 
                         delta=f"${kpis_globales['Retiros Totales']/kpis_globales['Frecuencia Retiros']:,.0f} c/u" if kpis_globales['Frecuencia Retiros'] > 0 else None,
                         icon="exit_to_app", help_text="Frecuencia de retiros")

            col18, col19 = st.columns(2)
            with col18: 
                styled_kpi("🏆 Mejor Mes", f"{kpis_globales['Mejor Mes']}", 
                         delta=f"{df['Beneficio en %'].max()*100:.1f}%",
                         icon="emoji_events", help_text="Mes con mayor rentabilidad")
            with col19: 
                styled_kpi("⚠️ Peor Mes", f"{kpis_globales['Peor Mes']}", 
                         delta=f"{df['Beneficio en %'].min()*100:.1f}%",
                         icon="warning", help_text="Mes con menor rentabilidad")

        # ==============================================
        # PÁGINA: GRÁFICOS
        # ==============================================
        elif pagina == "📊 Gráficos":
            st.title("📊 Visualizaciones Financieras")
            st.markdown("---")

            df_plot = df.copy()
            df_plot["Retiros"] = df_plot["Retiro de Fondos"].fillna(0)

            # Gráfico mejorado de capital invertido
            st.markdown("### 📈 Evolución del Capital")
            fig_capital = px.bar(
                df_plot, 
                x="Fecha", 
                y="Retiros", 
                title="<b>Capital Invertido vs Retiros</b>",
                labels={"Retiros": "Retiros (USD)"}
            )
            fig_capital.add_scatter(
                x=df_plot["Fecha"],
                y=df_plot["Capital Invertido"],
                mode='lines+markers',
                name="Capital Invertido",
                line=dict(color="#1a3a8f", width=3)
            )
            fig_capital.update_layout(
                hovermode="x unified",
                yaxis_tickprefix="$",
                yaxis_tickformat=",.0f",
                plot_bgcolor="rgba(0,0,0,0)",
                height=500
            )
            st.plotly_chart(fig_capital, use_container_width=True)

            # Gráfico mejorado de ganancias acumuladas
            st.markdown("### 📊 Ganancias Acumuladas")
            fig1 = create_profit_chart(df)
            st.plotly_chart(fig1, use_container_width=True)

            # Gráfico de ganancia bruta mensual
            st.markdown("### 💰 Ganancias Brutas Mensuales")
            ganancia_bruta_mensual = df.groupby(df["Fecha"].dt.to_period("M"))["Ganacias/Pérdidas Brutas"].sum().reset_index()
            ganancia_bruta_mensual["Fecha"] = ganancia_bruta_mensual["Fecha"].astype(str)
            fig2 = px.bar(
                ganancia_bruta_mensual,
                x="Fecha",
                y="Ganacias/Pérdidas Brutas",
                title="<b>Ganancia Bruta Mensual</b>",
                labels={"Ganacias/Pérdidas Brutas": "Ganancia Bruta (USD)"}
            )
            fig2.update_traces(
                marker_color="#27ae60",
                hovertemplate='Mes: %{x}<br>Ganancia: $%{y:,.0f}'
            )
            fig2.update_layout(
                yaxis_tickprefix="$",
                yaxis_tickformat=",.0f"
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Gráfico de comisiones
            st.markdown("### 💸 Comisiones Mensuales")
            comisiones_mensuales = df.groupby(df["Fecha"].dt.to_period("M"))["Comisiones 10 %"].sum().reset_index()
            comisiones_mensuales["Fecha"] = comisiones_mensuales["Fecha"].astype(str)
            fig4 = px.bar(
                comisiones_mensuales,
                x="Fecha",
                y="Comisiones 10 %",
                title="<b>Comisiones Mensuales (10%)</b>",
                labels={"Comisiones 10 %": "Comisiones (USD)"}
            )
            fig4.update_traces(
                marker_color="#e74c3c",
                hovertemplate='Mes: %{x}<br>Comisión: $%{y:,.0f}'
            )
            fig4.update_layout(
                yaxis_tickprefix="$",
                yaxis_tickformat=",.0f"
            )
            st.plotly_chart(fig4, use_container_width=True)

            # Gráfico de rentabilidad mensual
            st.markdown("### 📉 Rentabilidad Mensual (%)")
            rentabilidad = df.groupby("Mes")["Beneficio en %"].mean().reset_index()
            rentabilidad["Mes"] = rentabilidad["Mes"].astype(str)
            rentabilidad["Beneficio en %"] *= 100

            fig6 = px.bar(
                rentabilidad,
                x="Mes",
                y="Beneficio en %",
                title="<b>Rentabilidad Mensual</b>",
                labels={"Beneficio en %": "Rentabilidad (%)"},
                color_discrete_sequence=["#1a3a8f"]
            )
            fig6.update_traces(
                hovertemplate='Mes: %{x}<br>Rentabilidad: %{y:.1f}%'
            )
            fig6.update_layout(
                yaxis_ticksuffix="%"
            )
            st.plotly_chart(fig6, use_container_width=True)

        # ==============================================
        # PÁGINA: PROYECCIONES
        # ==============================================
        elif pagina == "📈 Proyecciones":
            st.title("📈 Proyección de Inversión")
            st.markdown("---")

            capital_actual = float(df["Capital Invertido"].dropna().iloc[-1])
            
            # Configuración de proyección
            col_config1, col_config2 = st.columns(2)
            with col_config1:
                aumento_opcion = st.selectbox(
                    "Porcentaje de aumento de capital", 
                    [0, 5, 10, 20, 30, 50],
                    format_func=lambda x: f"{x}%"
                )
            with col_config2:
                styled_kpi("📆 Promedio Histórico", f"{kpis_globales['Promedio Mensual (%)']:.1f}%",
                         help_text="Rentabilidad mensual promedio histórica")

            # Configuración avanzada
            with st.expander("⚙️ Configuración Avanzada"):
                col_adv1, col_adv2 = st.columns(2)
                with col_adv1:
                    beneficio_mensual = st.slider(
                        "Beneficio mensual estimado (%)", 
                        min_value=0.0, 
                        max_value=15.0, 
                        value=float(kpis_globales['Promedio Mensual (%)']), 
                        step=0.5
                    )
                with col_adv2:
                    meses_proyeccion = st.slider(
                        "Duración (meses)", 
                        min_value=1, 
                        max_value=60, 
                        value=12
                    )
                
                # Opción de aportes mensuales adicionales
                aporte_mensual = st.number_input(
                    "Aporte mensual adicional ($)", 
                    min_value=0, 
                    value=0,
                    help="Aportes regulares que se sumarán cada mes"
                )

            # Cálculo de proyección
            capital_proyectado = capital_actual * (1 + aumento_opcion / 100)
            proyeccion = [capital_proyectado]
            
            for i in range(1, meses_proyeccion + 1):
                nuevo_valor = proyeccion[i-1] * (1 + beneficio_mensual / 100) + aporte_mensual
                proyeccion.append(nuevo_valor)
                
            df_proy = pd.DataFrame({
                "Mes": list(range(meses_proyeccion + 1)),
                "Proyección": proyeccion,
                "Aportes Adicionales": [0] + [aporte_mensual] * meses_proyeccion
            })

            # KPIs de proyección
            st.markdown("---")
            st.markdown("### 📊 Resumen de Proyección")
            col_proy1, col_proy2, col_proy3 = st.columns(3)
            with col_proy1:
                styled_kpi("💼 Capital Inicial", f"${capital_proyectado:,.2f}", 
                         icon="account_balance_wallet", help_text="Capital inicial proyectado")
            with col_proy2:
                styled_kpi("📈 Valor Final", f"${proyeccion[-1]:,.2f}", 
                         delta=f"{(proyeccion[-1]/capital_proyectado-1):.1%} total",
                         icon="show_chart", help_text="Valor proyectado al final del período")
            with col_proy3:
                ganancia_total = proyeccion[-1] - capital_proyectado - (aporte_mensual * meses_proyeccion)
                styled_kpi("💰 Ganancia Neta", f"${ganancia_total:,.2f}", 
                         delta=f"{(ganancia_total/capital_proyectado):.1%} del capital",
                         icon="attach_money", help_text="Ganancias netas proyectadas")

            # Gráfico de proyección
            st.markdown("---")
            st.markdown("### 📈 Trayectoria Proyectada")
            fig_proy = px.line(
                df_proy,
                x="Mes",
                y="Proyección",
                title="<b>Proyección de Crecimiento de Capital</b>",
                labels={"Proyección": "Valor del Capital (USD)"}
            )
            
            if aporte_mensual > 0:
                fig_proy.add_bar(
                    x=df_proy["Mes"],
                    y=df_proy["Aportes Adicionales"],
                    name="Aportes Adicionales",
                    marker_color="#3498db"
                )
            
            fig_proy.update_layout(
                hovermode="x unified",
                yaxis_tickprefix="$",
                yaxis_tickformat=",.0f",
                height=500
            )
            fig_proy.update_traces(
                line=dict(width=3, color="#1a3a8f"),
                hovertemplate="Mes %{x}<br>$%{y:,.0f}"
            )
            st.plotly_chart(fig_proy, use_container_width=True)

            # Tabla de proyección detallada
            st.markdown("---")
            st.markdown("### 📄 Detalle Mensual")
            df_proy_display = df_proy.copy()
            df_proy_display["Ganancia Mensual"] = df_proy_display["Proyección"].pct_change() * 100
            df_proy_display["Ganancia Acumulada"] = (df_proy_display["Proyección"] / capital_proyectado - 1) * 100
            
            st.dataframe(
                df_proy_display.style.format({
                    "Proyección": "${:,.2f}",
                    "Aportes Adicionales": "${:,.2f}",
                    "Ganancia Mensual": "{:.2f}%",
                    "Ganancia Acumulada": "{:.2f}%"
                }),
                use_container_width=True
            )

            # Exportar proyección
            st.markdown("---")
            st.markdown("### 📤 Exportar Proyección")
            excel_proy = create_excel_report(
                df_proy_display,
                {
                    "Capital Actual": capital_actual,
                    "Aumento Capital": f"{aumento_opcion}%",
                    "Capital Proyectado": capital_proyectado,
                    "Beneficio Mensual": f"{beneficio_mensual}%",
                    "Meses Proyección": meses_proyeccion,
                    "Valor Final": proyeccion[-1],
                    "Ganancia Neta": ganancia_total
                }
            )
            
            st.download_button(
                "📥 Descargar Proyección Completa",
                data=excel_proy,
                file_name="proyeccion_inversion.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # ==============================================
        # PÁGINA: COMPARACIONES
        # ==============================================
        elif pagina == "⚖️ Comparaciones":
            st.title("⚖️ Comparaciones por Año")
            st.markdown("---")

            años_disponibles = sorted(df['Año'].dropna().unique().tolist())
            años_seleccionados = st.multiselect(
                "Selecciona los años a comparar", 
                años_disponibles, 
                default=años_disponibles[-2:] if len(años_disponibles) >= 2 else años_disponibles
            )

            if not años_seleccionados:
                st.warning("Selecciona al menos un año para comparar")
                st.stop()

            comparacion_anual = df[df['Año'].isin(años_seleccionados)].groupby(
                ['Año', 'MesNombre', 'MesOrden']
            ).agg({
                "Ganacias/Pérdidas Brutas": "sum",
                "Ganacias/Pérdidas Netas": "sum",
                "Comisiones Pagadas": "sum",
                "Beneficio en %": "mean"
            }).reset_index().sort_values("MesOrden")

            comparacion_anual["Beneficio en %"] *= 100

            # Orden correcto de meses en español
            orden_meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                           "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
            comparacion_anual["MesNombre"] = pd.Categorical(
                comparacion_anual["MesNombre"], categories=orden_meses, ordered=True
            )

            # ========== Gráfico 1: Rentabilidad mensual comparada ==========
            st.subheader("📊 Rentabilidad Promedio Mensual por Año")
            fig_cmp1 = px.bar(
                comparacion_anual,
                x="MesNombre",
                y="Beneficio en %",
                color="Año",
                barmode="group",
                labels={"Beneficio en %": "Rentabilidad (%)"},
                category_orders={"MesNombre": orden_meses},
                title="<b>Rentabilidad Promedio Mensual</b>",
                height=500
            )
            fig_cmp1.update_traces(
                text=comparacion_anual["Beneficio en %"].round(1),
                textposition="outside",
                hovertemplate="Año: %{color}<br>Mes: %{x}<br>Rentabilidad: %{y:.1f}%"
            )
            fig_cmp1.update_layout(yaxis_ticksuffix="%")
            st.plotly_chart(fig_cmp1, use_container_width=True)

            # ========== Gráfico 2: Ganancia Neta Mensual ==========
            st.subheader("📈 Ganancia Neta Mensual Comparada")
            fig_cmp2 = px.bar(
                comparacion_anual,
                x="MesNombre",
                y="Ganacias/Pérdidas Netas",
                color="Año",
                barmode="group",
                labels={"Ganacias/Pérdidas Netas": "Ganancia Neta (USD)"},
                category_orders={"MesNombre": orden_meses},
                title="<b>Ganancia Neta por Mes</b>",
                height=500
            )
            fig_cmp2.update_traces(
                text=comparacion_anual["Ganacias/Pérdidas Netas"].round(0),
                textposition="outside",
                hovertemplate="Año: %{color}<br>Mes: %{x}<br>Ganancia: $%{y:,.0f}"
            )
            fig_cmp2.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",.0f")
            st.plotly_chart(fig_cmp2, use_container_width=True)

            # ========== Gráfico 3: Comisiones Mensuales ==========
            st.subheader("💸 Comisiones Mensuales Comparadas")
            fig_cmp3 = px.bar(
                comparacion_anual,
                x="MesNombre",
                y="Comisiones Pagadas",
                color="Año",
                barmode="group",
                labels={"Comisiones Pagadas": "Comisiones (USD)"},
                category_orders={"MesNombre": orden_meses},
                title="<b>Comisiones por Mes</b>",
                height=500
            )
            fig_cmp3.update_traces(
                text=comparacion_anual["Comisiones Pagadas"].round(0),
                textposition="outside",
                hovertemplate="Año: %{color}<br>Mes: %{x}<br>Comisión: $%{y:,.0f}"
            )
            fig_cmp3.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",.0f")
            st.plotly_chart(fig_cmp3, use_container_width=True)

            # ========== Gráfico 4: Ganancia Neta Anual ==========
            st.subheader("📊 Ganancia Neta Anual Total")
            ganancia_anual = df[df['Año'].isin(años_seleccionados)].groupby("Año")["Ganacias/Pérdidas Netas"].sum().reset_index()
            fig_cmp4 = px.bar(
                ganancia_anual,
                x="Año",
                y="Ganacias/Pérdidas Netas",
                title="<b>Ganancia Neta Total por Año</b>",
                labels={"Ganacias/Pérdidas Netas": "Ganancia Neta (USD)"},
                height=500,
                color="Año",
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_cmp4.update_traces(
                texttemplate="$%{y:,.0f}",
                textposition="outside",
                hovertemplate="Año: %{x}<br>Ganancia: $%{y:,.0f}"
            )
            fig_cmp4.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",.0f", showlegend=False)
            st.plotly_chart(fig_cmp4, use_container_width=True)

        # ==============================================
        # PÁGINA: REPORTES
        # ==============================================
        elif pagina == "📊 Reportes":
            st.title("📊 Reportes y Exportaciones")
            st.markdown("Visualiza y descarga los datos utilizados en el dashboard.")

            st.markdown("### 🧾 Datos Filtrados")
            st.dataframe(df, use_container_width=True)

            # Descargar datos en Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Datos Filtrados', index=False)
            excel_data = output.getvalue()

            st.download_button(
                label="📥 Descargar Datos Filtrados en Excel",
                data=excel_data,
                file_name="datos_filtrados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Exportar KPIs
            st.markdown("### 📌 Exportar KPIs (Resumen Básico)")
            kpi_df = pd.DataFrame(kpis_globales.items(), columns=["Indicador", "Valor"])

            output_kpi = BytesIO()
            with pd.ExcelWriter(output_kpi, engine='xlsxwriter') as writer:
                kpi_df.to_excel(writer, sheet_name="KPIs", index=False)

            st.download_button(
                label="📥 Descargar KPIs en Excel",
                data=output_kpi.getvalue(),
                file_name="kpis_resumen.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
else:
    st.info("📂 Por favor, sube un archivo Excel desde la barra lateral para comenzar.")
