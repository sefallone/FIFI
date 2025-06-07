# 1. IMPORTACIONES
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

# 2. CONFIGURACIÓN INICIAL DE LA PÁGINA
st.set_page_config(
    page_title="Dashboard FIFI Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "### Fallone Investments\nDashboard de seguimiento financiero profesional"
    }
)

# 3. ESTILOS CSS AVANZADOS
st.markdown("""
<style>
    /* Fuentes profesionales */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #2c3e50;
    }
    
    /* Cards de KPIs modernos */
    .kpi-card {
        background: white;
        border-radius: 10px;
        padding: 18px 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 4px solid #3498db;
        transition: all 0.3s ease;
        margin-bottom: 15px;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    
    /* Sidebar elegante */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50, #1a252f);
    }
    [data-testid="stSidebar"] .st-eb {
        color: white !important;
    }
    
    /* Contenedores de gráficos */
    .stPlotlyChart {
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        background: white;
        padding: 15px;
    }
    
    /* Títulos mejorados */
    h1, h2, h3 {
        color: #2c3e50 !important;
    }
    
    /* Logo header */
    .logo-header {
        text-align: center;
        margin-bottom: 30px;
    }
    .logo-header img {
        width: 180px;
        border-radius: 50%;
        border: 4px solid #3498db;
        padding: 5px;
        background: white;
    }
</style>
""", unsafe_allow_html=True)

# 4. FUNCIÓN PARA KPIs ESTILIZADOS (MEJORADA)
def styled_kpi(title, value, delta=None, delta_color="auto", icon=None, help_text=None):
    """
    Versión mejorada con formato consistente para valores delta
    """
    # Mapeo de iconos a emojis
    icon_map = {
        "person": "👤", "account_balance": "💰", "show_chart": "📈",
        # ... (todos tus iconos existentes)
    }
    
    display_icon = icon_map.get(icon, "") if icon else ""

    # Configuración de colores
    color_classes = {
        "positive": "#27ae60",  # Verde
        "negative": "#e74c3c",  # Rojo
        "neutral": "#2c3e50"    # Azul oscuro
    }

    # Formateo del valor principal
    if isinstance(value, (int, float)):
        value_str = f"${value:,.2f}" if abs(value) >= 1000 else f"${value:.2f}"
    else:
        value_str = str(value)

    # Manejo del delta (parte crítica mejorada)
    delta_html = ""
    if delta is not None:
        # Formateo consistente del valor delta
        if isinstance(delta, (int, float)):
            delta_value = f"{delta:.1f}%"  # Formato fijo con 1 decimal y signo %
        else:
            delta_value = str(delta)

        # Color automático basado en el valor
        if delta_color == "auto":
            delta_color = "positive" if (isinstance(delta, (int, float)) and delta >= 0) else "negative"

        delta_color_hex = color_classes[delta_color.lower()]
        
        delta_html = f"""
        <div style="
            color: {delta_color_hex};
            font-size: 14px;
            margin-top: 6px;
            font-weight: 500;
            text-align: center;
        ">
            {delta_value}
        </div>
        """

    # HTML final
    html = f"""
    <div title="{help_text or ''}" class="kpi-card">
        <div style="
            display: flex;
            align-items: center;
            font-size: 16px;
            font-weight: 600;
            color: #7f8c8d;
            margin-bottom: 8px;
        ">
            <span style="margin-right: 8px; font-size: 1.2em;">{display_icon}</span>
            {title}
        </div>
        <div style="
            font-size: 26px;
            font-weight: 700;
            color: {color_classes['neutral']};
            text-align: center;
        ">
            {value_str}
        </div>
        {delta_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
# 5. FUNCIÓN PARA GRÁFICO DE GANANCIAS (MEJORADA)
def create_profit_chart(df):
    """Gráfico profesional de ganancias acumuladas con drawdown"""
    fig = px.area(
        df,
        x="Fecha",
        y="Acumulado",
        title="<b>Ganancias Acumuladas</b>",
        labels={"Acumulado": "Ganancia Acumulada (USD)"},
        template="plotly_white"
    )
    
    # Línea de máximo acumulado
    fig.add_scatter(
        x=df["Fecha"],
        y=df["MaxAcum"],
        mode='lines',
        name="Máximo Histórico",
        line=dict(color="#e74c3c", width=2, dash='dot')
    )
    
    # Configuración del layout
    fig.update_layout(
        hovermode="x unified",
        yaxis_tickprefix="$",
        height=450,
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Configuración de trazas
    fig.update_traces(
        line=dict(width=3, color="#27ae60"),
        hovertemplate="<b>%{x|%d/%m/%Y}</b><br>$%{y:,.2f}<extra></extra>"
    )
    
    return fig

# 6. INTERFAZ PRINCIPAL - LOGO
try:
    logo = Image.open("Logo.jpg")
    st.markdown(f"""
    <div class="logo-header">
        <img src='data:image/jpeg;base64,{base64.b64encode(open("Logo.jpg", "rb").read()).decode()}'/>
        <h3 style='margin-top:10px; color: #2c3e50;'>Fallone Investments</h3>
        <p style='color: #7f8c8d;'>Dashboard de Performance Financiera</p>
    </div>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    st.markdown("""
    <div class="logo-header">
        <div style='width:180px; height:180px; border-radius: 50%; border: 4px solid #3498db; 
                    margin: 0 auto; display: flex; align-items: center; justify-content: center; 
                    background: #f8f9fa;'>
            <span style='font-size: 60px;'>📊</span>
        </div>
        <h3 style='margin-top:10px; color: #2c3e50;'>Fallone Investments</h3>
        <p style='color: #7f8c8d;'>Dashboard de Performance Financiera</p>
    </div>
    """, unsafe_allow_html=True)

