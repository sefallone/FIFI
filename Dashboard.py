import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime
import base64
from io import BytesIO

# =============================================
# CONFIGURACIÓN INICIAL
# =============================================

st.set_page_config(
    page_title="Dashboard Fallone Investments",
    layout="wide",
    initial_sidebar_state="expanded"
)

try:
    from streamlit_extras.metric_cards import metric_card
    METRIC_CARDS_ENABLED = True
except ImportError:
    METRIC_CARDS_ENABLED = False

# =============================================
# FUNCIONES AUXILIARES (ADAPTADAS A TUS COLUMNAS)
# =============================================

def safe_divide(numerator, denominator):
    """Evita divisiones por cero"""
    try:
        return numerator / denominator if denominator != 0 else 0
    except:
        return 0

def normalize_column_names(df):
    """
    Normalización específica para tu estructura de columnas
    """
    # Mapeo exacto de tus nombres de columnas
    column_mapping = {
        'Fecha': 'fecha',
        'ID Inv': 'id_inversionista',
        'Nombre Inversionista': 'nombre_inversionista',
        'Capital Invertido': 'capital_invertido',
        'Aumento Capital': 'aumento_capital',
        'Retiro de Fondos': 'retiro_fondos',
        'Ganacias/Pérdidas Brutas': 'ganancias_perdidas_brutas',
        'Ganacias/Pérdidas Brutas Acumuladas': 'ganancias_perdidas_brutas_acum',
        'Comisiones 10 %': 'comisiones_10p',
        'Comisiones Pagadas': 'comisiones_pagadas',
        'Ganacias/Pérdidas Netas': 'ganancias_perdidas_netas',
        'Ganacias/Pérdidas Netas Acumuladas': 'ganancias_perdidas_netas_acum',
        'Ganacias/Pérdidas Promedio Diario': 'ganancias_perdidas_promedio_diario',
        'Beneficio en %': 'beneficio_porcentaje'
    }
    
    # Renombrar columnas
    df = df.rename(columns=column_mapping)
    return df

def validate_dataframe(df):
    """Validación adaptada a tus columnas requeridas"""
    required_columns = ['fecha', 'capital_invertido', 'ganancias_perdidas_brutas']
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        return False, f"Faltan columnas requeridas: {', '.join(missing_cols)}"
    
    try:
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['capital_invertido'] = pd.to_numeric(df['capital_invertido'])
        df['ganancias_perdidas_brutas'] = pd.to_numeric(df['ganancias_perdidas_brutas'])
        return True, "Datos válidos"
    except Exception as e:
        return False, f"Error en tipos de datos: {str(e)}"

def load_custom_style():
    """Estilo personalizado"""
    st.markdown("""
    <style>
        .stApp { background-color: #121212; color: #ffffff; }
        .stSidebar { background-color: #1e1e1e !important; }
        .stTextInput input, .stSelectbox select, .stSlider div[role='slider'], 
        .stDateInput input { background-color: #2d2d2d !important; color: white !important; }
        .stButton>button { background-color: #3f33ff; color: white; }
        h1, h2, h3, h4, h5, h6 { color: #3f33ff !important; }
    </style>
    """, unsafe_allow_html=True)

# =============================================
# FUNCIONES DE ANÁLISIS (ACTUALIZADAS)
# =============================================

def calculate_metrics(df):
    """Cálculo de métricas adaptadas a tus columnas"""
    metrics = {}
    
    # Métricas básicas
    metrics['capital_inicial'] = df['capital_invertido'].iloc[0] if len(df) > 0 else 0
    metrics['capital_actual'] = df['capital_invertido'].iloc[-1] if len(df) > 0 else 0
    metrics['ganancias_brutas'] = df['ganancias_perdidas_brutas'].sum()
    metrics['ganancias_netas'] = df.get('ganancias_perdidas_netas', pd.Series([0])).sum()
    metrics['comisiones'] = df.get('comisiones_pagadas', pd.Series([0])).sum()
    metrics['retiros'] = df.get('retiro_fondos', pd.Series([0])).sum()
    
    # Métricas calculadas
    metrics['roi'] = safe_divide(metrics['ganancias_netas'], metrics['capital_inicial']) * 100
    metrics['cagr'] = calculate_cagr(df, metrics['capital_inicial'], metrics['capital_actual'])
    metrics['sharpe_ratio'] = calculate_sharpe_ratio(df)
    metrics['max_drawdown'] = calculate_max_drawdown(df)
    
    return metrics

