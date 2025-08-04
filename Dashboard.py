import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from PIL import Image
import base64
import calendar
from io import BytesIO
import os

# =============================================================================
# 🔐 SISTEMA DE AUTENTICACIÓN MEJORADO
# =============================================================================
def check_password():
    """Autenticación segura con manejo mejorado de archivos."""
    
    if st.session_state.get("authenticated"):
        return True
    
    st.title("🔐 Acceso al Dashboard FIFI")
    st.markdown("Por favor ingrese sus credenciales de acceso")
    
    with st.form("login_form"):
        username = st.text_input("Usuario").strip()
        password = st.text_input("Contraseña", type="password").strip()
        submitted = st.form_submit_button("Ingresar")
        
        if submitted:
            try:
                credenciales_validas = st.secrets["inversionistas"]
                archivos_usuarios = st.secrets["archivos_usuarios"]
                
                if username in credenciales_validas and credenciales_validas[username] == password:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    
                    # Manejo mejorado de rutas de archivos
                    archivo_usuario = archivos_usuarios[username]
                    
                    # Verificar si es una URL o ruta local
                    if archivo_usuario.startswith(("http://", "https://")):
                        st.session_state["archivo_usuario"] = archivo_usuario
                    else:
                        # Para compatibilidad con Streamlit Cloud
                        st.session_state["archivo_usuario"] = os.path.join("data", archivo_usuario)
                    
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")
            except Exception as e:
                st.error(f"Error de autenticación: {str(e)}")
                st.stop()
    
    return False

if not check_password():
    st.stop()

# =============================================================================
# 🚀 CONFIGURACIÓN INICIAL
# =============================================================================
st.set_page_config(
    page_title=f"Dashboard FIFI - {st.session_state['username']}",
    layout="wide",
    page_icon="📊"
)

