import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from PIL import Image
import base64
import os
import requests
from io import BytesIO
import calendar

# =============================================================================
# 🎨 CONFIGURACIÓN DE PÁGINA Y ESTILOS
# =============================================================================

st.set_page_config(
    page_title="FIFI Investment Dashboard",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para diseño premium
st.markdown("""
<style>
    /* Fondo general oscuro premium */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
    }
    
    /* Sidebar premium */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0a0a 0%, #16213e 100%);
        border-right: 1px solid rgba(255,215,0,0.1);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        color: #c0c0c0;
    }
    
    /* Tarjetas de KPI premium */
    .kpi-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 20px;
        padding: 25px;
        margin: 10px 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        border: 1px solid rgba(255,215,0,0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, #ffd700, #f7971e);
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.8);
        border-color: rgba(255,215,0,0.3);
    }
    
    .kpi-title {
        color: #c0c0c0;
        font-size: 14px;
        font-weight: 500;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    
    .kpi-value {
        color: #ffffff;
        font-size: 32px;
        font-weight: 700;
        margin: 10px 0 5px 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .kpi-sub {
        color: #ffd700;
        font-size: 13px;
        font-weight: 400;
        margin-top: 8px;
    }
    
    .kpi-icon {
        font-size: 24px;
        margin-right: 10px;
    }
    
    /* Header premium */
    .premium-header {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 50%, #1a1a2e 100%);
        padding: 25px 30px;
        border-radius: 15px;
        border: 1px solid rgba(255,215,0,0.1);
        margin-bottom: 30px;
        text-align: center;
    }
    
    .premium-header h1 {
        color: #ffffff;
        font-weight: 300;
        font-size: 36px;
    }
    
    .premium-header h1 span {
        color: #ffd700;
        font-weight: 700;
    }
    
    .premium-header p {
        color: #c0c0c0;
        font-size: 16px;
        margin-top: 10px;
    }
    
    /* Botones premium */
    .stButton > button {
        background: linear-gradient(135deg, #ffd700 0%, #f7971e 100%);
        color: #000000;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 12px 30px;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(255,215,0,0.3);
    }
    
    /* Inputs premium */
    [data-testid="stTextInput"] input {
        background: #1a1a2e;
        border: 1px solid rgba(255,215,0,0.2);
        border-radius: 10px;
        color: #ffffff;
        padding: 12px;
    }
    
    [data-testid="stTextInput"] input:focus {
        border-color: #ffd700;
        box-shadow: 0 0 15px rgba(255,215,0,0.1);
    }
    
    /* Selectbox premium */
    [data-testid="stSelectbox"] {
        background: #1a1a2e;
        border-radius: 10px;
    }
    
    /* Tablas premium */
    [data-testid="stDataFrame"] {
        background: transparent;
    }
    
    .dataframe {
        background: #1a1a2e !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255,215,0,0.1) !important;
        color: #ffffff !important;
    }
    
    /* Scrollbar personalizada */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0a0a0a;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #ffd700, #f7971e);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #ffd700;
    }
    
    /* Login container */
    .login-container {
        max-width: 450px;
        margin: 100px auto;
        padding: 40px;
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 20px;
        border: 1px solid rgba(255,215,0,0.1);
        box-shadow: 0 20px 60px rgba(0,0,0,0.8);
    }
    
    .login-title {
        text-align: center;
        color: #ffffff;
        font-size: 28px;
        font-weight: 300;
        margin-bottom: 10px;
    }
    
    .login-title span {
        color: #ffd700;
        font-weight: 700;
    }
    
    .login-subtitle {
        text-align: center;
        color: #c0c0c0;
        font-size: 14px;
        margin-bottom: 30px;
    }
    
    /* Badge premium */
    .badge {
        background: linear-gradient(135deg, #ffd700, #f7971e);
        color: #000000;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# 🔐 SISTEMA DE AUTENTICACIÓN HÍBRIDO
# =============================================================================

def check_password_hybrid():
    """
    Autenticación híbrida:
    - En desarrollo local: usa secrets.toml
    - En producción (Render): usa variables de entorno
    """
    
    if st.session_state.get("authenticated"):
        return True
    
    # Mostrar login premium
    st.markdown("""
    <div style="text-align: center; padding: 30px 0;">
        <h1 style="color: #ffd700; font-size: 52px; font-weight: 700; margin-bottom: 5px;">🏛️ FIFI</h1>
        <p style="color: #c0c0c0; font-size: 20px; font-weight: 300;">Investment Dashboard</p>
        <div style="width: 60px; height: 3px; background: linear-gradient(90deg, #ffd700, #f7971e); margin: 15px auto;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login_form"):
                st.markdown("""
                <div style="background: #1a1a2e; padding: 30px; border-radius: 20px; border: 1px solid rgba(255,215,0,0.1);">
                """, unsafe_allow_html=True)
                
                username = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
                password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingresa tu contraseña")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                submitted = st.form_submit_button("🔓 Acceder al Dashboard", use_container_width=True)
                
                if submitted:
                    if username and password:
                        authenticated = False
                        archivo_usuario = None
                        
                        # 1. PRIMERO: Intentar con secrets.toml (desarrollo local)
                        try:
                            credenciales_validas = st.secrets["inversionistas"]
                            archivos_usuarios = st.secrets["archivos_usuarios"]
                            
                            if username in credenciales_validas and credenciales_validas[username] == password:
                                authenticated = True
                                archivo_usuario = archivos_usuarios.get(username, f"{username}.xlsx")
                        except:
                            pass
                        
                        # 2. SEGUNDO: Si falló, intentar con variables de entorno (Render)
                        if not authenticated:
                            env_user_var = f"USER_{username.upper()}"
                            env_password = os.getenv(env_user_var)
                            
                            if env_password and env_password == password:
                                authenticated = True
                                env_file_var = f"FILE_{username.upper()}"
                                archivo_usuario = os.getenv(env_file_var, f"{username}.xlsx")
                        
                        # 3. Si autenticó correctamente
                        if authenticated and archivo_usuario:
                            st.session_state["authenticated"] = True
                            st.session_state["username"] = username
                            
                            # Determinar si es URL o archivo local
                            if archivo_usuario.startswith(("http://", "https://")):
                                st.session_state["archivo_usuario"] = archivo_usuario
                            else:
                                st.session_state["archivo_usuario"] = os.path.join("data", archivo_usuario)
                            
                            st.rerun()
                        else:
                            st.error("❌ Credenciales incorrectas. Por favor, verifica tus datos.")
                    else:
                        st.warning("⚠️ Por favor, completa ambos campos.")
    
    # Mostrar footer
    st.markdown("""
    <div style="position: fixed; bottom: 20px; width: 100%; text-align: center; color: #555; font-size: 12px;">
        FIFI Investments © 2026 - Todos los derechos reservados
    </div>
    """, unsafe_allow_html=True)
    
    return False

# Verificar autenticación
if not check_password_hybrid():
    st.stop()

# =============================================================================
# 🚀 CONFIGURACIÓN POST-LOGIN
# =============================================================================

# Barra lateral con información del usuario
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <div style="background: linear-gradient(135deg, #ffd700, #f7971e); width: 60px; height: 60px; border-radius: 50%; margin: 0 auto; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 700; color: #000;">
            {st.session_state['username'][0].upper()}
        </div>
        <h3 style="color: #ffffff; margin-top: 10px;">{st.session_state['username']}</h3>
        <span class="badge">🟢 Activo</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ⚙️ Configuración")
    st.caption("Última actualización: " + datetime.now().strftime("%d/%m/%Y %H:%M"))

# Logo
def load_logo():
    try:
        logo_path = os.path.join("logo.jpg")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_b64 = base64.b64encode(f.read()).decode()
            st.markdown(f"""
                <div style='text-align: center; padding: 10px 0 20px 0;'>
                    <img src='data:image/jpeg;base64,{logo_b64}' style='width:180px;'/>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Logo no encontrado")
    except:
        pass

load_logo()

# =============================================================================
# 📁 CARGA DE DATOS MEJORADA
# =============================================================================

@st.cache_data(ttl=3600)
def load_user_data(file_path):
    """Carga los datos del usuario con manejo robusto de errores."""
    try:
        if file_path.startswith(("http://", "https://")):
            response = requests.get(file_path)
            df = pd.read_excel(BytesIO(response.content), sheet_name="Histórico")
        else:
            if not os.path.exists(file_path):
                alt_path = os.path.join("data", os.path.basename(file_path))
                if os.path.exists(alt_path):
                    file_path = alt_path
                else:
                    raise FileNotFoundError(f"No se encontró el archivo: {file_path}")
            df = pd.read_excel(file_path, sheet_name="Histórico")
        
        # Validación de columnas requeridas
        required_columns = ["Fecha", "Capital Invertido", "Ganacias/Pérdidas Netas"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Columna requerida no encontrada: {col}")
        
        df = df.dropna(subset=["Fecha"])
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df["Mes"] = df["Fecha"].dt.to_period("M")
        
        # Asegurar que las columnas numéricas sean float
        numeric_columns = [
            "Capital Invertido", "Aumento Capital", "Retiro de Fondos",
            "Ganacias/Pérdidas Brutas", "Ganacias/Pérdidas Brutas Acumuladas",
            "Comisiones 10 %", "Comisiones Pagadas",
            "Ganacias/Pérdidas Netas", "Ganacias/Pérdidas Netas Acumuladas",
            "Ganacias/Pérdidas Promedio Diario", "Beneficio en %"
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df.sort_values("Fecha")
        
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {str(e)}")
        st.stop()

# Cargar datos con manejo de errores
try:
    archivo_usuario = st.session_state.get("archivo_usuario", "")
    if not archivo_usuario:
        st.error("No se ha configurado archivo para este usuario")
        st.stop()
    
    df = load_user_data(archivo_usuario)
    
    with st.sidebar:
        st.success(f"📊 Datos cargados correctamente")
        st.caption(f"📁 {os.path.basename(archivo_usuario)}")
        st.caption(f"📅 {len(df)} registros")
    
except Exception as e:
    st.error(f"❌ Error al cargar datos del usuario: {str(e)}")
    st.stop()

# =============================================================================
# 📌 SECCIÓN DE KPIs PREMIUM (CORREGIDA)
# =============================================================================

def styled_kpi_premium(title, value, subtitle="", icon="", color="#ffd700", tooltip=""):
    """KPI con diseño premium"""
    
    st.markdown(f"""
    <div class="kpi-card" title="{tooltip}">
        <div class="kpi-title">
            <span class="kpi-icon">{icon}</span> {title}
        </div>
        <div class="kpi-value" style="color: {color};">{value}</div>
        <div class="kpi-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def show_premium_kpis():
    """Muestra los KPIs con diseño premium - VERSIÓN CORREGIDA"""
    
    st.markdown(f"""
    <div class="premium-header">
        <h1>📊 <span>KPI</span> Dashboard</h1>
        <p>Indicadores clave de desempeño al <span style="color: #ffd700;">{datetime.now().strftime('%d/%m/%Y')}</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Validación de columnas
    required_columns = ["Fecha", "Capital Invertido", "Ganacias/Pérdidas Netas"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"❌ Columnas faltantes: {', '.join(missing_cols)}")
        st.stop()
    
    try:
        # Preprocesamiento
        df_copy = df.copy()
        df_copy["Mes"] = df_copy["Fecha"].dt.to_period("M")
        
        # Calcular acumulados si no existen
        if "Ganacias/Pérdidas Netas Acumuladas" not in df_copy.columns:
            df_copy["Ganacias/Pérdidas Netas Acumuladas"] = df_copy["Ganacias/Pérdidas Netas"].cumsum()
        
        df_copy["Acumulado"] = df_copy["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
        df_copy["MaxAcum"] = df_copy["Acumulado"].cummax()
        df_copy["Drawdown"] = df_copy["Acumulado"] - df_copy["MaxAcum"]
        
        # Obtener datos básicos
        capital_actual = df_copy["Capital Invertido"].dropna().iloc[-1]
        capital_inicial = df_copy["Capital Invertido"].dropna().iloc[0]
        
        # ===== CÁLCULOS CORREGIDOS =====
        
        # 1. GANANCIA NETA TOTAL
        ganancia_neta_total = df_copy["Ganacias/Pérdidas Netas"].sum()
        
        # 2. RETIROS TOTALES (NUEVO KPI)
        total_retiros = df_copy["Retiro de Fondos"].sum() if "Retiro de Fondos" in df_copy.columns else 0
        
        # 3. ROI (Retorno sobre Inversión)
        # ROI = (Ganancia Neta Total / Capital Invertido) * 100
        if capital_actual > 0:
            roi = (ganancia_neta_total / capital_actual) * 100
        else:
            roi = 0
        
        # 4. RENTABILIDAD MENSUAL PROMEDIO (CORREGIDO)
        # Se calcula como el promedio de los Beneficios en % de cada mes
        if "Beneficio en %" in df_copy.columns:
            # Agrupar por mes y calcular el beneficio promedio de cada mes
            monthly_returns = df_copy.groupby("Mes")["Beneficio en %"].mean()
            # Promedio de los retornos mensuales
            avg_monthly_return = monthly_returns.mean() * 100  # Convertir a porcentaje
        else:
            avg_monthly_return = 0
        
        # 5. DRAWDOWN MÁXIMO
        max_drawdown = df_copy["Drawdown"].min() if "Drawdown" in df_copy.columns else 0
        
        # 6. RATING DE RIESGO (basado en drawdown y consistencia)
        if max_drawdown != 0:
            risk_ratio = abs(max_drawdown / capital_actual)
            if risk_ratio < 0.05:
                rating = "⭐⭐⭐⭐⭐"
                risk_text = "Perfil Muy Conservador"
            elif risk_ratio < 0.10:
                rating = "⭐⭐⭐⭐"
                risk_text = "Perfil Conservador"
            elif risk_ratio < 0.20:
                rating = "⭐⭐⭐"
                risk_text = "Perfil Moderado"
            elif risk_ratio < 0.30:
                rating = "⭐⭐"
                risk_text = "Perfil Agresivo"
            else:
                rating = "⭐"
                risk_text = "Perfil Muy Agresivo"
        else:
            rating = "⭐⭐⭐⭐⭐"
            risk_text = "Perfil Muy Conservador"
        
        # 7. MEJOR Y PEOR MES
        if "Beneficio en %" in df_copy.columns:
            mejor_mes_idx = df_copy["Beneficio en %"].idxmax()
            peor_mes_idx = df_copy["Beneficio en %"].idxmin()
            mejor_mes = df_copy.loc[mejor_mes_idx, "Fecha"].strftime("%b %Y") if not pd.isna(mejor_mes_idx) else "N/A"
            mejor_mes_valor = df_copy.loc[mejor_mes_idx, "Beneficio en %"] * 100 if not pd.isna(mejor_mes_idx) else 0
            peor_mes = df_copy.loc[peor_mes_idx, "Fecha"].strftime("%b %Y") if not pd.isna(peor_mes_idx) else "N/A"
            peor_mes_valor = df_copy.loc[peor_mes_idx, "Beneficio en %"] * 100 if not pd.isna(peor_mes_idx) else 0
        else:
            mejor_mes = "N/A"
            mejor_mes_valor = 0
            peor_mes = "N/A"
            peor_mes_valor = 0
        
        # 8. TOTAL DE MESES
        total_meses = len(df_copy["Mes"].unique())
        
        # 9. CAGR (Tasa de Crecimiento Anual Compuesta)
        if total_meses > 0 and capital_inicial > 0 and capital_actual > 0:
            cagr = (((capital_actual / capital_inicial) ** (12 / total_meses)) - 1) * 100
        else:
            cagr = 0
        
        # ===== FILA 1: KPIs PRINCIPALES =====
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            styled_kpi_premium(
                "Capital Actual",
                f"${capital_actual:,.0f}",
                f"▲ +{((capital_actual/capital_inicial - 1) * 100):.1f}% desde inicio",
                "💰",
                "#ffd700"
            )
        
        with col2:
            styled_kpi_premium(
                "Rentabilidad Total (ROI)",
                f"{roi:.1f}%",
                f"📈 CAGR: {cagr:.1f}% anual",
                "📈",
                "#4CAF50" if roi > 0 else "#f44336"
            )
        
        with col3:
            styled_kpi_premium(
                "Drawdown Máximo",
                f"${abs(max_drawdown):,.0f}",
                f"📉 {abs(max_drawdown/capital_actual * 100):.1f}% del capital",
                "📉",
                "#f44336"
            )
        
        with col4:
            styled_kpi_premium(
                "Rating de Riesgo",
                rating,
                risk_text,
                "🛡️",
                "#ffd700"
            )
        
        st.markdown("---")
        
        # ===== FILA 2: KPIs SECUNDARIOS =====
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            # RENTABILIDAD MENSUAL PROMEDIO (CORREGIDO)
            styled_kpi_premium(
                "Rentabilidad Mensual Prom",
                f"{avg_monthly_return:.2f}%",
                f"📊 Basado en {total_meses} meses",
                "📊",
                "#2196F3"
            )
        
        with col6:
            styled_kpi_premium(
                "Capital Inicial",
                f"${capital_inicial:,.0f}",
                f"📅 {df_copy['Fecha'].min().strftime('%b %Y')}",
                "🏦",
                "#9E9E9E"
            )
        
        with col7:
            styled_kpi_premium(
                "Ganancia Neta Total",
                f"${ganancia_neta_total:,.0f}",
                f"▲ +{(ganancia_neta_total/capital_actual * 100):.1f}% sobre capital",
                "📊",
                "#4CAF50" if ganancia_neta_total > 0 else "#f44336"
            )
        
        with col8:
            # RETIROS TOTALES (NUEVO KPI)
            styled_kpi_premium(
                "Retiros Totales",
                f"${total_retiros:,.0f}",
                f"💸 {total_retiros/capital_actual * 100:.1f}% del capital retirado",
                "💸",
                "#FF9800"
            )
        
        st.markdown("---")
        
        # ===== FILA 3: KPIs ADICIONALES =====
        col9, col10, col11, col12 = st.columns(4)
        
        with col9:
            styled_kpi_premium(
                "Mejor Mes",
                mejor_mes,
                f"▲ {mejor_mes_valor:.2f}%",
                "🏆",
                "#4CAF50"
            )
        
        with col10:
            styled_kpi_premium(
                "Peor Mes",
                peor_mes,
                f"▼ {peor_mes_valor:.2f}%",
                "⚠️",
                "#f44336"
            )
        
        with col11:
            # Índice de Sharpe simplificado (Rentabilidad / Riesgo)
            if max_drawdown != 0:
                sharpe_ratio = avg_monthly_return / abs(max_drawdown/capital_actual * 100) if avg_monthly_return > 0 else 0
                sharpe_display = f"{sharpe_ratio:.2f}"
            else:
                sharpe_display = "N/A"
            
            styled_kpi_premium(
                "Ratio Sharpe",
                sharpe_display,
                "Rendimiento ajustado por riesgo",
                "📊",
                "#FF9800"
            )
        
        with col12:
            styled_kpi_premium(
                "Días en el Mercado",
                f"{(df_copy['Fecha'].max() - df_copy['Fecha'].min()).days}",
                f"Desde {df_copy['Fecha'].min().strftime('%d/%m/%Y')}",
                "📅",
                "#2196F3"
            )
            
    except Exception as e:
        st.error(f"❌ Error al calcular KPIs: {str(e)}")
        st.stop()

# =============================================================================
# 📊 SECCIÓN DE GRÁFICOS PREMIUM
# =============================================================================

def show_premium_charts():
    """Muestra gráficos con diseño premium"""
    
    st.markdown("""
    <div class="premium-header">
        <h1>📈 <span>Visualizaciones</span> Financieras</h1>
        <p>Análisis detallado de la evolución de la inversión</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Preprocesamiento
        df_copy = df.copy()
        df_copy["Mes"] = df_copy["Fecha"].dt.to_period("M")
        
        # Calcular acumulados si no existen
        if "Ganacias/Pérdidas Netas Acumuladas" not in df_copy.columns:
            df_copy["Ganacias/Pérdidas Netas Acumuladas"] = df_copy["Ganacias/Pérdidas Netas"].cumsum()
        
        df_copy["Acumulado"] = df_copy["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
        df_copy["MaxAcum"] = df_copy["Acumulado"].cummax()
        df_copy["Drawdown"] = df_copy["Acumulado"] - df_copy["MaxAcum"]
        
        # Gráfico 1: Evolución del Capital y Drawdown
        st.markdown("### 📊 Evolución del Capital y Drawdown")
        
        fig1 = go.Figure()
        
        # Capital invertido
        fig1.add_trace(go.Scatter(
            x=df_copy["Fecha"],
            y=df_copy["Capital Invertido"],
            mode='lines+markers',
            name='Capital Invertido',
            line=dict(color='#ffd700', width=3),
            marker=dict(size=6, color='#ffd700'),
            hovertemplate='%{x}<br>Capital: $%{y:,.0f}<extra></extra>'
        ))
        
        # Drawdown
        fig1.add_trace(go.Scatter(
            x=df_copy["Fecha"],
            y=df_copy["Drawdown"],
            mode='lines',
            name='Drawdown',
            line=dict(color='#f44336', width=2, dash='dash'),
            fill='tozeroy',
            fillcolor='rgba(244, 67, 54, 0.2)',
            hovertemplate='%{x}<br>Drawdown: $%{y:,.0f}<extra></extra>'
        ))
        
        fig1.update_layout(
            template='plotly_dark',
            height=500,
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(0,0,0,0.5)'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Fecha',
            yaxis_title='Valor ($)',
            yaxis=dict(tickformat='$,.0f')
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown("---")
        
        # Gráfico 2: Ganancia Neta Acumulada
        st.markdown("### 📈 Ganancia Neta Acumulada")
        
        fig2 = go.Figure()
        
        fig2.add_trace(go.Scatter(
            x=df_copy["Fecha"],
            y=df_copy["Acumulado"],
            mode='lines+markers',
            name='Ganancia Acumulada',
            line=dict(color='#4CAF50', width=3),
            marker=dict(size=6, color='#4CAF50'),
            fill='tozeroy',
            fillcolor='rgba(76, 175, 80, 0.2)',
            hovertemplate='%{x}<br>Ganancia: $%{y:,.0f}<extra></extra>'
        ))
        
        fig2.update_layout(
            template='plotly_dark',
            height=400,
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(0,0,0,0.5)'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Fecha',
            yaxis_title='Ganancia ($)',
            yaxis=dict(tickformat='$,.0f')
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("---")
        
        # Gráfico 3: Rentabilidad Mensual (Heatmap)
        st.markdown("### 🌡️ Rentabilidad Mensual - Heatmap")
        
        if "Beneficio en %" in df_copy.columns:
            df_copy["Año"] = df_copy["Fecha"].dt.year
            df_copy["MesNombre"] = df_copy["Fecha"].dt.strftime("%b")
            df_copy["MesNum"] = df_copy["Fecha"].dt.month
            
            # Pivot para heatmap
            pivot_rent = df_copy.pivot_table(
                values="Beneficio en %",
                index="Año",
                columns="MesNum",
                aggfunc="mean"
            ) * 100
            
            # Renombrar columnas a nombres de meses
            pivot_rent.columns = [calendar.month_abbr[i] for i in pivot_rent.columns]
            
            fig3 = go.Figure(data=go.Heatmap(
                z=pivot_rent.values,
                x=pivot_rent.columns,
                y=pivot_rent.index,
                colorscale='RdYlGn',
                zmid=0,
                text=pivot_rent.values.round(2),
                texttemplate='%{text}%',
                textfont={"size": 12, "color": "white"},
                hovertemplate='<b>%{y}</b><br>%{x}<br>Rentabilidad: %{z:.2f}%<extra></extra>'
            ))
            
            fig3.update_layout(
                template='plotly_dark',
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title='Mes',
                yaxis_title='Año',
                xaxis=dict(side='top')
            )
            
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown("---")
        
        # Gráfico 4: Distribución de Retornos Mensuales
        st.markdown("### 📊 Distribución de Retornos Mensuales")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if "Beneficio en %" in df_copy.columns:
                # Histograma
                fig4 = go.Figure()
                
                fig4.add_trace(go.Histogram(
                    x=df_copy["Beneficio en %"] * 100,
                    nbinsx=20,
                    marker=dict(
                        color='#ffd700',
                        line=dict(color='#000', width=1)
                    ),
                    hovertemplate='Rentabilidad: %{x:.2f}%<br>Frecuencia: %{y}<extra></extra>'
                ))
                
                fig4.update_layout(
                    template='plotly_dark',
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis_title='Rentabilidad (%)',
                    yaxis_title='Frecuencia',
                    showlegend=False
                )
                
                st.plotly_chart(fig4, use_container_width=True)
        
        with col2:
            if "Beneficio en %" in df_copy.columns:
                # Boxplot
                fig5 = go.Figure()
                
                fig5.add_trace(go.Box(
                    y=df_copy["Beneficio en %"] * 100,
                    name='Retornos Mensuales',
                    marker_color='#ffd700',
                    boxmean='sd',
                    hovertemplate='Mediana: %{median:.2f}%<br>Media: %{mean:.2f}%<br>Mín: %{min:.2f}%<br>Máx: %{max:.2f}%<extra></extra>'
                ))
                
                fig5.update_layout(
                    template='plotly_dark',
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    yaxis_title='Rentabilidad (%)',
                    showlegend=False
                )
                
                st.plotly_chart(fig5, use_container_width=True)
        
        st.markdown("---")
        
        # Gráfico 5: Comisiones vs Ganancia Neta
        if "Comisiones Pagadas" in df_copy.columns and "Ganacias/Pérdidas Brutas" in df_copy.columns:
            st.markdown("### 💰 Análisis de Comisiones")
            
            comisiones_mensuales = df_copy.groupby("Mes").agg({
                "Comisiones Pagadas": "sum",
                "Ganacias/Pérdidas Brutas": "sum"
            }).reset_index()
            comisiones_mensuales["Mes"] = comisiones_mensuales["Mes"].astype(str)
            
            fig6 = go.Figure()
            
            # Barras de comisiones
            fig6.add_trace(go.Bar(
                x=comisiones_mensuales["Mes"],
                y=comisiones_mensuales["Comisiones Pagadas"],
                name='Comisiones',
                marker_color='#f44336',
                hovertemplate='%{x}<br>Comisiones: $%{y:,.0f}<extra></extra>'
            ))
            
            # Línea de ganancias
            fig6.add_trace(go.Scatter(
                x=comisiones_mensuales["Mes"],
                y=comisiones_mensuales["Ganacias/Pérdidas Brutas"],
                mode='lines+markers',
                name='Ganancia Bruta',
                line=dict(color='#4CAF50', width=3),
                marker=dict(size=8, color='#4CAF50'),
                hovertemplate='%{x}<br>Ganancia: $%{y:,.0f}<extra></extra>'
            ))
            
            fig6.update_layout(
                template='plotly_dark',
                height=400,
                hovermode='x unified',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(0,0,0,0.5)'
                ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title='Mes',
                yaxis_title='Valor ($)',
                yaxis=dict(tickformat='$,.0f')
            )
            
            st.plotly_chart(fig6, use_container_width=True)
            
    except Exception as e:
        st.error(f"❌ Error al generar gráficos: {str(e)}")
        st.stop()

# =============================================================================
# 📈 SECCIÓN DE PROYECCIONES PREMIUM
# =============================================================================

def show_premium_projections():
    """Muestra proyecciones con diseño premium"""
    
    st.markdown("""
    <div class="premium-header">
        <h1>🚀 <span>Proyección</span> de Inversión</h1>
        <p>Simula el crecimiento de tu capital a futuro</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        capital_actual = df["Capital Invertido"].dropna().iloc[-1]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: #1a1a2e; padding: 20px; border-radius: 15px; border: 1px solid rgba(255,215,0,0.1);">
            """, unsafe_allow_html=True)
            
            aumento_opcion = st.selectbox(
                "📈 Aumento de capital",
                [0, 5, 10, 15, 20, 30, 50],
                format_func=lambda x: f"{x}%"
            )
            
            beneficio_mensual = st.slider(
                "📊 Beneficio mensual estimado",
                min_value=0.0,
                max_value=15.0,
                value=5.0,
                step=0.5,
                format="%.1f%%"
            )
            
            meses_proyeccion = st.slider(
                "📅 Duración de la inversión",
                min_value=1,
                max_value=60,
                value=12,
                format="%d meses"
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            # Mostrar estadísticas rápidas
            capital_proyectado = capital_actual * (1 + aumento_opcion / 100)
            proyeccion = [capital_proyectado * ((1 + beneficio_mensual / 100) ** i) for i in range(meses_proyeccion + 1)]
            
            st.markdown(f"""
            <div style="background: #1a1a2e; padding: 20px; border-radius: 15px; border: 1px solid rgba(255,215,0,0.1); height: 100%;">
                <div style="margin-bottom: 15px;">
                    <div style="color: #c0c0c0; font-size: 14px;">Capital Actual</div>
                    <div style="color: #ffffff; font-size: 24px; font-weight: 700;">${capital_actual:,.0f}</div>
                </div>
                <div style="margin-bottom: 15px;">
                    <div style="color: #c0c0c0; font-size: 14px;">Capital Proyectado</div>
                    <div style="color: #ffd700; font-size: 24px; font-weight: 700;">${capital_proyectado:,.0f}</div>
                </div>
                <div>
                    <div style="color: #c0c0c0; font-size: 14px;">Valor Estimado Final</div>
                    <div style="color: #4CAF50; font-size: 28px; font-weight: 700;">${proyeccion[-1]:,.0f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Gráfico de proyección
        df_proy = pd.DataFrame({
            "Mes": list(range(meses_proyeccion + 1)),
            "Proyección": proyeccion
        })
        
        fig = go.Figure()
        
        # Área de proyección
        fig.add_trace(go.Scatter(
            x=df_proy["Mes"],
            y=df_proy["Proyección"],
            mode='lines+markers',
            name='Proyección',
            line=dict(color='#ffd700', width=3),
            marker=dict(size=8, color='#ffd700'),
            fill='tozeroy',
            fillcolor='rgba(255, 215, 0, 0.2)',
            hovertemplate='Mes %{x}<br>Capital: $%{y:,.0f}<extra></extra>'
        ))
        
        # Añadir línea de tendencia
        z = np.polyfit(df_proy["Mes"], df_proy["Proyección"], 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=df_proy["Mes"],
            y=p(df_proy["Mes"]),
            mode='lines',
            name='Tendencia',
            line=dict(color='rgba(255, 215, 0, 0.3)', width=2, dash='dash')
        ))
        
        fig.update_layout(
            template='plotly_dark',
            height=450,
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(0,0,0,0.5)'
            ),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Meses',
            yaxis_title='Capital Proyectado ($)',
            yaxis=dict(tickformat='$,.0f')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla detallada
        st.markdown("### 📄 Detalle de Proyección")
        
        df_proy_display = df_proy.copy()
        df_proy_display["Proyección"] = df_proy_display["Proyección"].apply(lambda x: f"${x:,.0f}")
        df_proy_display["Crecimiento"] = ["0%"] + [
            f"{(df_proy['Proyección'][i] / df_proy['Proyección'][0] - 1) * 100:.1f}%" 
            for i in range(1, len(df_proy))
        ]
        
        st.dataframe(
            df_proy_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Mes": "Mes",
                "Proyección": "Capital Proyectado",
                "Crecimiento": "Crecimiento %"
            }
        )
        
        # Botón de descarga
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            resumen = pd.DataFrame({
                "Descripción": [
                    "Capital Actual",
                    "% Aumento Capital",
                    "Capital Proyectado",
                    "% Beneficio Mensual",
                    "Meses de Proyección",
                    "Valor Final Estimado",
                    "Crecimiento Total"
                ],
                "Valor": [
                    capital_actual,
                    f"{aumento_opcion}%",
                    capital_proyectado,
                    f"{beneficio_mensual}%",
                    meses_proyeccion,
                    proyeccion[-1],
                    f"{(proyeccion[-1] / capital_proyectado - 1) * 100:.1f}%"
                ]
            })
            resumen.to_excel(writer, index=False, sheet_name="Resumen")
            df_proy.to_excel(writer, index=False, sheet_name="Proyección")
        
        excel_data = output.getvalue()
        
        st.download_button(
            "📥 Descargar Proyección en Excel",
            data=excel_data,
            file_name=f"proyeccion_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"❌ Error al generar proyecciones: {str(e)}")
        st.stop()

# =============================================================================
# ⚖️ SECCIÓN DE COMPARACIONES PREMIUM
# =============================================================================

def show_premium_comparisons():
    """Muestra comparaciones con diseño premium"""
    
    st.markdown("""
    <div class="premium-header">
        <h1>⚖️ <span>Comparaciones</span> Anuales</h1>
        <p>Análisis comparativo de rendimiento por año</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Crear columnas necesarias
        df_copy = df.copy()
        df_copy["Año"] = df_copy["Fecha"].dt.year
        df_copy["MesNombre"] = df_copy["Fecha"].dt.strftime("%b")
        df_copy["MesNum"] = df_copy["Fecha"].dt.month
        
        # Calcular acumulados si no existen
        if "Ganacias/Pérdidas Netas Acumuladas" not in df_copy.columns:
            df_copy["Ganacias/Pérdidas Netas Acumuladas"] = df_copy["Ganacias/Pérdidas Netas"].cumsum()
        
        df_copy["Acumulado"] = df_copy["Ganacias/Pérdidas Netas Acumuladas"].fillna(method="ffill")
        df_copy["MaxAcum"] = df_copy["Acumulado"].cummax()
        df_copy["Drawdown"] = df_copy["Acumulado"] - df_copy["MaxAcum"]
        
        # Selección de años
        años_disponibles = sorted(df_copy["Año"].unique().tolist())
        años_seleccionados = st.multiselect(
            "📅 Selecciona los años a comparar",
            años_disponibles,
            default=años_disponibles[-2:] if len(años_disponibles) > 1 else años_disponibles
        )
        
        if not años_seleccionados:
            st.warning("⚠️ Selecciona al menos un año para comparar")
            st.stop()
        
        # Filtrar datos
        df_filtrado = df_copy[df_copy["Año"].isin(años_seleccionados)]
        
        # Gráfico 1: Comparación de Rentabilidad Mensual
        st.markdown("### 📈 Comparación de Rentabilidad Mensual")
        
        if "Beneficio en %" in df_filtrado.columns:
            comparacion = df_filtrado.groupby(["Año", "MesNum", "MesNombre"]).agg({
                "Beneficio en %": "mean"
            }).reset_index().sort_values(["Año", "MesNum"])
            
            comparacion["Beneficio en %"] *= 100
            
            fig1 = go.Figure()
            
            for año in años_seleccionados:
                data_año = comparacion[comparacion["Año"] == año]
                fig1.add_trace(go.Scatter(
                    x=data_año["MesNombre"],
                    y=data_año["Beneficio en %"],
                    mode='lines+markers',
                    name=f"{año}",
                    line=dict(width=3),
                    marker=dict(size=8),
                    hovertemplate='%{x}<br>Rentabilidad: %{y:.2f}%<extra></extra>'
                ))
            
            fig1.update_layout(
                template='plotly_dark',
                height=400,
                hovermode='x unified',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(0,0,0,0.5)'
                ),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title='Mes',
                yaxis_title='Rentabilidad (%)',
                xaxis=dict(categoryorder='array', categoryarray=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
            )
            
            st.plotly_chart(fig1, use_container_width=True)
            st.markdown("---")
        
        # Gráfico 2: Comparación de Ganancia Anual
        st.markdown("### 💰 Comparación de Ganancia Anual")
        
        ganancia_anual = df_filtrado.groupby("Año").agg({
            "Ganacias/Pérdidas Netas": "sum"
        }).reset_index()
        
        fig2 = go.Figure()
        
        fig2.add_trace(go.Bar(
            x=ganancia_anual["Año"],
            y=ganancia_anual["Ganacias/Pérdidas Netas"],
            marker_color=['#4CAF50' if x > 0 else '#f44336' for x in ganancia_anual["Ganacias/Pérdidas Netas"]],
            text=[f"${x:,.0f}" for x in ganancia_anual["Ganacias/Pérdidas Netas"]],
            textposition='outside',
            hovertemplate='Año: %{x}<br>Ganancia: $%{y:,.0f}<extra></extra>'
        ))
        
        fig2.update_layout(
            template='plotly_dark',
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis_title='Año',
            yaxis_title='Ganancia Neta ($)',
            yaxis=dict(tickformat='$,.0f')
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("---")
        
        # Gráfico 3: Comparación de Drawdown
        if "Drawdown" in df_filtrado.columns:
            st.markdown("### 📉 Comparación de Drawdown Máximo")
            
            drawdown_anual = df_filtrado.groupby("Año").agg({
                "Drawdown": "min"
            }).reset_index()
            
            fig3 = go.Figure()
            
            fig3.add_trace(go.Bar(
                x=drawdown_anual["Año"],
                y=drawdown_anual["Drawdown"],
                marker_color='#f44336',
                text=[f"${x:,.0f}" for x in drawdown_anual["Drawdown"]],
                textposition='outside',
                hovertemplate='Año: %{x}<br>Drawdown: $%{y:,.0f}<extra></extra>'
            ))
            
            fig3.update_layout(
                template='plotly_dark',
                height=400,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title='Año',
                yaxis_title='Drawdown ($)',
                yaxis=dict(tickformat='$,.0f')
            )
            
            st.plotly_chart(fig3, use_container_width=True)
            st.markdown("---")
        
        # Tabla comparativa
        st.markdown("### 📊 Tabla Comparativa Anual")
        
        tabla_comparativa = df_filtrado.groupby("Año").agg({
            "Capital Invertido": "last",
            "Ganacias/Pérdidas Netas": "sum",
            "Beneficio en %": "mean",
            "Retiro de Fondos": "sum" if "Retiro de Fondos" in df_filtrado.columns else lambda x: 0
        }).reset_index()
        
        tabla_comparativa["Beneficio en %"] = tabla_comparativa["Beneficio en %"] * 100
        tabla_comparativa["ROI"] = (tabla_comparativa["Ganacias/Pérdidas Netas"] / tabla_comparativa["Capital Invertido"]) * 100
        
        tabla_comparativa_display = tabla_comparativa.copy()
        tabla_comparativa_display["Capital Invertido"] = tabla_comparativa_display["Capital Invertido"].apply(lambda x: f"${x:,.0f}")
        tabla_comparativa_display["Ganacias/Pérdidas Netas"] = tabla_comparativa_display["Ganacias/Pérdidas Netas"].apply(lambda x: f"${x:,.0f}")
        tabla_comparativa_display["Beneficio en %"] = tabla_comparativa_display["Beneficio en %"].apply(lambda x: f"{x:.2f}%")
        tabla_comparativa_display["ROI"] = tabla_comparativa_display["ROI"].apply(lambda x: f"{x:.2f}%")
        
        if "Retiro de Fondos" in tabla_comparativa_display.columns:
            tabla_comparativa_display["Retiro de Fondos"] = tabla_comparativa_display["Retiro de Fondos"].apply(lambda x: f"${x:,.0f}")
        
        column_names = ["Año", "Capital Final", "Ganancia Neta", "Rentabilidad Prom.", "ROI Anual"]
        if "Retiro de Fondos" in tabla_comparativa_display.columns:
            column_names.append("Retiros")
        
        tabla_comparativa_display.columns = column_names
        
        st.dataframe(
            tabla_comparativa_display,
            use_container_width=True,
            hide_index=True
        )
        
        # Estadísticas adicionales
        st.markdown("### 📈 Análisis de Rendimiento")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            mejor_año = tabla_comparativa.loc[tabla_comparativa["Ganacias/Pérdidas Netas"].idxmax()]
            st.markdown(f"""
            <div style="background: #1a1a2e; padding: 20px; border-radius: 15px; border: 1px solid rgba(76, 175, 80, 0.3);">
                <div style="color: #c0c0c0; font-size: 14px;">🏆 Mejor Año</div>
                <div style="color: #4CAF50; font-size: 24px; font-weight: 700;">{int(mejor_año['Año'])}</div>
                <div style="color: #c0c0c0; font-size: 14px;">Ganancia: ${mejor_año['Ganacias/Pérdidas Netas']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            peor_año = tabla_comparativa.loc[tabla_comparativa["Ganacias/Pérdidas Netas"].idxmin()]
            st.markdown(f"""
            <div style="background: #1a1a2e; padding: 20px; border-radius: 15px; border: 1px solid rgba(244, 67, 54, 0.3);">
                <div style="color: #c0c0c0; font-size: 14px;">⚠️ Peor Año</div>
                <div style="color: #f44336; font-size: 24px; font-weight: 700;">{int(peor_año['Año'])}</div>
                <div style="color: #c0c0c0; font-size: 14px;">Ganancia: ${peor_año['Ganacias/Pérdidas Netas']:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            promedio_anual = tabla_comparativa["Ganacias/Pérdidas Netas"].mean()
            st.markdown(f"""
            <div style="background: #1a1a2e; padding: 20px; border-radius: 15px; border: 1px solid rgba(255, 215, 0, 0.3);">
                <div style="color: #c0c0c0; font-size: 14px;">📊 Ganancia Promedio Anual</div>
                <div style="color: #ffd700; font-size: 24px; font-weight: 700;">${promedio_anual:,.0f}</div>
                <div style="color: #c0c0c0; font-size: 14px;">Basado en {len(tabla_comparativa)} años</div>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"❌ Error al generar comparaciones: {str(e)}")
        st.stop()

# =============================================================================
# 🏁 MENÚ PRINCIPAL PREMIUM
# =============================================================================

# Sidebar navigation premium
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📋 Navegación")
    
    pagina = st.radio(
        "",
        ["📌 KPIs", "📊 Gráficos", "📈 Proyecciones", "⚖️ Comparaciones"],
        index=0,
        format_func=lambda x: x
    )
    
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #555; font-size: 12px; padding: 10px 0;">
        <div>FIFI Investments</div>
        <div>v2.0 - Premium</div>
    </div>
    """, unsafe_allow_html=True)

# Mostrar sección seleccionada
if pagina == "📌 KPIs":
    show_premium_kpis()
elif pagina == "📊 Gráficos":
    show_premium_charts()
elif pagina == "📈 Proyecciones":
    show_premium_projections()
elif pagina == "⚖️ Comparaciones":
    show_premium_comparisons()