def calculate_cagr(df, capital_inicial, current_capital):
    """Cálculo de CAGR adaptado"""
    if len(df) < 2 or capital_inicial == 0:
        return 0
    
    try:
        start_date = df['fecha'].iloc[0]
        end_date = df['fecha'].iloc[-1]
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if months <= 0: months = 1
        return ((float(current_capital) / float(capital_inicial)) ** (12/months) - 1) * 100
    except:
        return 0

def calculate_sharpe_ratio(df):
    """Cálculo de Sharpe ratio adaptado"""
    if 'ganancias_perdidas_netas' not in df.columns or len(df) < 2:
        return 0
    
    try:
        returns = df['ganancias_perdidas_netas'].pct_change().dropna()
        if len(returns) < 1 or returns.std() == 0:
            return 0
        return (returns.mean() / returns.std()) * (np.sqrt(12))
    except:
        return 0

def calculate_max_drawdown(df):
    """Cálculo de drawdown adaptado"""
    if 'capital_invertido' not in df.columns or len(df) < 1:
        return 0
    
    try:
        df['capital_acumulado'] = df['capital_invertido'].cummax()
        df['drawdown'] = safe_divide(
            (df['capital_invertido'] - df['capital_acumulado']),
            df['capital_acumulado']
        )
        return df['drawdown'].min() * 100
    except:
        return 0

# =============================================
# VISUALIZACIONES (ACTUALIZADAS)
# =============================================