# 7. SIDEBAR CONFIGURABLE
with st.sidebar:
    st.title("⚙️ Configuración")
    
    # Uploader de archivo
    with st.expander("📂 Cargar Datos", expanded=True):
        uploaded_file = st.file_uploader("Subir archivo Excel (.xlsx)", type=["xlsx"])
    
    if uploaded_file:
        try:
            # Carga de datos
            df_completo = pd.read_excel(uploaded_file, sheet_name="Histórico")
            df_completo["Fecha"] = pd.to_datetime(df_completo["Fecha"], errors="coerce")
            df_completo = df_completo.dropna(subset=["Fecha"])
            
            # Validación de columnas
            required_columns = ["Capital Invertido", "Aumento Capital", "Retiro de Fondos", 
                              "Ganacias/Pérdidas Netas", "Comisiones Pagadas", "Fecha"]
            if not all(col in df_completo.columns for col in required_columns):
                st.error("❌ El archivo no contiene las columnas requeridas.")
                st.stop()
            
            # Filtros de fecha
            fecha_min = df_completo["Fecha"].min().replace(day=1)
            fecha_max_original = df_completo["Fecha"].max().replace(day=1)
            fecha_max_limit = fecha_max_original - pd.DateOffset(months=1)
            
            años_disponibles = list(range(fecha_min.year, fecha_max_limit.year + 1))
            meses_disponibles = list(range(1, 13))
            
            with st.expander("📅 Filtros de Fecha", expanded=True):
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
                
                # Validación de fechas
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
            
            # Navegación
            st.markdown("---")
            st.markdown("**Secciones**")
            pagina = st.radio("", 
                            ["📌 KPIs", "📊 Gráficos", "📈 Proyecciones", "⚖️ Comparaciones"], 
                            label_visibility="collapsed")
            
            # Filtrar DataFrame
            df = df_completo[
                (df_completo["Fecha"] >= fecha_inicio_sel) & 
                (df_completo["Fecha"] <= fecha_fin_sel)
            ].copy()
            
            if df.empty:
                st.warning("⚠️ No hay datos disponibles en el rango de fechas seleccionado.")
                st.stop()
            
            # Preprocesamiento
            df["Mes"] = df["Fecha"].dt.to_period("M")
            df["Acumulado"] = df["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
            df["MaxAcum"] = df["Acumulado"].cummax()
            df["Drawdown"] = df["Acumulado"] - df["MaxAcum"]
            
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {str(e)}")
            st.stop()

# 8. PÁGINA DE KPIs (MEJORADA)
if uploaded_file and pagina == "📌 KPIs":
    st.title("📊 Indicadores Clave de Desempeño")
    st.markdown("---")
    
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
    
    # KPIs de rendimiento
    sharpe_ratio = ganancia_neta / (df["Beneficio en %"].std() * np.sqrt(12)) if len(df) > 1 else 0
    max_drawdown = df["Drawdown"].min()
    win_rate = (df["Beneficio en %"] > 0).mean()
    promedio_mensual_ganancias_pct = df.groupby("Mes")["Beneficio en %"].mean().mean() * 100
    frecuencia_aportes = df[df["Aumento Capital"] > 0].shape[0]
    frecuencia_retiros = df[df["Retiro de Fondos"] > 0].shape[0]
    mejor_mes = df.loc[df["Beneficio en %"].idxmax()]["Mes"]
    peor_mes = df.loc[df["Beneficio en %"].idxmin()]["Mes"]
    
    # Layout de KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1: 
        styled_kpi("Inversionista", f"{inversionista}", icon="person")
    with col2: 
        styled_kpi("Capital Inicial", f"${capital_inicial:,.2f}", icon="account_balance")
    with col3: 
        styled_kpi("Capital Actual", f"${capital_invertido:,.2f}", icon="show_chart")
    with col4: 
        styled_kpi("Inyección Total", f"${inyeccion_total:,.2f}", icon="savings")
    
    col5, col6, col7, col8 = st.columns(4)
    with col5: 
        styled_kpi("Retiros Totales", f"${total_retiros:,.2f}", icon="money_off")
    with col6: 
        styled_kpi("Ganancia Bruta", f"${ganancia_bruta:,.2f}", 
                  delta=f"{(ganancia_bruta/(capital_inicial + inyeccion_total - total_retiros)):.1%} del capital" if (capital_inicial + inyeccion_total - total_retiros) > 0 else None,
                  icon="trending_up")
    with col7: 
        styled_kpi("Ganancia Neta", f"${ganancia_neta:,.2f}", 
                  delta=f"{(ganancia_neta/(capital_inicial + inyeccion_total - total_retiros)):.1%} del capital" if (capital_inicial + inyeccion_total - total_retiros) > 0 else None,
                  icon="bar_chart")
    with col8: 
        styled_kpi("Comisiones", f"${comisiones:,.2f}", 
                  delta=f"{(comisiones/ganancia_bruta):.1%} de ganancias" if ganancia_bruta > 0 else None,
                  icon="receipt")
    
    st.markdown("---")
    st.markdown("### 📈 Rendimiento")
    col9, col10, col11 = st.columns(3)
    with col9: 
        styled_kpi("Fecha Ingreso", f"{fecha_ingreso}", icon="event")
    with col10: 
        styled_kpi("ROI Total", f"{roi:.2%}", 
                  delta=f"${ganancia_neta:,.0f} absolutos",
                  icon="donut_large")
    with col11: 
        styled_kpi("CAGR Anual", f"{cagr:.2%}", icon="timeline")
    
    col12, col13, col14 = st.columns(3)
    with col12: 
        styled_kpi("Sharpe Ratio", f"{sharpe_ratio:.2f}", icon="balance")
    with col13: 
        styled_kpi("Máx Drawdown", f"${max_drawdown:,.0f}", icon="waterfall_chart")
    with col14: 
        styled_kpi("Win Rate", f"{win_rate:.0%}", icon="check_circle")
    
    st.markdown("---")
    st.markdown("### 📅 Estadísticas Mensuales")
    col15, col16, col17 = st.columns(3)
    with col15: 
        styled_kpi("Prom. Mensual", f"{promedio_mensual_ganancias_pct:.2f}%", icon="calendar_today")
    with col16: 
        styled_kpi("Frec. Aportes", f"{frecuencia_aportes}", 
                  delta=f"${inyeccion_total/frecuencia_aportes:,.0f} c/u" if frecuencia_aportes > 0 else None,
                  icon="repeat")
    with col17: 
        styled_kpi("Frec. Retiros", f"{frecuencia_retiros}", 
                  delta=f"${total_retiros/frecuencia_retiros:,.0f} c/u" if frecuencia_retiros > 0 else None,
                  icon="exit_to_app")
    
    col18, col19 = st.columns(2)
    with col18: 
        styled_kpi("Mejor Mes", f"{mejor_mes}", 
                  delta=f"{df['Beneficio en %'].max()*100:.1f}%",
                  icon="emoji_events")
    with col19: 
        styled_kpi("Peor Mes", f"{peor_mes}", 
                  delta=f"{df['Beneficio en %'].min()*100:.1f}%",
                  icon="warning")

# 9. PÁGINA DE GRÁFICOS (MEJORADA)
elif uploaded_file and pagina == "📊 Gráficos":
    st.title("📈 Visualización de Datos")
    st.markdown("---")
    
    df_plot = df.copy()
    df_plot["Retiros"] = df_plot["Retiro de Fondos"].fillna(0)
    
    # Gráfico 1 - Capital vs Retiros
    with st.container():
        st.markdown("### 💰 Evolución del Capital")
        fig_capital = px.bar(
            df_plot, 
            x="Fecha", 
            y="Retiros",
            title="<b>Capital Invertido vs Retiros</b>",
            template="plotly_white",
            labels={"Retiros": "Retiros (USD)"},
            color_discrete_sequence=["#e74c3c"]
        )
        fig_capital.add_scatter(
            x=df_plot["Fecha"],
            y=df_plot["Capital Invertido"],
            mode='lines',
            name="Capital Invertido",
            line=dict(color="#3498db", width=3)
        )
        fig_capital.update_layout(
            hovermode="x unified",
            yaxis_tickprefix="$",
            plot_bgcolor="rgba(0,0,0,0)",
            height=450,
            xaxis_title=None
        )
        st.plotly_chart(fig_capital, use_container_width=True)
    
    # Gráfico 2 - Ganancias acumuladas
    with st.container():
        st.markdown("### 📊 Ganancias Acumuladas")
        fig1 = create_profit_chart(df)
        st.plotly_chart(fig1, use_container_width=True)
    
    # Gráfico 3 - Ganancia bruta mensual
    with st.container():
        st.markdown("### 💵 Ganancia Bruta Mensual")
        ganancia_bruta_mensual = df.groupby(df["Fecha"].dt.to_period("M"))["Ganacias/Pérdidas Brutas"].sum().reset_index()
        ganancia_bruta_mensual["Fecha"] = ganancia_bruta_mensual["Fecha"].astype(str)
        fig2 = px.bar(
            ganancia_bruta_mensual,
            x="Fecha",
            y="Ganacias/Pérdidas Brutas",
            title="<b>Ganancia Bruta Mensual</b>",
            labels={"Ganacias/Pérdidas Brutas": "Ganancia Bruta (USD)"},
            template="plotly_white",
            color_discrete_sequence=["#27ae60"]
        )
        fig2.update_traces(
            hovertemplate='Mes: %{x}<br>Ganancia: $%{y:,.0f}'
        )
        fig2.update_layout(
            yaxis_tickprefix="$",
            height=400
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Gráfico 4 - Comisiones mensuales
    with st.container():
        st.markdown("### 💸 Comisiones Mensuales")
        comisiones_mensuales = df.groupby(df["Fecha"].dt.to_period("M"))["Comisiones Pagadas"].sum().reset_index()
        comisiones_mensuales["Fecha"] = comisiones_mensuales["Fecha"].astype(str)
        fig4 = px.bar(
            comisiones_mensuales,
            x="Fecha",
            y="Comisiones Pagadas",
            title="<b>Comisiones Mensuales</b>",
            labels={"Comisiones Pagadas": "Comisiones (USD)"},
            template="plotly_white",
            color_discrete_sequence=["#e74c3c"]
        )
        fig4.update_traces(
            hovertemplate='Mes: %{x}<br>Comisión: $%{y:,.0f}'
        )
        fig4.update_layout(
            yaxis_tickprefix="$",
            height=400
        )
        st.plotly_chart(fig4, use_container_width=True)
    
    # Gráfico 5 - Rentabilidad mensual
    with st.container():
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
            template="plotly_white",
            color_discrete_sequence=["#3498db"]
        )
        fig6.update_traces(
            hovertemplate='Mes: %{x}<br>Rentabilidad: %{y:.1f}%'
        )
        fig6.update_layout(
            yaxis_ticksuffix="%",
            height=400
        )
        st.plotly_chart(fig6, use_container_width=True)

# 10. PÁGINA DE PROYECCIONES (MEJORADA)
elif uploaded_file and pagina == "📈 Proyecciones":
    st.title("🚀 Proyección de Inversión")
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
        styled_kpi("Promedio Histórico", 
                  f"{(df['Beneficio en %'].sum(skipna=True) / len(df['Beneficio en %'])):.2%}",
                  help_text="Rentabilidad mensual promedio histórica")
    
    # Configuración avanzada
    with st.expander("⚙️ Configuración Avanzada", expanded=True):
        col_adv1, col_adv2 = st.columns(2)
        with col_adv1:
            beneficio_mensual = st.slider(
                "Beneficio mensual estimado (%)", 
                min_value=0.0, 
                max_value=15.0, 
                value=float(df['Beneficio en %'].mean() * 100), 
                step=0.5
            )
        with col_adv2:
            meses_proyeccion = st.slider(
                "Duración (meses)", 
                min_value=1, 
                max_value=60, 
                value=12
            )
    
    # Cálculo de proyección
    capital_proyectado = capital_actual * (1 + aumento_opcion / 100)
    proyeccion = [capital_proyectado]
    for i in range(1, meses_proyeccion + 1):
        proyeccion.append(proyeccion[i-1] * (1 + beneficio_mensual / 100))
    
    df_proy = pd.DataFrame({
        "Mes": list(range(meses_proyeccion + 1)),
        "Proyección": proyeccion
    })
    
    # KPIs de proyección
    st.markdown("---")
    st.markdown("### 📊 Resumen de Proyección")
    col_proy1, col_proy2, col_proy3 = st.columns(3)
    with col_proy1:
        styled_kpi("Capital Inicial", f"${capital_proyectado:,.2f}", 
                 icon="account_balance_wallet")
    with col_proy2:
        styled_kpi("Valor Final", f"${proyeccion[-1]:,.2f}", 
                 delta=f"{(proyeccion[-1]/capital_proyectado-1):.1%} total",
                 icon="show_chart")
    with col_proy3:
        ganancia_total = proyeccion[-1] - capital_proyectado
        styled_kpi("Ganancia Neta", f"${ganancia_total:,.2f}", 
                 delta=f"{(ganancia_total/capital_proyectado):.1%} del capital",
                 icon="attach_money")
    
    # Gráfico de proyección
    st.markdown("---")
    st.markdown("### 📈 Trayectoria Proyectada")
    fig_proy = px.line(
        df_proy,
        x="Mes",
        y="Proyección",
        title="<b>Proyección de Crecimiento de Capital</b>",
        labels={"Proyección": "Valor del Capital (USD)"},
        template="plotly_white"
    )
    fig_proy.update_layout(
        hovermode="x unified",
        yaxis_tickprefix="$",
        height=500
    )
    fig_proy.update_traces(
        line=dict(width=3, color="#1a3a8f"),
        hovertemplate="Mes %{x}<br>$%{y:,.0f}"
    )
    st.plotly_chart(fig_proy, use_container_width=True)
    
    # Tabla de proyección
    st.markdown("---")
    st.markdown("### 📄 Detalle Mensual")
    df_proy_display = df_proy.copy()
    df_proy_display["Ganancia Mensual"] = df_proy_display["Proyección"].pct_change() * 100
    df_proy_display["Ganancia Acumulada"] = (df_proy_display["Proyección"] / capital_proyectado - 1) * 100
    
    st.dataframe(
        df_proy_display.style.format({
            "Proyección": "${:,.2f}",
            "Ganancia Mensual": "{:.2f}%",
            "Ganancia Acumulada": "{:.2f}%"
        }),
        use_container_width=True
    )
    
    # Exportar proyección
    st.markdown("---")
    st.markdown("### 📤 Exportar Proyección")
    excel_proy = BytesIO()
    with pd.ExcelWriter(excel_proy, engine='xlsxwriter') as writer:
        df_proy_display.to_excel(writer, sheet_name='Proyección', index=False)
        pd.DataFrame({
            "Métrica": ["Capital Actual", "% Aumento", "Capital Proyectado", 
                       "% Beneficio Mensual", "Meses Proyección", "Valor Final"],
            "Valor": [capital_actual, f"{aumento_opcion}%", capital_proyectado, 
                     f"{beneficio_mensual}%", meses_proyeccion, proyeccion[-1]]
        }).to_excel(writer, sheet_name='Resumen', index=False)
    
    st.download_button(
        "📥 Descargar Proyección Completa",
        data=excel_proy.getvalue(),
        file_name="proyeccion_inversion.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# 11. PÁGINA DE COMPARACIONES (MEJORADA)
elif pagina == "⚖️ Comparaciones":
    st.title("📊 Comparaciones por Año")
    st.markdown("---")
    
    # [...] (código existente de configuración de años)
    
    # ==============================================
    # NUEVO GRÁFICO 1: Relación Aumento Capital vs Retiros
    # ==============================================
    st.markdown("### 💰 Relación Aportes vs Retiros")
    
    # Preparación de datos
    aportes_retiros = df[df['Año'].isin(años_seleccionados)].groupby('Año').agg({
        'Aumento Capital': 'sum',
        'Retiro de Fondos': 'sum'
    }).reset_index()
    
    fig_relacion = px.bar(
        aportes_retiros.melt(id_vars='Año', 
                           value_vars=['Aumento Capital', 'Retiro de Fondos'],
                           var_name='Tipo', 
                           value_name='Monto'),
        x='Año',
        y='Monto',
        color='Tipo',
        barmode='group',
        color_discrete_sequence=['#27ae60', '#e74c3c'],  # Verde para aportes, rojo para retiros
        labels={'Monto': 'Monto (USD)', 'Tipo': 'Operación'},
        height=500
    )
    
    # Personalización
    fig_relacion.update_layout(
        yaxis_tickprefix='$',
        hovermode='x unified',
        plot_bgcolor='rgba(0,0,0,0)',
        legend_title_text='',
        xaxis_title=None
    )
    
    fig_relacion.update_traces(
        hovertemplate='<b>Año %{x}</b><br>%{customdata[0]}: $%{y:,.0f}',
        customdata=aportes_retiros[['Tipo']]
    )
    
    st.plotly_chart(fig_relacion, use_container_width=True)
    st.markdown("---")
    
    # ==============================================
    # NUEVO GRÁFICO 2: Sugerencia - Eficiencia de Capital (Gráfico de Radar)
    # ==============================================
    st.markdown("### 📊 Eficiencia de Capital por Año")
    
    # Cálculo de métricas de eficiencia
    eficiencia = df[df['Año'].isin(años_seleccionados)].groupby('Año').apply(
        lambda x: pd.Series({
            'ROI': (x['Ganacias/Pérdidas Netas'].sum() / 
                   (x['Aumento Capital'].sum() - x['Retiro de Fondos'].sum())) * 100,
            'Frecuencia Aportes': x[x['Aumento Capital'] > 0].shape[0],
            'Retorno Promedio': x['Beneficio en %'].mean() * 100,
            'Ratio Retiros/Aportes': (x['Retiro de Fondos'].sum() / 
                                     x['Aumento Capital'].sum()) * 100
        })
    ).reset_index()
    
    # Normalización para el gráfico de radar
    eficiencia_norm = eficiencia.copy()
    for col in ['ROI', 'Frecuencia Aportes', 'Retorno Promedio', 'Ratio Retiros/Aportes']:
        eficiencia_norm[col] = (eficiencia[col] - eficiencia[col].min()) / \
                              (eficiencia[col].max() - eficiencia[col].min()) * 100
    
    # Gráfico de radar
    fig_radar = px.line_polar(
        eficiencia_norm,
        r=eficiencia_norm.iloc[0, 2:].values,  # Primer año como ejemplo
        theta=eficiencia_norm.columns[2:],
        line_close=True,
        template='plotly_white',
        color_discrete_sequence=['#3498db']
    )
    
    # Añadir más años como trazas adicionales
    for año in eficiencia_norm['Año'].unique()[1:]:
        fig_radar.add_trace(
            px.line_polar(
                eficiencia_norm[eficiencia_norm['Año'] == año],
                r=eficiencia_norm[eficiencia_norm['Año'] == año].iloc[0, 2:].values,
                theta=eficiencia_norm.columns[2:]
            ).data[0]
        )
    
    # Personalización
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100]),
            angularaxis=dict(direction='clockwise')
        ),
        height=500,
        legend_title_text='Año',
        hovermode='closest'
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)
    st.markdown("""
    **Interpretación:**
    - **ROI:** Porcentaje de retorno sobre el capital neto
    - **Frec. Aportes:** Cantidad de operaciones de inyección
    - **Retorno Prom.:** Rentabilidad promedio mensual
    - **Ratio Ret/Aport:** Porcentaje de capital retirado vs aportado
    """)
# 12. MENSAJE INICIAL (CUANDO NO HAY ARCHIVO CARGADO)
elif not uploaded_file:
    st.info("""
    📂 **Instrucciones:**  
    1. Sube tu archivo Excel desde la barra lateral  
    2. Configura los filtros de fecha  
    3. Explora las diferentes secciones del dashboard
    """)
    st.image("https://via.placeholder.com/800x400?text=Sube+tu+archivo+Excel+para+comenzar", use_container_width=True)





