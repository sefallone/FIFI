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

        # Página principal de KPIs
        mostrar_logo()
        st.title("📌 KPIs Comparativos")
        st.markdown("---")

        # Sección 1: KPIs del Período Seleccionado
        st.header("📊 Período Seleccionado")
        st.markdown(f"**Rango de fechas:** {fecha_inicio_sel.strftime('%d/%m/%Y')} - {fecha_fin_sel.strftime('%d/%m/%Y')}")
        
        # Cálculos para el período filtrado
        capital_inicial = df_full["Aumento Capital"].dropna().iloc[0] if not df_full["Aumento Capital"].dropna().empty else 0
        inyeccion_total = df_filtered["Aumento Capital"].sum(skipna=True)
        inversionista = df_filtered["ID Inv"].dropna().iloc[0] if "ID Inv" in df_filtered.columns and not df_filtered["ID Inv"].dropna().empty else "N/A"
        total_retiros = df_filtered["Retiro de Fondos"].sum(skipna=True)
        ganancia_bruta = df_filtered["Ganacias/Pérdidas Brutas"].sum(skipna=True)
        ganancia_neta = df_filtered["Ganacias/Pérdidas Netas"].sum(skipna=True)
        comisiones = df_filtered["Comisiones Pagadas"].sum(skipna=True)
        capital_invertido = df_filtered["Capital Invertido"].dropna().iloc[-1] if not df_filtered["Capital Invertido"].dropna().empty else 0
        
        capital_inicial_neto = capital_inicial + inyeccion_total - total_retiros
        roi = (ganancia_neta / capital_inicial_neto) if capital_inicial_neto > 0 else 0
        
        fecha_inicio = df_filtered["Fecha"].min()
        fecha_fin = df_filtered["Fecha"].max()
        años_inversion = (fecha_fin - fecha_inicio).days / 365.25
        cagr = ((capital_invertido / capital_inicial_neto) ** (1 / años_inversion) - 1 if años_inversion > 0 and capital_inicial_neto > 0 else 0

        # Layout de KPIs para período seleccionado
        col1, col2, col3, col4 = st.columns(4)
        with col1: styled_kpi("Inversionista", f"{inversionista}", "#a3e4d7")
        with col2: styled_kpi("💼 Capital Inicial", f"${capital_inicial:,.2f}", "#a3e4d7")
        with col3: styled_kpi("💰 Capital Actual", f"${capital_invertido:,.2f}", "#a3e4d7")
        with col4: styled_kpi("💵 Inyección Total", f"${inyeccion_total:,.2f}", "#a3e4d7")

        col5, col6, col7, col8 = st.columns(4)
        with col5: styled_kpi("💸 Retiros", f"${total_retiros:,.2f}", "#ec7063")
        with col6: styled_kpi("📉 Ganancia Bruta", f"${ganancia_bruta:,.2f}", "#58d68d")
        with col7: styled_kpi("📈 Ganancia Neta", f"${ganancia_neta:,.2f}", "#58d68d")
        with col8: styled_kpi("🧾 Comisiones", f"${comisiones:,.2f}", "#ec7063")

        col9, col10, col11 = st.columns(3)
        with col9: styled_kpi("📅 Fecha Ingreso", f"{df_full['Fecha'].min().date()}", "#a3e4d7")
        with col10: styled_kpi("📊 ROI", f"{roi:.2%}", "#58d68d")
        with col11: styled_kpi("📈 CAGR", f"{cagr:.2%}", "#58d68d")

        # Sección 2: KPIs del Histórico Completo
        st.markdown("---")
        st.header("📊 Histórico Completo")
        st.markdown(f"**Rango completo:** {df_full['Fecha'].min().strftime('%d/%m/%Y')} - {df_full['Fecha'].max().strftime('%d/%m/%Y')}")
        
        # Cálculos para el histórico completo
        capital_inicial_full = df_full["Aumento Capital"].dropna().iloc[0] if not df_full["Aumento Capital"].dropna().empty else 0
        inyeccion_total_full = df_full["Aumento Capital"].sum(skipna=True)
        inversionista_full = df_full["ID Inv"].dropna().iloc[0] if "ID Inv" in df_full.columns and not df_full["ID Inv"].dropna().empty else "N/A"
        total_retiros_full = df_full["Retiro de Fondos"].sum(skipna=True)
        ganancia_bruta_full = df_full["Ganacias/Pérdidas Brutas"].sum(skipna=True)
        ganancia_neta_full = df_full["Ganacias/Pérdidas Netas"].sum(skipna=True)
        comisiones_full = df_full["Comisiones Pagadas"].sum(skipna=True)
        capital_invertido_full = df_full["Capital Invertido"].dropna().iloc[-1] if not df_full["Capital Invertido"].dropna().empty else 0
        
        capital_inicial_neto_full = capital_inicial_full + inyeccion_total_full - total_retiros_full
        roi_full = (ganancia_neta_full / capital_inicial_neto_full) if capital_inicial_neto_full > 0 else 0
        
        fecha_inicio_full = df_full["Fecha"].min()
        fecha_fin_full = df_full["Fecha"].max()
        años_inversion_full = (fecha_fin_full - fecha_inicio_full).days / 365.25
        cagr_full = ((capital_invertido_full / capital_inicial_neto_full) ** (1 / años_inversion_full) - 1 if años_inversion_full > 0 and capital_inicial_neto_full > 0 else 0

        # Layout de KPIs para histórico completo
        col12, col13, col14, col15 = st.columns(4)
        with col12: styled_kpi("Inversionista", f"{inversionista_full}", "#d1c4e9")
        with col13: styled_kpi("💼 Capital Inicial", f"${capital_inicial_full:,.2f}", "#d1c4e9")
        with col14: styled_kpi("💰 Capital Actual", f"${capital_invertido_full:,.2f}", "#d1c4e9")
        with col15: styled_kpi("💵 Inyección Total", f"${inyeccion_total_full:,.2f}", "#d1c4e9")

        col16, col17, col18, col19 = st.columns(4)
        with col16: styled_kpi("💸 Retiros", f"${total_retiros_full:,.2f}", "#ffccbc")
        with col17: styled_kpi("📉 Ganancia Bruta", f"${ganancia_bruta_full:,.2f}", "#c8e6c9")
        with col18: styled_kpi("📈 Ganancia Neta", f"${ganancia_neta_full:,.2f}", "#c8e6c9")
        with col19: styled_kpi("🧾 Comisiones", f"${comisiones_full:,.2f}", "#ffccbc")

        col20, col21, col22 = st.columns(3)
        with col20: styled_kpi("📅 Fecha Ingreso", f"{df_full['Fecha'].min().date()}", "#d1c4e9")
        with col21: styled_kpi("📊 ROI", f"{roi_full:.2%}", "#c8e6c9")
        with col22: styled_kpi("📈 CAGR", f"{cagr_full:.2%}", "#c8e6c9")

        # Sección 3: KPIs Adicionales Comparativos
        st.markdown("---")
        st.header("📌 Comparación Directa")

        # Calcular métricas adicionales para comparación
        avg_return = df_filtered.groupby("Mes")["Beneficio en %"].mean().mean() * 100
        avg_return_full = df_full.groupby("Mes")["Beneficio en %"].mean().mean() * 100
        
        volatility = df_filtered.groupby("Mes")["Beneficio en %"].std().mean() * 100
        volatility_full = df_full.groupby("Mes")["Beneficio en %"].std().mean() * 100
        
        max_drawdown = df_filtered["Drawdown"].min()
        max_drawdown_full = df_full["Drawdown"].min()

        col23, col24, col25 = st.columns(3)
        with col23: 
            styled_kpi("📈 Rentabilidad Prom. Mensual", 
                     f"{avg_return_full:.2f}% (Total) | {avg_return:.2f}% (Período)", 
                     "#F1F8E9")
        with col24: 
            styled_kpi("📉 Volatilidad Mensual", 
                     f"{volatility_full:.2f}% (Total) | {volatility:.2f}% (Período)", 
                     "#FFEBEE")
        with col25: 
            styled_kpi("📊 Máximo Drawdown", 
                     f"${max_drawdown_full:,.2f} (Total) | ${max_drawdown:,.2f} (Período)", 
                     "#FFCDD2")

        # Gráfico comparativo de evolución
        st.markdown("---")
        st.header("📊 Evolución Comparativa")
        
        # Preparar datos para el gráfico
        df_full_evolution = df_full.groupby(df_full["Fecha"].dt.to_period("M")).agg({
            "Capital Invertido": "last"
        }).reset_index()
        df_full_evolution["Tipo"] = "Histórico Completo"
        
        df_filtered_evolution = df_filtered.groupby(df_filtered["Fecha"].dt.to_period("M")).agg({
            "Capital Invertido": "last"
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
            title="Evolución del Capital Invertido: Comparación",
            template="plotly_white",
            labels={"Capital Invertido": "Capital ($)", "Fecha": "Mes"}
        )
        st.plotly_chart(fig_capital, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
else:
    mostrar_logo()
    st.info("📂 Por favor, sube un archivo Excel desde la barra lateral para comenzar.")


