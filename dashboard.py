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
# 🎨 CONFIGURACIÓN DE PÁGINA Y ESTILOS - VERSIÓN LEGIBLE
# =============================================================================

st.set_page_config(
    page_title="FIFI Investment Dashboard",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado - Estilo elegante y LEGIBLE
st.markdown("""
<style>
    /* Fondo principal - Blanco puro para máxima legibilidad */
    .stApp {
        background: #ffffff;
    }
    
    /* Sidebar elegante - Azul profundo */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1a2e 0%, #1a2a3f 100%);
        border-right: 1px solid rgba(255,255,255,0.05);
        padding-top: 20px;
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        color: #e8e8e8;
    }
    
    [data-testid="stSidebar"] .stCaption {
        color: #a0b0c0;
    }
    
    /* Tarjetas de KPI - Blancas con sombra sutil */
    .kpi-card {
        background: #ffffff;
        border-radius: 10px;
        padding: 14px 18px 16px 18px;
        margin: 5px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #eef0f2;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
        min-height: 78px;
    }
    
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2.5px;
        background: linear-gradient(90deg, #2c6e8f, #4a8db7);
        opacity: 0.7;
    }
    
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(44, 110, 143, 0.10);
        border-color: rgba(44, 110, 143, 0.15);
    }
    
    .kpi-title {
        color: #6b7a8a;
        font-size: 10.5px;
        font-weight: 600;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .kpi-title .help-icon {
        color: #a0b0c0;
        font-size: 12px;
        cursor: help;
        margin-left: 6px;
        opacity: 0.5;
        transition: opacity 0.3s ease;
    }
    
    .kpi-title .help-icon:hover {
        opacity: 1;
        color: #2c6e8f;
    }
    
    .kpi-value {
        color: #1a2634;
        font-size: 22px;
        font-weight: 700;
        margin: 2px 0 2px 0;
        letter-spacing: -0.2px;
    }
    
    .kpi-sub {
        color: #8a9aa8;
        font-size: 11px;
        font-weight: 400;
        margin-top: 2px;
    }
    
    .kpi-icon {
        font-size: 15px;
        margin-right: 5px;
    }
    
    /* Header elegante */
    .premium-header {
        background: #f8f9fa;
        padding: 18px 28px;
        border-radius: 10px;
        border: 1px solid #eef0f2;
        margin-bottom: 22px;
        text-align: center;
    }
    
    .premium-header h1 {
        color: #1a2634;
        font-weight: 300;
        font-size: 26px;
        letter-spacing: -0.3px;
        margin: 0;
    }
    
    .premium-header h1 span {
        color: #2c6e8f;
        font-weight: 600;
    }
    
    .premium-header p {
        color: #6b7a8a;
        font-size: 14px;
        margin-top: 4px;
        font-weight: 400;
    }
    
    .premium-header .sub-info {
        font-size: 12px;
        color: #8a9aa8;
        margin-top: 2px;
    }
    
    /* Botones elegantes en sidebar */
    .stButton > button {
        background: transparent;
        color: #c8d0d8;
        font-weight: 400;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 8px;
        padding: 9px 16px;
        transition: all 0.3s ease;
        font-size: 13px;
        letter-spacing: 0.3px;
        width: 100%;
        text-align: left;
        font-family: 'Inter', sans-serif;
    }
    
    .stButton > button:hover {
        background: rgba(255,255,255,0.06);
        border-color: rgba(255,255,255,0.12);
        transform: translateX(3px);
        color: #ffffff;
    }
    
    .stButton > button:active {
        background: rgba(255,255,255,0.10);
    }
    
    /* Botón activo en sidebar */
    .stButton > button[data-testid="baseButton-secondary"] {
        background: rgba(255,255,255,0.06);
        border-color: rgba(255,255,255,0.12);
        color: #ffffff;
    }
    
    /* Botón de cerrar sesión */
    .logout-btn > button {
        color: #d4a0a0;
        border-color: rgba(212, 160, 160, 0.08);
    }
    
    .logout-btn > button:hover {
        background: rgba(212, 160, 160, 0.06);
        border-color: rgba(212, 160, 160, 0.15);
        color: #d4a0a0;
    }
    
    /* Inputs elegantes */
    [data-testid="stTextInput"] input {
        background: #f8f9fa;
        border: 1px solid #e8eaec;
        border-radius: 8px;
        color: #1a2634;
        padding: 10px 14px;
        font-size: 14px;
    }
    
    [data-testid="stTextInput"] input:focus {
        border-color: #2c6e8f;
        box-shadow: 0 0 0 3px rgba(44, 110, 143, 0.08);
    }
    
    /* Selectbox elegante */
    [data-testid="stSelectbox"] {
        background: #f8f9fa;
        border-radius: 8px;
    }
    
    [data-testid="stSelectbox"] select {
        color: #1a2634;
    }
    
    /* Tablas elegantes */
    [data-testid="stDataFrame"] {
        background: transparent;
    }
    
    .dataframe {
        background: #ffffff !important;
        border-radius: 10px !important;
        border: 1px solid #eef0f2 !important;
        color: #1a2634 !important;
        font-size: 13px !important;
    }
    
    /* Scrollbar elegante */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #f0f0f0;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #2c6e8f, #4a8db7);
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #2c6e8f;
    }
    
    /* Login elegante y legible */
    .login-container {
        max-width: 420px;
        margin: 60px auto;
        padding: 35px 40px 40px 40px;
        background: #ffffff;
        border-radius: 14px;
        border: 1px solid #eef0f2;
        box-shadow: 0 20px 60px rgba(0,0,0,0.06);
    }
    
    .login-title {
        text-align: center;
        color: #1a2634;
        font-size: 26px;
        font-weight: 300;
        margin-bottom: 4px;
    }
    
    .login-title span {
        color: #2c6e8f;
        font-weight: 600;
    }
    
    .login-subtitle {
        text-align: center;
        color: #6b7a8a;
        font-size: 13px;
        margin-bottom: 25px;
        font-weight: 400;
    }
    
    /* Badge elegante */
    .badge {
        background: rgba(44, 110, 143, 0.08);
        color: #2c6e8f;
        padding: 2px 12px;
        border-radius: 12px;
        font-size: 10.5px;
        font-weight: 500;
        display: inline-block;
        border: 1px solid rgba(44, 110, 143, 0.08);
    }
    
    /* Avatar en sidebar */
    .avatar {
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: linear-gradient(135deg, #2c6e8f, #4a8db7);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
        font-weight: 600;
        color: #ffffff;
        margin: 0 auto 8px auto;
    }
    
    /* Logo en sidebar */
    .sidebar-logo {
        text-align: center;
        padding: 8px 0 16px 0;
        border-bottom: 1px solid rgba(255,255,255,0.04);
        margin-bottom: 16px;
    }
    
    .sidebar-logo img {
        max-width: 110px;
        height: auto;
        opacity: 0.9;
    }
    
    .sidebar-logo .logo-text {
        color: #c8d0d8;
        font-size: 15px;
        font-weight: 300;
        margin-top: 4px;
        letter-spacing: 2px;
    }
    
    .sidebar-logo .logo-text span {
        color: #5a9abb;
        font-weight: 400;
    }
    
    /* Separador elegante */
    .sidebar-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.04), transparent);
        margin: 12px 0;
    }
    
    /* Navegación en sidebar */
    .nav-section-title {
        color: #6a7a8a;
        font-size: 9px;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        padding: 8px 0 6px 0;
        opacity: 0.5;
    }
    
    /* Estilo para sliders */
    [data-testid="stSlider"] {
        color: #1a2634;
    }
    
    [data-testid="stSlider"] .stSlider {
        color: #2c6e8f;
    }
    
    /* Mensajes de error/warning */
    .stAlert {
        border-radius: 8px;
        border: 1px solid #eef0f2;
    }
    
    /* Tablas en proyecciones */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
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
    
    # Mostrar login elegante
    st.markdown("""
    <div style="text-align: center; padding: 20px 0 5px 0;">
        <h1 style="color: #1a2634; font-size: 40px; font-weight: 300; letter-spacing: -0.5px; margin: 0;">
            🏛️ <span style="font-weight: 600; color: #2c6e8f;">FIFI</span>
        </h1>
        <p style="color: #6b7a8a; font-size: 15px; font-weight: 400; margin: 4px 0 0 0;">
            Investment Dashboard
        </p>
        <div style="width: 40px; height: 2px; background: linear-gradient(90deg, #2c6e8f, #4a8db7); margin: 10px auto;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.form("login_form"):
                st.markdown("""
                <div style="background: #ffffff; padding: 28px 30px 32px 30px; border-radius: 12px; border: 1px solid #eef0f2; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                """, unsafe_allow_html=True)
                
                username = st.text_input("Usuario", placeholder="Ingresa tu usuario", label_visibility="collapsed")
                st.markdown("<br>", unsafe_allow_html=True)
                password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña", label_visibility="collapsed")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                submitted = st.form_submit_button("Acceder", use_container_width=True)
                
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
                            
                            if archivo_usuario.startswith(("http://", "https://")):
                                st.session_state["archivo_usuario"] = archivo_usuario
                            else:
                                st.session_state["archivo_usuario"] = os.path.join("data", archivo_usuario)
                            
                            st.rerun()
                        else:
                            st.error("❌ Credenciales incorrectas")
                    else:
                        st.warning("⚠️ Completa ambos campos")
    
    # Footer
    st.markdown("""
    <div style="position: fixed; bottom: 20px; width: 100%; text-align: center; color: #c0b8b0; font-size: 11px; letter-spacing: 0.5px;">
        FIFI Investments © 2026
    </div>
    """, unsafe_allow_html=True)
    
    return False

if not check_password_hybrid():
    st.stop()

# =============================================================================
# 🚀 CONFIGURACIÓN POST-LOGIN
# =============================================================================

# Barra lateral elegante
with st.sidebar:
    # Logo
    st.markdown("""
    <div class="sidebar-logo">
    """, unsafe_allow_html=True)
    
    try:
        logo_path = os.path.join("logo.jpg")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_b64 = base64.b64encode(f.read()).decode()
            st.markdown(f"""
                <img src='data:image/jpeg;base64,{logo_b64}' style='max-width:120px;'/>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="color: #c8d0d8; font-size: 28px; font-weight: 300;">🏛️</div>
            """, unsafe_allow_html=True)
    except:
        st.markdown("""
        <div style="color: #c8d0d8; font-size: 28px; font-weight: 300;">🏛️</div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="logo-text"><span>FIFI</span> Investments</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Información del usuario
    st.markdown(f"""
    <div style="text-align: center; padding: 12px 0 8px 0;">
        <div class="avatar">{st.session_state['username'][0].upper()}</div>
        <div style="color: #ffffff; font-size: 14px; font-weight: 400;">{st.session_state['username']}</div>
        <div style="margin-top: 3px;"><span class="badge">● Activo</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    # Navegación con botones elegantes
    st.markdown('<div class="nav-section-title">Navegación</div>', unsafe_allow_html=True)
    
    # Estado de la página actual
    if "pagina" not in st.session_state:
        st.session_state["pagina"] = "KPIs"
    
    # Botones de navegación
    if st.button("📊 KPIs", key="nav_kpis", use_container_width=True):
        st.session_state["pagina"] = "KPIs"
        st.rerun()
    
    if st.button("📈 Gráficos", key="nav_charts", use_container_width=True):
        st.session_state["pagina"] = "Gráficos"
        st.rerun()
    
    if st.button("🚀 Proyecciones", key="nav_projections", use_container_width=True):
        st.session_state["pagina"] = "Proyecciones"
        st.rerun()
    
    if st.button("⚖️ Comparaciones", key="nav_comparisons", use_container_width=True):
        st.session_state["pagina"] = "Comparaciones"
        st.rerun()
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    # Cerrar sesión
    st.markdown('<div class="logout-btn">', unsafe_allow_html=True)
    if st.button("🚪 Cerrar sesión", key="logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Info del archivo
    try:
        st.markdown('<div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.03);">', unsafe_allow_html=True)
        st.caption(f"📁 {os.path.basename(archivo_usuario)}")
        st.caption(f"📅 {len(df)} registros")
        st.markdown('</div>', unsafe_allow_html=True)
    except:
        pass

# =============================================================================
# 📁 CARGA DE DATOS
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
        
        required_columns = ["Fecha", "Capital Invertido", "Ganacias/Pérdidas Netas"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Columna requerida no encontrada: {col}")
        
        df = df.dropna(subset=["Fecha"])
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
        df["Mes"] = df["Fecha"].dt.to_period("M")
        
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

try:
    archivo_usuario = st.session_state.get("archivo_usuario", "")
    if not archivo_usuario:
        st.error("No se ha configurado archivo para este usuario")
        st.stop()
    
    df = load_user_data(archivo_usuario)
    
except Exception as e:
    st.error(f"❌ Error al cargar datos del usuario: {str(e)}")
    st.stop()

# =============================================================================
# 📌 SECCIÓN DE KPIs - VERSIÓN LEGIBLE
# =============================================================================

def styled_kpi_elegant(title, value, subtitle="", icon="", color="#1a2634", tooltip=""):
    """KPI con diseño elegante y legible"""
    
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">
            <span>
                <span class="kpi-icon">{icon}</span> {title}
            </span>
            <span class="help-icon" title="{tooltip}">ⓘ</span>
        </div>
        <div class="kpi-value" style="color: {color};">{value}</div>
        <div class="kpi-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def show_elegant_kpis():
    """Muestra los KPIs con diseño elegante y legible"""
    
    st.markdown(f"""
    <div class="premium-header">
        <h1>📊 <span>KPI</span> Dashboard</h1>
        <p>Indicadores clave de desempeño</p>
        <div class="sub-info">Actualizado al {datetime.now().strftime('%d/%m/%Y')}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Validación
    required_columns = ["Fecha", "Capital Invertido", "Ganacias/Pérdidas Netas"]
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        st.error(f"❌ Columnas faltantes: {', '.join(missing_cols)}")
        st.stop()
    
    try:
        # Preprocesamiento
        df_copy = df.copy()
        df_copy["Mes"] = df_copy["Fecha"].dt.to_period("M")
        
        if "Ganacias/Pérdidas Netas Acumuladas" not in df_copy.columns:
            df_copy["Ganacias/Pérdidas Netas Acumuladas"] = df_copy["Ganacias/Pérdidas Netas"].cumsum()
        
        df_copy["Acumulado"] = df_copy["Ganacias/Pérdidas Netas Acumuladas"].ffill()
        df_copy["MaxAcum"] = df_copy["Acumulado"].cummax()
        df_copy["Drawdown"] = df_copy["Acumulado"] - df_copy["MaxAcum"]
        
        # Datos básicos
        capital_actual = df_copy["Capital Invertido"].dropna().iloc[-1]
        
        # CAPITAL INICIAL - Primer valor de "Aumento Capital"
        if "Aumento Capital" in df_copy.columns:
            aumentos_validos = df_copy["Aumento Capital"].dropna()
            aumentos_validos = aumentos_validos[aumentos_validos > 0]
            if len(aumentos_validos) > 0:
                capital_inicial = aumentos_validos.iloc[0]
            else:
                capital_inicial = df_copy["Capital Invertido"].dropna().iloc[0]
        else:
            capital_inicial = df_copy["Capital Invertido"].dropna().iloc[0]
        
        # APORTES AL FONDO (NUEVO KPI)
        if "Aumento Capital" in df_copy.columns:
            total_aumentos = df_copy["Aumento Capital"].sum()
            aportes_fondo = total_aumentos - capital_inicial
        else:
            aportes_fondo = 0
        
        # Cálculos
        ganancia_neta_total = df_copy["Ganacias/Pérdidas Netas"].sum()
        total_retiros = df_copy["Retiro de Fondos"].sum() if "Retiro de Fondos" in df_copy.columns else 0
        
        if capital_actual > 0:
            roi = (ganancia_neta_total / capital_actual) * 100
        else:
            roi = 0
        
        if "Beneficio en %" in df_copy.columns:
            monthly_returns = df_copy.groupby("Mes")["Beneficio en %"].mean()
            avg_monthly_return = monthly_returns.mean() * 100
        else:
            avg_monthly_return = 0
        
        max_drawdown = df_copy["Drawdown"].min() if "Drawdown" in df_copy.columns else 0
        
        # Rating de Riesgo
        if max_drawdown != 0 and capital_actual > 0:
            risk_ratio = abs(max_drawdown / capital_actual)
            if risk_ratio < 0.05:
                rating = "⭐⭐⭐⭐⭐"
                risk_text = "Muy Conservador"
            elif risk_ratio < 0.10:
                rating = "⭐⭐⭐⭐"
                risk_text = "Conservador"
            elif risk_ratio < 0.20:
                rating = "⭐⭐⭐"
                risk_text = "Moderado"
            elif risk_ratio < 0.30:
                rating = "⭐⭐"
                risk_text = "Agresivo"
            else:
                rating = "⭐"
                risk_text = "Muy Agresivo"
        else:
            rating = "⭐⭐⭐⭐⭐"
            risk_text = "Muy Conservador"
        
        # Mejor y Peor Mes
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
        
        total_meses = len(df_copy["Mes"].unique())
        
        if total_meses > 0 and capital_inicial > 0 and capital_actual > 0:
            cagr = (((capital_actual / capital_inicial) ** (12 / total_meses)) - 1) * 100
        else:
            cagr = 0
        
        # ===== FILA 1: KPIs PRINCIPALES =====
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            styled_kpi_elegant(
                "Capital Actual",
                f"${capital_actual:,.0f}",
                f"▲ +{((capital_actual/capital_inicial - 1) * 100):.1f}%",
                "💰",
                "#1a2634",
                "Valor total del capital invertido al día de hoy."
            )
        
        with col2:
            styled_kpi_elegant(
                "Rentabilidad Total",
                f"{roi:.1f}%",
                f"CAGR {cagr:.1f}% anual",
                "📈",
                "#2c6e8f" if roi > 0 else "#c0392b",
                "Retorno sobre la inversión total (ROI)."
            )
        
        with col3:
            styled_kpi_elegant(
                "Drawdown Máximo",
                f"${abs(max_drawdown):,.0f}",
                f"{abs(max_drawdown/capital_actual * 100):.1f}% del capital",
                "📉",
                "#c0392b",
                "Peor pérdida acumulada desde un punto máximo."
            )
        
        with col4:
            styled_kpi_elegant(
                "Rating de Riesgo",
                rating,
                risk_text,
                "🛡️",
                "#2c6e8f",
                "Nivel de riesgo basado en el drawdown máximo."
            )
        
        st.markdown("---")
        
        # ===== FILA 2: KPIs SECUNDARIOS =====
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            styled_kpi_elegant(
                "Rentabilidad Mensual Prom",
                f"{avg_monthly_return:.2f}%",
                f"{total_meses} meses",
                "📊",
                "#4a8db7",
                "Promedio de los rendimientos mensuales."
            )
        
        with col6:
            styled_kpi_elegant(
                "Capital Inicial",
                f"${capital_inicial:,.0f}",
                f"{df_copy['Fecha'].min().strftime('%b %Y')}",
                "🏦",
                "#6b7a8a",
                "Primer aporte de capital registrado."
            )
        
        with col7:
            styled_kpi_elegant(
                "Aportes al Fondo",
                f"${aportes_fondo:,.0f}",
                "Nuevos aportes realizados",
                "💳",
                "#27ae60",
                "Suma de todos los aumentos de capital adicionales."
            )
        
        with col8:
            styled_kpi_elegant(
                "Retiros Totales",
                f"${total_retiros:,.0f}",
                f"{total_retiros/capital_actual * 100:.1f}% del capital",
                "💸",
                "#e67e22",
                "Total de dinero retirado del fondo."
            )
        
        st.markdown("---")
        
        # ===== FILA 3: KPIs ADICIONALES =====
        col9, col10, col11, col12 = st.columns(4)
        
        with col9:
            styled_kpi_elegant(
                "Mejor Mes",
                mejor_mes,
                f"▲ {mejor_mes_valor:.2f}%",
                "🏆",
                "#27ae60",
                "Mes con la mayor rentabilidad porcentual."
            )
        
        with col10:
            styled_kpi_elegant(
                "Peor Mes",
                peor_mes,
                f"▼ {peor_mes_valor:.2f}%",
                "⚠️",
                "#c0392b",
                "Mes con la peor rentabilidad porcentual."
            )
        
        with col11:
            if max_drawdown != 0 and capital_actual > 0 and avg_monthly_return > 0:
                sharpe_ratio = avg_monthly_return / abs(max_drawdown/capital_actual * 100)
                sharpe_display = f"{sharpe_ratio:.2f}"
            else:
                sharpe_display = "N/A"
            
            styled_kpi_elegant(
                "Ratio Sharpe",
                sharpe_display,
                "Rendimiento / Riesgo",
                "📐",
                "#6b7a8a",
                "Mide la rentabilidad por unidad de riesgo."
            )
        
        with col12:
            styled_kpi_elegant(
                "Días en el Mercado",
                f"{(df_copy['Fecha'].max() - df_copy['Fecha'].min()).days}",
                f"Desde {df_copy['Fecha'].min().strftime('%d/%m/%Y')}",
                "📅",
                "#4a8db7",
                "Días desde el inicio de la inversión."
            )
            
    except Exception as e:
        st.error(f"❌ Error al calcular KPIs: {str(e)}")
        st.stop()

# =============================================================================
# 📊 SECCIÓN DE GRÁFICOS - VERSIÓN LEGIBLE
# =============================================================================

def show_premium_charts():
    """Muestra gráficos con diseño elegante y legible"""
    
    st.markdown("""
    <div class="premium-header">
        <h1>📈 <span>Visualizaciones</span> Financieras</h1>
        <p>Análisis detallado de la evolución de la inversión</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        df_copy = df.copy()
        df_copy["Mes"] = df_copy["Fecha"].dt.to_period("M")
        
        if "Ganacias/Pérdidas Netas Acumuladas" not in df_copy.columns:
            df_copy["Ganacias/Pérdidas Netas Acumuladas"] = df_copy["Ganacias/Pérdidas Netas"].cumsum()
        
        df_copy["Acumulado"] = df_copy["Ganacias/Pérdidas Netas Acumuladas"].ffill()
        df_copy["MaxAcum"] = df_copy["Acumulado"].cummax()
        df_copy["Drawdown"] = df_copy["Acumulado"] - df_copy["MaxAcum"]
        
        # Gráfico 1: Evolución del Capital
        st.markdown("### 📊 Evolución del Capital")
        
        fig1 = go.Figure()
        
        fig1.add_trace(go.Scatter(
            x=df_copy["Fecha"],
            y=df_copy["Capital Invertido"],
            mode='lines+markers',
            name='Capital Invertido',
            line=dict(color='#2c6e8f', width=3),
            marker=dict(size=6, color='#2c6e8f'),
            hovertemplate='%{x}<br>Capital: $%{y:,.0f}<extra></extra>'
        ))
        
        fig1.update_layout(
            template='plotly_white',
            height=450,
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255,255,255,0.95)',
                bordercolor='#eef0f2',
                borderwidth=1
            ),
            paper_bgcolor='rgba(255,255,255,0)',
            plot_bgcolor='rgba(255,255,255,0)',
            xaxis_title='Fecha',
            yaxis_title='Valor ($)',
            yaxis=dict(tickformat='$,.0f', gridcolor='#f0f2f4'),
            xaxis=dict(gridcolor='#f0f2f4')
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
            line=dict(color='#27ae60', width=3),
            marker=dict(size=6, color='#27ae60'),
            fill='tozeroy',
            fillcolor='rgba(39, 174, 96, 0.08)',
            hovertemplate='%{x}<br>Ganancia: $%{y:,.0f}<extra></extra>'
        ))
        
        fig2.update_layout(
            template='plotly_white',
            height=400,
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255,255,255,0.95)',
                bordercolor='#eef0f2',
                borderwidth=1
            ),
            paper_bgcolor='rgba(255,255,255,0)',
            plot_bgcolor='rgba(255,255,255,0)',
            xaxis_title='Fecha',
            yaxis_title='Ganancia ($)',
            yaxis=dict(tickformat='$,.0f', gridcolor='#f0f2f4'),
            xaxis=dict(gridcolor='#f0f2f4')
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("---")
        
        # Gráfico 3: Rentabilidad Mensual - Heatmap
        st.markdown("### 🌡️ Rentabilidad Mensual")
        
        if "Beneficio en %" in df_copy.columns:
            df_copy["Año"] = df_copy["Fecha"].dt.year
            df_copy["MesNombre"] = df_copy["Fecha"].dt.strftime("%b")
            df_copy["MesNum"] = df_copy["Fecha"].dt.month
            
            pivot_rent = df_copy.pivot_table(
                values="Beneficio en %",
                index="Año",
                columns="MesNum",
                aggfunc="mean"
            ) * 100
            
            pivot_rent.columns = [calendar.month_abbr[i] for i in pivot_rent.columns]
            
            fig3 = go.Figure(data=go.Heatmap(
                z=pivot_rent.values,
                x=pivot_rent.columns,
                y=pivot_rent.index,
                colorscale='RdBu_r',
                zmid=0,
                text=pivot_rent.values.round(2),
                texttemplate='%{text}%',
                textfont={"size": 11, "color": "#1a2634"},
                hovertemplate='<b>%{y}</b><br>%{x}<br>Rentabilidad: %{z:.2f}%<extra></extra>'
            ))
            
            fig3.update_layout(
                template='plotly_white',
                height=350,
                paper_bgcolor='rgba(255,255,255,0)',
                plot_bgcolor='rgba(255,255,255,0)',
                xaxis_title='Mes',
                yaxis_title='Año',
                xaxis=dict(side='top')
            )
            
            st.plotly_chart(fig3, use_container_width=True)
            
    except Exception as e:
        st.error(f"❌ Error al generar gráficos: {str(e)}")
        st.stop()

# =============================================================================
# 📈 SECCIÓN DE PROYECCIONES
# =============================================================================

def show_premium_projections():
    """Muestra proyecciones con diseño elegante"""
    
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
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #eef0f2;">
            """, unsafe_allow_html=True)
            
            aumento_opcion = st.selectbox(
                "Aumento de capital",
                [0, 5, 10, 15, 20, 30, 50],
                format_func=lambda x: f"{x}%"
            )
            
            beneficio_mensual = st.slider(
                "Beneficio mensual estimado",
                min_value=0.0,
                max_value=15.0,
                value=5.0,
                step=0.5,
                format="%.1f%%"
            )
            
            meses_proyeccion = st.slider(
                "Duración de la inversión",
                min_value=1,
                max_value=60,
                value=12,
                format="%d meses"
            )
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            capital_proyectado = capital_actual * (1 + aumento_opcion / 100)
            proyeccion = [capital_proyectado * ((1 + beneficio_mensual / 100) ** i) for i in range(meses_proyeccion + 1)]
            
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #eef0f2; height: 100%;">
                <div style="margin-bottom: 10px;">
                    <div style="color: #6b7a8a; font-size: 12px;">Capital Actual</div>
                    <div style="color: #1a2634; font-size: 22px; font-weight: 600;">${capital_actual:,.0f}</div>
                </div>
                <div style="margin-bottom: 10px;">
                    <div style="color: #6b7a8a; font-size: 12px;">Capital Proyectado</div>
                    <div style="color: #2c6e8f; font-size: 22px; font-weight: 600;">${capital_proyectado:,.0f}</div>
                </div>
                <div>
                    <div style="color: #6b7a8a; font-size: 12px;">Valor Estimado Final</div>
                    <div style="color: #27ae60; font-size: 26px; font-weight: 600;">${proyeccion[-1]:,.0f}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        df_proy = pd.DataFrame({
            "Mes": list(range(meses_proyeccion + 1)),
            "Proyección": proyeccion
        })
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_proy["Mes"],
            y=df_proy["Proyección"],
            mode='lines+markers',
            name='Proyección',
            line=dict(color='#2c6e8f', width=3),
            marker=dict(size=8, color='#2c6e8f'),
            fill='tozeroy',
            fillcolor='rgba(44, 110, 143, 0.06)',
            hovertemplate='Mes %{x}<br>Capital: $%{y:,.0f}<extra></extra>'
        ))
        
        z = np.polyfit(df_proy["Mes"], df_proy["Proyección"], 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(
            x=df_proy["Mes"],
            y=p(df_proy["Mes"]),
            mode='lines',
            name='Tendencia',
            line=dict(color='rgba(44, 110, 143, 0.25)', width=2, dash='dash')
        ))
        
        fig.update_layout(
            template='plotly_white',
            height=400,
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(255,255,255,0.95)',
                bordercolor='#eef0f2',
                borderwidth=1
            ),
            paper_bgcolor='rgba(255,255,255,0)',
            plot_bgcolor='rgba(255,255,255,0)',
            xaxis_title='Meses',
            yaxis_title='Capital Proyectado ($)',
            yaxis=dict(tickformat='$,.0f', gridcolor='#f0f2f4'),
            xaxis=dict(gridcolor='#f0f2f4')
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
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
            "📥 Descargar Proyección",
            data=excel_data,
            file_name=f"proyeccion_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"❌ Error al generar proyecciones: {str(e)}")
        st.stop()

# =============================================================================
# ⚖️ SECCIÓN DE COMPARACIONES
# =============================================================================

def show_premium_comparisons():
    """Muestra comparaciones con diseño elegante"""
    
    st.markdown("""
    <div class="premium-header">
        <h1>⚖️ <span>Comparaciones</span> Anuales</h1>
        <p>Análisis comparativo de rendimiento por año</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        df_copy = df.copy()
        df_copy["Año"] = df_copy["Fecha"].dt.year
        df_copy["MesNombre"] = df_copy["Fecha"].dt.strftime("%b")
        df_copy["MesNum"] = df_copy["Fecha"].dt.month
        
        if "Ganacias/Pérdidas Netas Acumuladas" not in df_copy.columns:
            df_copy["Ganacias/Pérdidas Netas Acumuladas"] = df_copy["Ganacias/Pérdidas Netas"].cumsum()
        
        df_copy["Acumulado"] = df_copy["Ganacias/Pérdidas Netas Acumuladas"].ffill()
        df_copy["MaxAcum"] = df_copy["Acumulado"].cummax()
        df_copy["Drawdown"] = df_copy["Acumulado"] - df_copy["MaxAcum"]
        
        años_disponibles = sorted(df_copy["Año"].unique().tolist())
        años_seleccionados = st.multiselect(
            "Selecciona los años a comparar",
            años_disponibles,
            default=años_disponibles[-2:] if len(años_disponibles) > 1 else años_disponibles
        )
        
        if not años_seleccionados:
            st.warning("Selecciona al menos un año para comparar")
            st.stop()
        
        df_filtrado = df_copy[df_copy["Año"].isin(años_seleccionados)]
        
        st.markdown("### 📈 Comparación de Rentabilidad Mensual")
        
        if "Beneficio en %" in df_filtrado.columns:
            comparacion = df_filtrado.groupby(["Año", "MesNum", "MesNombre"]).agg({
                "Beneficio en %": "mean"
            }).reset_index().sort_values(["Año", "MesNum"])
            
            comparacion["Beneficio en %"] *= 100
            
            fig1 = go.Figure()
            
            colores = ['#2c6e8f', '#4a8db7', '#6ba3c9', '#8ab8d9', '#aacce6']
            
            for i, año in enumerate(años_seleccionados):
                data_año = comparacion[comparacion["Año"] == año]
                fig1.add_trace(go.Scatter(
                    x=data_año["MesNombre"],
                    y=data_año["Beneficio en %"],
                    mode='lines+markers',
                    name=f"{año}",
                    line=dict(width=2.5, color=colores[i % len(colores)]),
                    marker=dict(size=7, color=colores[i % len(colores)]),
                    hovertemplate='%{x}<br>Rentabilidad: %{y:.2f}%<extra></extra>'
                ))
            
            fig1.update_layout(
                template='plotly_white',
                height=400,
                hovermode='x unified',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    bgcolor='rgba(255,255,255,0.95)',
                    bordercolor='#eef0f2',
                    borderwidth=1
                ),
                paper_bgcolor='rgba(255,255,255,0)',
                plot_bgcolor='rgba(255,255,255,0)',
                xaxis_title='Mes',
                yaxis_title='Rentabilidad (%)',
                xaxis=dict(categoryorder='array', categoryarray=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
            )
            
            st.plotly_chart(fig1, use_container_width=True)
            
    except Exception as e:
        st.error(f"❌ Error al generar comparaciones: {str(e)}")
        st.stop()

# =============================================================================
# 🏁 MENÚ PRINCIPAL
# =============================================================================

# Mostrar sección seleccionada
if st.session_state["pagina"] == "KPIs":
    show_elegant_kpis()
elif st.session_state["pagina"] == "Gráficos":
    show_premium_charts()
elif st.session_state["pagina"] == "Proyecciones":
    show_premium_projections()
elif st.session_state["pagina"] == "Comparaciones":
    show_premium_comparisons()