# Barra lateral
with st.sidebar:
    st.markdown(f"### 👤 {st.session_state['username']}")
    if st.button("🚪 Cerrar sesión"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Configuración")

# Logo
def load_logo():
    try:
        logo_path = os.path.join("logo.jpg")
        with open(logo_path, "rb") as f:
            logo_b64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <div style='text-align: center;'>
                <img src='data:image/jpeg;base64,{logo_b64}' style='width:200px;'/>
                <h3 style='margin-top:10px;'>Fallone Investments</h3>
            </div>
            """, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Logo no encontrado en la ruta especificada")

load_logo()

# =============================================================================
# 📁 CARGA DE DATOS MEJORADA
# =============================================================================
@st.cache_data(ttl=3600)
def load_user_data(file_path):
    """Carga los datos del usuario con manejo robusto de errores."""
    try:
        if file_path.startswith(("http://", "https://")):
            # Para archivos remotos
            df = pd.read_excel(file_path, sheet_name="Histórico")
        else:
            # Para archivos locales
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"No se encontró el archivo: {file_path}")
            df = pd.read_excel(file_path, sheet_name="Histórico")
        
        # Validación básica de datos
        required_columns = ["Fecha", "Capital Invertido", "Ganacias/Pérdidas Netas"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Columna requerida no encontrada: {col}")
        
        df = df.dropna(subset=["Fecha"])
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df["Mes"] = df["Fecha"].dt.to_period("M")
        return df.sort_values("Fecha")
        
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        st.stop()

# Cargar datos con manejo de errores
try:
    archivo_usuario = st.session_state.get("archivo_usuario", "")
    if not archivo_usuario:
        st.error("No se ha configurado archivo para este usuario")
        st.stop()
    
    df = load_user_data(archivo_usuario)
    st.sidebar.success(f"Archivo cargado: {os.path.basename(archivo_usuario)}")
    
except Exception as e:
    st.error(f"Error al cargar datos del usuario: {str(e)}")
    st.stop()

# =============================================================================
# 📌 SECCIÓN DE KPIs
# =============================================================================
def styled_kpi(title, value, bg_color="#45403D", text_color="#DDE2ED", tooltip=""):
    
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

def show_kpis():
    """Muestra los KPIs financieros con validación robusta de datos."""
    
    st.title("📌 Indicadores Clave de Desempeño (KPIs)")
    
    # =========================================================================
    # 🔍 VALIDACIÓN DE COLUMNAS REQUERIDAS
    # =========================================================================
    required_columns = {
        "Fecha": "datetime",
        "Capital Invertido": "numeric",
        "Aumento Capital": "numeric",
        "ID Inv": "any",
        "Retiro de Fondos": "numeric",
        "Ganacias/Pérdidas Brutas": "numeric",
        "Ganacias/Pérdidas Netas": "numeric",
        "Comisiones Pagadas": "numeric",
        "Ganacias/Pérdidas Netas Acumuladas": "numeric",
        "Beneficio en %": "numeric"
    }

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"❌ Columnas faltantes en el archivo: {', '.join(missing_cols)}")
        st.stop()

    # =========================================================================
    # 📊 CÁLCULO DE KPIs
    # =========================================================================
    try:
        # Preprocesamiento esencial
        df["Mes"] = df["Fecha"].dt.to_period("M")
        df["Acumulado"] = df["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
        df["MaxAcum"] = df["Acumulado"].cummax()
        df["Drawdown"] = df["Acumulado"] - df["MaxAcum"]

        # Datos básicos
        capital_invertido = df["Capital Invertido"].dropna().iloc[-1]
        capital_inicial = df["Aumento Capital"].dropna().iloc[0]
        inyeccion_total = df["Aumento Capital"].sum(skipna=True)
        inversionista = df["ID Inv"].dropna().iloc[0]
        total_retiros = df["Retiro de Fondos"].sum(skipna=True)
        ganancia_bruta = df["Ganacias/Pérdidas Brutas"].sum(skipna=True)
        ganancia_neta = df["Ganacias/Pérdidas Netas"].sum(skipna=True)
        comisiones = df["Comisiones Pagadas"].iloc[-1]
        fecha_ingreso = df["Fecha"].dropna().iloc[0].date()

        # Cálculos avanzados
        capital_base = capital_invertido - total_retiros
        roi = (ganancia_neta / capital_base) if capital_base > 0 else 0
        
        monthly_returns = df.groupby("Mes")["Ganacias/Pérdidas Netas"].sum()
        monthly_avg_return_pct = (df["Beneficio en %"].sum(skipna=True) / len(df["Beneficio en %"]))
        
        months_active = (df["Fecha"].max() - df["Fecha"].min()).days / 30.44
        cagr_mensual = ((1 + roi) ** (1 / months_active) - 1) if months_active > 0 else 0
        
        max_drawdown = df["Drawdown"].min()
        mejor_mes = df.loc[df["Beneficio en %"].idxmax()]["Mes"] if not df.empty else "N/A"
        peor_mes = df.loc[df["Beneficio en %"].idxmin()]["Mes"] if not df.empty else "N/A"

        # =========================================================================
        # 🎨 VISUALIZACIÓN DE KPIs
        # =========================================================================
        col1, col2, col3, col4 = st.columns(4)
        with col1: 
            styled_kpi("🧑 Inversionista", f"{inversionista}", "#276CF5", tooltip="ID del inversionista")
        with col2: 
            styled_kpi("💼 Capital Inicial", f"${capital_inicial:,.2f}", "#276CF5", tooltip="Capital inicial invertido")
        with col3: 
            styled_kpi("💰 Capital Actual", f"${capital_invertido:,.2f}", "#276CF5", tooltip="Capital actual en cartera")
        with col4: 
            styled_kpi("💵 Inyección Total", f"${inyeccion_total:,.2f}", "#276CF5", tooltip="Total de aportes realizados")

        col5, col6, col7, col8 = st.columns(4)
        with col5: 
            styled_kpi("💸 Retiros Totales", f"${total_retiros:,.2f}", "#276CF5", tooltip="Total retirado de la inversión")
        with col6: 
            styled_kpi("📉 Ganancia Bruta", f"${ganancia_bruta:,.2f}", "#276CF5", tooltip="Ganancias antes de comisiones")
        with col7: 
            styled_kpi("📈 Ganancia Neta", f"${ganancia_neta:,.2f}", "#276CF5", tooltip="Ganancias después de comisiones")
        with col8: 
            styled_kpi("🧾 Comisiones", f"${comisiones:,.2f}", "#276CF5", tooltip="Total en comisiones pagadas")

        col9, col10, col11 = st.columns(3)
        with col9: 
            styled_kpi("📅 Fecha Ingreso", fecha_ingreso.strftime("%d/%m/%Y"), "#276CF5", tooltip="Fecha de inicio de inversión")
        with col10: 
            styled_kpi("📊 ROI Total", f"{roi:.2%}", "#276CF5", tooltip="Retorno total sobre la inversión")
        with col11: 
            styled_kpi("🚀 CAGR Mensual", f"{cagr_mensual:.2%}", "#276CF5", tooltip="Tasa de crecimiento anualizada")

        st.markdown("---")
        
        col12, col13, col14 = st.columns(3)
        with col12:
            styled_kpi("📆 Rentabilidad Prom.", f"{monthly_avg_return_pct:.2%}", "#276CF5", tooltip="Rentabilidad mensual promedio")
        with col13:
            styled_kpi("📉 Máximo Drawdown", f"${max_drawdown:,.2f}", "#276CF5", tooltip="Peor pérdida acumulada")
        with col14:
            styled_kpi("📅 Mejor Mes", f"{mejor_mes}", "#276CF5", tooltip="Mes con mayor rentabilidad en %")

        st.markdown("---")
        
    except Exception as e:
        st.error(f"❌ Error al calcular KPIs: {str(e)}")
        st.stop()
# =============================================================================
# 📊 SECCIÓN DE GRÁFICOS
# =============================================================================
def show_charts():
    st.title("📊 Visualizaciones Financieras")

    # Preprocesamiento adicional
    df["Mes"] = df["Fecha"].dt.to_period("M")
    df["Acumulado"] = df["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
    df["MaxAcum"] = df["Acumulado"].cummax()
    df["Drawdown"] = df["Acumulado"] - df["MaxAcum"]
    df["Capital Acumulado"] = df["Capital Invertido"]

    # Gráfico 1: Capital Invertido y Retiros
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

    # Gráfico 2: Ganancia Neta Acumulada
    fig1 = px.line(
        df,
        x="Fecha",
        y="Ganacias/Pérdidas Netas Acumuladas",
        title="Ganancia Neta Acumulada",
        template="plotly_white"
    )
    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 3: Ganancia Bruta Mensual
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

    # Gráfico 4: Comisiones Mensuales
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

    # Gráfico 5: Rentabilidad Mensual
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

# =============================================================================
# 📈 SECCIÓN DE PROYECCIONES
# =============================================================================
def show_projections():
    st.title("📈 Proyección de Inversión Personalizada")

    capital_actual = float(df["Capital Invertido"].dropna().iloc[-1])
    aumento_opcion = st.selectbox("Selecciona porcentaje de aumento de capital", [0, 5, 10, 20, 30, 50])
    promedio_mensual_ganancias = (df["Beneficio en %"].sum(skipna=True) / len(df["Beneficio en %"]))
    
    styled_kpi("📆 Promedio Mensual de Ganancias", f"{promedio_mensual_ganancias:.2%}", "#E0F7FA", tooltip="Promedio mensual de las ganancias brutas en porcentaje sobre el capital actual.")

    beneficio_mensual = st.slider("Beneficio mensual estimado (%)", min_value=0.0, max_value=15.0, value=5.0, step=0.5)
    meses_proyeccion = st.slider("Duración de la inversión (meses)", min_value=1, max_value=60, value=12)

    capital_proyectado = capital_actual * (1 + aumento_opcion / 100)
    proyeccion = [capital_proyectado * ((1 + beneficio_mensual / 100) ** i) for i in range(meses_proyeccion + 1)]
    df_proy = pd.DataFrame({"Mes": list(range(meses_proyeccion + 1)), "Proyección": proyeccion})

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1: styled_kpi("💼 Capital Inicial Proyectado", f"${capital_proyectado:,.2f}", "#276CF5")
    with col2: styled_kpi("📈 Valor Estimado Final", f"${proyeccion[-1]:,.2f}", "#276CF5")
    #with col3: styled_kpi("📈 Capital Compuesto Anual", f"${capital_proyectado * ((1 + beneficio_mensual / 100) ** 12):,.2f}", "#276CF5")

    fig = px.line(df_proy, x="Mes", y="Proyección", title="Proyección de Crecimiento de Capital", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📄 Detalle de Proyección (mes a mes)")
    st.dataframe(df_proy.style.format({"Proyección": "${:,.2f}"}), use_container_width=True)

    # Exportar a Excel
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
    st.download_button(
        "📥 Descargar proyección en Excel",
        data=excel_data,
        file_name="proyeccion.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# =============================================================================
# ⚖️ SECCIÓN DE COMPARACIONES
# =============================================================================
def show_comparisons():
    st.title("⚖️ Comparaciones por Año")
    
    try:
        # Verificar y crear columnas necesarias
        if 'Fecha' not in df.columns:
            st.error("La columna 'Fecha' no existe en los datos")
            st.stop()
            
        # Crear columnas de año y mes si no existen
        df['Año'] = df['Fecha'].dt.year
        df['MesNombre'] = df['Fecha'].dt.strftime('%b')
        df['MesOrden'] = df['Fecha'].dt.month
        
        # Asegurar que existe la columna Drawdown
        if 'Drawdown' not in df.columns:
            if 'Ganacias/Pérdidas Netas Acumuladas' in df.columns:
                df['Acumulado'] = df['Ganacias/Pérdidas Netas Acumuladas'].fillna(method='ffill')
                df['MaxAcum'] = df['Acumulado'].cummax()
                df['Drawdown'] = df['Acumulado'] - df['MaxAcum']
            else:
                st.error("No se puede calcular Drawdown: faltan columnas necesarias")
                st.stop()

        # Selección de años
        años_disponibles = sorted(df['Año'].unique().tolist())
        if not años_disponibles:
            st.warning("No hay datos de años disponibles para comparar")
            st.stop()
            
        años_seleccionados = st.multiselect(
            "Selecciona los años a comparar",
            años_disponibles,
            default=años_disponibles[-2:] if len(años_disponibles) > 1 else años_disponibles
        )
        
        if not años_seleccionados:
            st.warning("Por favor selecciona al menos un año")
            st.stop()

        # Gráfico 1: Rentabilidad Promedio Mensual
        st.markdown("### 📈 Rentabilidad Promedio Mensual (%)")
        
        # Calcular rentabilidad mensual
        if 'Beneficio en %' not in df.columns:
            st.error("Columna 'Beneficio en %' no encontrada")
            st.stop()
            
        comparacion_anual = df[df['Año'].isin(años_seleccionados)].groupby(
            ['Año', 'MesNombre', 'MesOrden']).agg({
                'Beneficio en %': 'mean'
            }).reset_index().sort_values(['Año', 'MesOrden'])
        
        comparacion_anual["Beneficio en %"] *= 100  # Convertir a porcentaje

        fig_rentabilidad = px.line(
            comparacion_anual,
            x="MesNombre",
            y="Beneficio en %",
            color="Año",
            title="Rentabilidad Promedio Mensual por Año",
            template="plotly_white",
            category_orders={"MesNombre": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                                         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]}
        )
        fig_rentabilidad.update_traces(
            mode="lines+markers+text",
            text=comparacion_anual["Beneficio en %"].round(1),
            textposition="top center",
            hovertemplate='Mes: %{x}<br>Rentabilidad: %{y:.1f}%'
        )
        fig_rentabilidad.update_layout(yaxis_title="Rentabilidad (%)")
        st.plotly_chart(fig_rentabilidad, use_container_width=True)
        st.markdown("---")

        # Gráfico 2: Ganancia Neta Anual
        st.markdown("### 📊 Ganancia Neta Anual")
        ganancia_anual = df[df['Año'].isin(años_seleccionados)].groupby("Año").agg({
            'Ganacias/Pérdidas Netas': 'sum'
        }).reset_index()

        fig_ganancia = px.bar(
            ganancia_anual,
            x="Año",
            y="Ganacias/Pérdidas Netas",
            title="Ganancia Neta Anual",
            template="plotly_white",
            text_auto='.2s'
        )
        fig_ganancia.update_traces(
            marker_color='#4CAF50',
            hovertemplate='Año: %{x}<br>Ganancia: %{y:,.2f} USD'
        )
        fig_ganancia.update_layout(yaxis_tickformat=",", yaxis_title="Ganancia Neta (USD)")
        st.plotly_chart(fig_ganancia, use_container_width=True)
        st.markdown("---")

        # Gráfico 3: Drawdown Máximo Anual
        st.markdown("### 📉 Drawdown Máximo Anual")
        drawdown_anual = df[df['Año'].isin(años_seleccionados)].groupby("Año").agg({
            'Drawdown': 'min'
        }).reset_index()

        fig_drawdown = px.bar(
            drawdown_anual,
            x="Año",
            y="Drawdown",
            title="Drawdown Máximo Anual",
            template="plotly_white",
            text_auto='.2s'
        )
        fig_drawdown.update_traces(
            marker_color='#F44336',
            hovertemplate='Año: %{x}<br>Drawdown: %{y:,.2f} USD'
        )
        fig_drawdown.update_layout(yaxis_title="Drawdown (USD)")
        st.plotly_chart(fig_drawdown, use_container_width=True)

    except Exception as e:
        st.error(f"Error al generar comparaciones: {str(e)}")
        st.stop()

# =============================================================================
# 🏁 MENÚ PRINCIPAL
# =============================================================================
pagina = st.sidebar.radio(
    "Selecciona la sección",
    ["📌 KPIs", "📊 Gráficos", "📈 Proyecciones", "⚖️ Comparaciones"]
)

if pagina == "📌 KPIs":
    show_kpis()
elif pagina == "📊 Gráficos":
    show_charts()
elif pagina == "📈 Proyecciones":
    show_projections()
elif pagina == "⚖️ Comparaciones":
    show_comparisons()































