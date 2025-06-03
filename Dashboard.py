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

# =============================================
# CONFIGURACIÓN INICIAL
# =============================================
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

# =============================================
# BARRA LATERAL Y CARGA DE DATOS
# =============================================
with st.sidebar:
    st.title("Configuración")
    uploaded_file = st.file_uploader("Sube el archivo Excel (.xlsx)", type=["xlsx"])

# =============================================
# PROCESAMIENTO PRINCIPAL
# =============================================
if uploaded_file:
    try:
        # Carga y preprocesamiento inicial
        df = pd.read_excel(uploaded_file, sheet_name="Histórico")
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df = df.dropna(subset=["Fecha"])
        
        # Validación de columnas críticas
        required_columns = [
            "Capital Invertido", "Aumento Capital", "Retiro de Fondos",
            "Ganacias/Pérdidas Netas", "Comisiones Pagadas", "Fecha"
        ]
        if not all(col in df.columns for col in required_columns):
            st.error("❌ El archivo no contiene las columnas requeridas.")
            st.stop()

        # Configuración de filtros de fecha
        fecha_min = df["Fecha"].min().replace(day=1)
        fecha_max_original = df["Fecha"].max().replace(day=1)
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

        # Filtrado del DataFrame
        df = df[(df["Fecha"] >= fecha_inicio_sel) & (df["Fecha"] <= fecha_fin_sel)]
        if df.empty:
            st.warning("⚠️ No hay datos disponibles en el rango de fechas seleccionado.")
            st.stop()

        # Preprocesamiento adicional
        df["Mes"] = df["Fecha"].dt.to_period("M")
        df["Acumulado"] = df["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
        df["MaxAcum"] = df["Acumulado"].cummax()
        df["Drawdown"] = df["Acumulado"] - df["MaxAcum"]

        # Navegación entre páginas
        pagina = st.sidebar.radio(
            "Selecciona la sección",
            ["📌 KPIs", "📊 Gráficos", "📈 Proyecciones", "⚖️ Comparaciones"]
        )

        # =============================================
        # PÁGINA: KPIs
        # =============================================
        if pagina == "📌 KPIs":
            mostrar_logo()
            st.title("📌 Indicadores Clave de Desempeño (KPIs)")
            st.markdown("---")

            # Cálculo de KPIs base
            capital_invertido = df["Capital Invertido"].dropna().iloc[-1] if not df["Capital Invertido"].dropna().empty else 0
            capital_inicial = df["Aumento Capital"].dropna().iloc[0] if not df["Aumento Capital"].dropna().empty else 0
            inyeccion_total = df["Aumento Capital"].sum(skipna=True)
            inversionista = df["ID Inv"].dropna().iloc[0] if "ID Inv" in df.columns and not df["ID Inv"].dropna().empty else "N/A"
            total_retiros = df["Retiro de Fondos"].sum(skipna=True)
            ganancia_bruta = df["Ganacias/Pérdidas Brutas"].sum(skipna=True)
            ganancia_neta = df["Ganacias/Pérdidas Netas"].sum(skipna=True)
            comisiones = df["Comisiones Pagadas"].sum(skipna=True)
            fecha_ingreso = df["Fecha"].min().date()

            # Cálculos financieros avanzados
            capital_inicial_neto = capital_inicial + inyeccion_total - total_retiros
            roi = (ganancia_neta / capital_inicial_neto) if capital_inicial_neto > 0 else 0
            
            fecha_inicio = df["Fecha"].min()
            fecha_fin = df["Fecha"].max()
            años_inversion = (fecha_fin - fecha_inicio).days / 365.25
            cagr = ((capital_invertido / capital_inicial_neto) ** (1 / años_inversion) - 1) if años_inversion > 0 and capital_inicial_neto > 0 else 0

            # Layout de KPIs
            col1, col2, col3, col4 = st.columns(4)
            with col1: styled_kpi("Inversionista", f"{inversionista}", "#a3e4d7")
            with col2: styled_kpi("💼 Capital Inicial", f"${capital_inicial:,.2f}", "#a3e4d7")
            with col3: styled_kpi("💰 Capital Invertido", f"${capital_invertido:,.2f}", "#a3e4d7")
            with col4: styled_kpi("💵 Inyección Capital", f"${inyeccion_total:,.2f}", "#a3e4d7")

            col5, col6, col7, col8 = st.columns(4)
            with col5: styled_kpi("💸 Retiros", f"${total_retiros:,.2f}", "#ec7063")
            with col6: styled_kpi("📉 Ganancia Bruta", f"${ganancia_bruta:,.2f}", "#58d68d")
            with col7: styled_kpi("📈 Ganancia Neta", f"${ganancia_neta:,.2f}", "#58d68d")
            with col8: styled_kpi("🧾 Comisiones", f"${comisiones:,.2f}", "#ec7063")

            col9, col10, col11 = st.columns(3)
            with col9: styled_kpi("📅 Fecha Ingreso", f"{fecha_ingreso}", "#a3e4d7")
            with col10: styled_kpi("📊 ROI Total", f"{roi:.2%}", "#58d68d")
            with col11: styled_kpi("📈 CAGR", f"{cagr:.2%}", "#58d68d")

            st.markdown("---")
            
            # KPIs adicionales
            promedio_mensual = df.groupby("Mes")["Beneficio en %"].mean().mean() * 100
            styled_kpi("📈 Rentabilidad Prom. Mensual", f"{promedio_mensual:.2f}%", "#F1F8E9")

            col12, col13, col14 = st.columns(3)
            with col12:
                freq_aportes = df[df["Aumento Capital"] > 0].shape[0]
                styled_kpi("🔁 Aportes", f"{freq_aportes}", "#E3F2FD")
            with col13:
                freq_retiros = df[df["Retiro de Fondos"] > 0].shape[0]
                styled_kpi("📤 Retiros", f"{freq_retiros}", "#FFF3E0")
            with col14:
                mejor_mes = df.loc[df["Beneficio en %"].idxmax()]["Mes"]
                styled_kpi("🌟 Mejor Mes", f"{mejor_mes}", "#E8F5E9")

        # =============================================
        # PÁGINA: GRÁFICOS
        # =============================================
        elif pagina == "📊 Gráficos":
            mostrar_logo()
            st.title("📊 Visualizaciones Financieras")
            
            # Gráfico 1: Evolución del capital
            fig_capital = px.line(
                df, x="Fecha", y="Capital Invertido",
                title="Evolución del Capital Invertido",
                template="plotly_white"
            )
            st.plotly_chart(fig_capital, use_container_width=True)

            # Gráfico 2: Ganancias netas acumuladas
            fig_acumulado = px.line(
                df, x="Fecha", y="Ganacias/Pérdidas Netas Acumuladas",
                title="Ganancias Netas Acumuladas",
                template="plotly_white"
            )
            st.plotly_chart(fig_acumulado, use_container_width=True)

            # Gráfico 3: Rentabilidad mensual
            rentabilidad_mensual = df.groupby("Mes")["Beneficio en %"].mean().reset_index()
            rentabilidad_mensual["Mes"] = rentabilidad_mensual["Mes"].astype(str)
            fig_rentabilidad = px.bar(
                rentabilidad_mensual, x="Mes", y="Beneficio en %",
                title="Rentabilidad Mensual (%)",
                template="plotly_white"
            )
            st.plotly_chart(fig_rentabilidad, use_container_width=True)

        # =============================================
        # PÁGINA: PROYECCIONES
        # =============================================
        elif pagina == "📈 Proyecciones":
            mostrar_logo()
            st.title("📈 Proyección de Inversión")

            capital_actual = float(df["Capital Invertido"].dropna().iloc[-1])
            aumento_opcion = st.selectbox(
                "Aumento de capital (%)",
                [0, 5, 10, 20, 30, 50]
            )
            beneficio_mensual = st.slider(
                "Beneficio mensual estimado (%)",
                0.0, 15.0, 5.0, 0.5
            )
            meses_proyeccion = st.slider(
                "Meses de proyección",
                1, 60, 12
            )

            # Cálculos de proyección
            capital_proyectado = capital_actual * (1 + aumento_opcion/100)
            proyeccion = [
                capital_proyectado * ((1 + beneficio_mensual/100) ** i) 
                for i in range(meses_proyeccion + 1)
            ]
            
            # Mostrar resultados
            col1, col2 = st.columns(2)
            with col1:
                styled_kpi("Capital Inicial", f"${capital_proyectado:,.2f}", "#E3F2FD")
            with col2:
                styled_kpi("Valor Final", f"${proyeccion[-1]:,.2f}", "#E8F5E9")

            # Gráfico de proyección
            fig_proy = px.line(
                x=range(meses_proyeccion + 1),
                y=proyeccion,
                title="Proyección de Crecimiento",
                labels={"x": "Meses", "y": "Capital ($)"},
                template="plotly_white"
            )
            st.plotly_chart(fig_proy, use_container_width=True)

        # =============================================
        # PÁGINA: COMPARACIONES
        # =============================================
        elif pagina == "⚖️ Comparaciones":
            mostrar_logo()
            st.title("⚖️ Comparaciones por Año")

            df['Año'] = df['Fecha'].dt.year
            df['MesNombre'] = df['Fecha'].dt.strftime('%b')
            años_disponibles = sorted(df['Año'].unique())
            
            años_seleccionados = st.multiselect(
                "Selecciona años a comparar",
                años_disponibles,
                default=años_disponibles
            )

            # Gráfico comparativo de ganancias netas
            ganancias_anuales = df[df['Año'].isin(años_seleccionados)].groupby('Año')['Ganacias/Pérdidas Netas'].sum().reset_index()
            
            fig_comparativo = px.bar(
                ganancias_anuales, x='Año', y='Ganacias/Pérdidas Netas',
                title='Ganancias Netas por Año',
                template='plotly_white'
            )
            st.plotly_chart(fig_comparativo, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error crítico: {str(e)}")
else:
    mostrar_logo()
    st.info("📂 Por favor, sube un archivo Excel desde la barra lateral para comenzar.")