def plot_combined_capital_withdrawals(df, capital_inicial):
    """Gráfico adaptado a tus columnas"""
    if not all(col in df.columns for col in ['fecha', 'capital_invertido']):
        st.warning("No se pueden generar el gráfico. Faltan columnas requeridas.")
        return
    
    try:
        fig = px.line(
            df, x='fecha', y='capital_invertido',
            title='<b>Evolución del Capital</b>',
            labels={'capital_invertido': 'Monto ($)', 'fecha': 'Fecha'},
            template="plotly_dark"
        )
        
        if 'retiro_fondos' in df.columns:
            fig.add_bar(
                x=df['fecha'], y=df['retiro_fondos'],
                name='Retiros', marker_color='#FF6B6B', opacity=0.7
            )
            fig.update_layout(title='<b>Evolución del Capital vs Retiros</b>')
        
        fig.add_hline(
            y=capital_inicial, line_dash="dash", line_color="green",
            annotation_text=f"Capital Inicial: ${capital_inicial:,.2f}",
            annotation_position="bottom right"
        )
        
        fig.update_layout(height=450, hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error al generar gráfico: {str(e)}")

def plot_profit_analysis(df):
    """Análisis de ganancias adaptado"""
    if not all(col in df.columns for col in ['fecha', 'ganancias_perdidas_brutas']):
        return
    
    try:
        # Gráfico de ganancias/pérdidas brutas
        fig = px.bar(
            df, x='fecha', y='ganancias_perdidas_brutas',
            title='Ganancias/Pérdidas Brutas por Periodo',
            color='ganancias_perdidas_brutas',
            color_continuous_scale=px.colors.diverging.RdYlGn,
            template="plotly_dark"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Gráfico acumulado si existe
        if 'ganancias_perdidas_brutas_acum' in df.columns:
            fig_acum = px.area(
                df, x='fecha', y='ganancias_perdidas_brutas_acum',
                title='Ganancias/Pérdidas Brutas Acumuladas',
                template="plotly_dark"
            )
            fig_acum.update_layout(height=400)
            st.plotly_chart(fig_acum, use_container_width=True)
    except Exception as e:
        st.error(f"Error al generar gráficos de ganancias: {str(e)}")

# =============================================
# INTERFAZ PRINCIPAL (ACTUALIZADA)
# =============================================

def main():
    load_custom_style()
    st.title("📊 Dashboard Fallone Investments")
    
    uploaded_file = st.file_uploader("📤 Subir archivo Excel", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            selected_sheet = st.selectbox("📋 Seleccionar hoja", sheet_names)
            
            @st.cache_data
            def load_data(file, sheet):
                df = pd.read_excel(file, sheet_name=sheet)
                df = normalize_column_names(df)
                return df.loc[:, ~df.columns.duplicated()]
            
            df = load_data(uploaded_file, selected_sheet)
            
            # Validación
            is_valid, validation_msg = validate_dataframe(df)
            if not is_valid:
                st.error(validation_msg)
                st.stop()
            
            # Filtros
            filtered_df = advanced_filters(df)
            
            if len(filtered_df) == 0:
                st.warning("No hay datos que coincidan con los filtros")
                st.stop()
            
            st.success(f"✅ Datos cargados correctamente ({len(filtered_df)} registros)")
            
            # Cálculo de métricas
            metrics = calculate_metrics(filtered_df)
            id_inversionista = filtered_df['id_inversionista'].iloc[0] if 'id_inversionista' in filtered_df.columns else "N/D"
            fecha_entrada = filtered_df['fecha'].iloc[0].strftime('%d/%m/%Y') if len(filtered_df) > 0 else "N/D"
            
            # Mostrar KPIs
            st.markdown("---")
            st.markdown('<h2 style="color: #3f33ff;">📊 KPIs Principales</h2>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                display_kpi("ID Inversionista", id_inversionista, "🆔", False)
                display_kpi("Capital Inicial", metrics['capital_inicial'], "🏁")
            with col2:
                display_kpi("Fecha Entrada", fecha_entrada, "📅", False)
                display_kpi("Capital Actual", metrics['capital_actual'], "🏦", 
                          delta=f"{metrics['capital_actual'] - metrics['capital_inicial']:+,.2f}")
            with col3:
                display_kpi("Ganancias Brutas", metrics['ganancias_brutas'], "💵")
                display_kpi("Ganancias Netas", metrics['ganancias_netas'], "💰")
            with col4:
                display_kpi("ROI", metrics['roi'], "📊", False, True)
                display_kpi("CAGR Mensual", metrics['cagr'], "🚀", False, True)
            
            # Gráficos principales
            st.markdown("---")
            tab1, tab2 = st.tabs(["📈 Visualizaciones", "🔍 Datos"])
            
            with tab1:
                plot_combined_capital_withdrawals(filtered_df, metrics['capital_inicial'])
                plot_profit_analysis(filtered_df)
                
                if 'comisiones_pagadas' in filtered_df.columns:
                    filtered_df['comisiones_acum'] = filtered_df['comisiones_pagadas'].cumsum()
                    fig_com = px.area(
                        filtered_df, x='fecha', y='comisiones_acum',
                        title='Comisiones Pagadas Acumuladas',
                        template="plotly_dark"
                    )
                    fig_com.update_layout(height=400)
                    st.plotly_chart(fig_com, use_container_width=True)
            
            with tab2:
                st.dataframe(
                    filtered_df.style.format({
                        'capital_invertido': '${:,.2f}',
                        'ganancias_perdidas_brutas': '${:,.2f}',
                        'ganancias_perdidas_netas': '${:,.2f}',
                        'comisiones_pagadas': '${:,.2f}',
                        'retiro_fondos': '${:,.2f}'
                    }), 
                    use_container_width=True,
                    height=500
                )
                
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Exportar datos filtrados",
                    data=csv,
                    file_name="datos_fallone.csv",
                    mime="text/csv"
                )
        
        except Exception as e:
            st.error(f"Error al procesar el archivo: {str(e)}")
    else:
        st.info("👋 Por favor, sube un archivo Excel para comenzar")

if __name__ == "__main__":
    main()
