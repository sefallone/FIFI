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
        # Cargar y preparar los datos
        df = pd.read_excel(uploaded_file, sheet_name="Histórico")
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df = df.dropna(subset=["Fecha"])
        
        # Validar columnas requeridas
        required_columns = [
            "Capital Invertido", "Aumento Capital", "Retiro de Fondos",
            "Ganacias/Pérdidas Netas", "Comisiones Pagadas", "Fecha"
        ]
        if not all(col in df.columns for col in required_columns):
            st.error("❌ El archivo no contiene las columnas requeridas.")
            st.stop()

        # Configurar filtros de fecha
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

        # Filtrar DataFrame
        df_filtrado = df[(df["Fecha"] >= fecha_inicio_sel) & (df["Fecha"] <= fecha_fin_sel)]
        if df_filtrado.empty:
            st.warning("⚠️ No hay datos disponibles en el rango de fechas seleccionado.")
            st.stop()

        # Procesamiento adicional
        df_filtrado["Mes"] = df_filtrado["Fecha"].dt.to_period("M")
        df_filtrado["Acumulado"] = df_filtrado["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
        df_filtrado["MaxAcum"] = df_filtrado["Acumulado"].cummax()
        df_filtrado["Drawdown"] = df_filtrado["Acumulado"] - df_filtrado["MaxAcum"]

        # Navegación entre páginas
        pagina = st.sidebar.radio(
            "Selecciona la sección",
            ["📌 KPIs", "📊 Gráficos", "📈 Proyecciones", "⚖️ Comparaciones"]
        )

        # Página de KPIs
        if pagina == "📌 KPIs":
            mostrar_logo()
            st.title("📌 Indicadores Clave de Desempeño (KPIs)")
            st.markdown("---")

            # Obtener capital inicial del primer registro histórico (sin filtrar)
            capital_inicial = df["Aumento Capital"].dropna().iloc[0] if not df["Aumento Capital"].dropna().empty else 0

            # Calcular KPIs con datos filtrados
            capital_invertido = df_filtrado["Capital Invertido"].dropna().iloc[-1] if not df_filtrado["Capital Invertido"].dropna().empty else 0
            inyeccion_total = df_filtrado["Aumento Capital"].sum(skipna=True)
            inversionista = df_filtrado["ID Inv"].dropna().iloc[0] if "ID Inv" in df_filtrado.columns and not df_filtrado["ID Inv"].dropna().empty else "N/A"
            total_retiros = df_filtrado["Retiro de Fondos"].sum(skipna=True)
            ganancia_bruta = df_filtrado["Ganacias/Pérdidas Brutas"].sum(skipna=True)
            ganancia_neta = df_filtrado["Ganacias/Pérdidas Netas"].sum(skipna=True)
            comisiones = df_filtrado["Comisiones Pagadas"].sum(skipna=True)
            fecha_ingreso = df["Fecha"].min().date()

            # Cálculos financieros
            capital_inicial_neto = capital_inicial + inyeccion_total - total_retiros
            roi = (ganancia_neta / capital_inicial_neto) if capital_inicial_neto > 0 else 0
            
            fecha_inicio = df_filtrado["Fecha"].min()
            fecha_fin = df_filtrado["Fecha"].max()
            años_inversion = (fecha_fin - fecha_inicio).days / 365.25
            cagr = ((capital_invertido / capital_inicial_neto) ** (1 / años_inversion) - 1) if años_inversion > 0 and capital_inicial_neto > 0 else 0

            # Mostrar KPIs
            col1, col2, col3, col4 = st.columns(4)
            with col1: styled_kpi("Inversionista", f"{inversionista}", "#a3e4d7", "ID del inversionista")
            with col2: styled_kpi("💼 Capital Inicial", f"${capital_inicial:,.2f}", "#a3e4d7", "Primer aporte de capital")
            with col3: styled_kpi("💰 Capital Actual", f"${capital_invertido:,.2f}", "#a3e4d7", "Capital al final del período")
            with col4: styled_kpi("💵 Inyección Total", f"${inyeccion_total:,.2f}", "#a3e4d7", "Suma de aportes en el período")

            col5, col6, col7, col8 = st.columns(4)
            with col5: styled_kpi("💸 Retiros", f"${total_retiros:,.2f}", "#ec7063", "Total retirado en el período")
            with col6: styled_kpi("📉 Ganancia Bruta", f"${ganancia_bruta:,.2f}", "#58d68d", "Ganancias antes de comisiones")
            with col7: styled_kpi("📈 Ganancia Neta", f"${ganancia_neta:,.2f}", "#58d68d", "Ganancias después de comisiones")
            with col8: styled_kpi("🧾 Comisiones", f"${comisiones:,.2f}", "#ec7063", "Comisiones pagadas en el período")

            col9, col10, col11 = st.columns(3)
            with col9: styled_kpi("📅 Fecha Ingreso", f"{fecha_ingreso}", "#a3e4d7", "Fecha del primer registro")
            with col10: styled_kpi("📊 ROI", f"{roi:.2%}", "#58d68d", "Retorno sobre inversión")
            with col11: styled_kpi("📈 CAGR", f"{cagr:.2%}", "#58d68d", "Tasa de crecimiento anual compuesto")

            st.markdown("---")
            
            # KPIs adicionales
            promedio_mensual = df_filtrado.groupby("Mes")["Beneficio en %"].mean().mean() * 100
            styled_kpi("📈 Rentabilidad Prom. Mensual", f"{promedio_mensual:.2f}%", "#F1F8E9", "Promedio mensual de rentabilidad")

            col12, col13, col14 = st.columns(3)
            with col12:
                freq_aportes = df_filtrado[df_filtrado["Aumento Capital"] > 0].shape[0]
                styled_kpi("🔁 Aportes", f"{freq_aportes}", "#E3F2FD", "Número de aportes de capital")
            with col13:
                freq_retiros = df_filtrado[df_filtrado["Retiro de Fondos"] > 0].shape[0]
                styled_kpi("📤 Retiros", f"{freq_retiros}", "#FFF3E0", "Número de retiros realizados")
            with col14:
                mejor_mes = df_filtrado.loc[df_filtrado["Beneficio en %"].idxmax()]["Mes"] if not df_filtrado.empty else "N/A"
                styled_kpi("🌟 Mejor Mes", f"{mejor_mes}", "#E8F5E9", "Mes con mayor rentabilidad")

        # Página de Gráficos
        elif pagina == "📊 Gráficos":
            mostrar_logo()
            st.title("📊 Visualizaciones Financieras")
            
            # Gráfico 1: Evolución del capital
            fig_capital = px.line(
                df_filtrado, x="Fecha", y="Capital Invertido",
                title="Evolución del Capital Invertido",
                template="plotly_white"
            )
            st.plotly_chart(fig_capital, use_container_width=True)

            # Gráfico 2: Ganancias netas acumuladas
            fig_acumulado = px.line(
                df_filtrado, x="Fecha", y="Ganacias/Pérdidas Netas Acumuladas",
                title="Ganancias Netas Acumuladas",
                template="plotly_white"
            )
            st.plotly_chart(fig_acumulado, use_container_width=True)

            # Gráfico 3: Rentabilidad mensual
            rentabilidad_mensual = df_filtrado.groupby("Mes")["Beneficio en %"].mean().reset_index()
            rentabilidad_mensual["Mes"] = rentabilidad_mensual["Mes"].astype(str)
            fig_rentabilidad = px.bar(
                rentabilidad_mensual, x="Mes", y="Beneficio en %",
                title="Rentabilidad Mensual (%)",
                template="plotly_white"
            )
            st.plotly_chart(fig_rentabilidad, use_container_width=True)

            # Gráfico 4: Comisiones mensuales
            comisiones_mensuales = df_filtrado.groupby("Mes")["Comisiones Pagadas"].sum().reset_index()
            comisiones_mensuales["Mes"] = comisiones_mensuales["Mes"].astype(str)
            fig_comisiones = px.bar(
                comisiones_mensuales, x="Mes", y="Comisiones Pagadas",
                title="Comisiones Mensuales",
                template="plotly_white"
            )
            st.plotly_chart(fig_comisiones, use_container_width=True)

        # Página de Proyecciones
        elif pagina == "📈 Proyecciones":
            mostrar_logo()
            st.title("📈 Proyección de Inversión")

            capital_actual = float(df_filtrado["Capital Invertido"].dropna().iloc[-1])
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

            # Tabla de proyección
            st.markdown("### Detalle de Proyección")
            df_proyeccion = pd.DataFrame({
                "Mes": range(meses_proyeccion + 1),
                "Capital": proyeccion
            })
            st.dataframe(df_proyeccion.style.format({"Capital": "${:,.2f}"}))

        # Página de Comparaciones
        elif pagina == "⚖️ Comparaciones":
            mostrar_logo()
            st.title("⚖️ Comparaciones por Año")

            df_filtrado['Año'] = df_filtrado['Fecha'].dt.year
            df_filtrado['MesNombre'] = df_filtrado['Fecha'].dt.strftime('%b')
            años_disponibles = sorted(df_filtrado['Año'].unique())
            
            años_seleccionados = st.multiselect(
                "Selecciona años a comparar",
                años_disponibles,
                default=años_disponibles
            )

            # Gráfico comparativo de ganancias netas
            ganancias_anuales = df_filtrado[df_filtrado['Año'].isin(años_seleccionados)].groupby('Año')['Ganacias/Pérdidas Netas'].sum().reset_index()
            
            fig_comparativo = px.bar(
                ganancias_anuales, x='Año', y='Ganacias/Pérdidas Netas',
                title='Ganancias Netas por Año',
                template='plotly_white'
            )
            st.plotly_chart(fig_comparativo, use_container_width=True)

            # Gráfico de composición de rendimiento
            rendimiento_mensual = df_filtrado[df_filtrado['Año'].isin(años_seleccionados)].groupby(['Año', 'MesNombre'])['Beneficio en %'].mean().reset_index()
            
            fig_rendimiento = px.bar(
                rendimiento_mensual, x='MesNombre', y='Beneficio en %',
                color='Año', barmode='group',
                title='Rendimiento Mensual por Año',
                template='plotly_white'
            )
            st.plotly_chart(fig_rendimiento, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
else:
    mostrar_logo()
    st.info("📂 Por favor, sube un archivo Excel desde la barra lateral para comenzar.")







