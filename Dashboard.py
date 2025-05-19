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

# Configuración de página
st.set_page_config(
    page_title="Dashboard Fallone Investments",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración para metric cards
try:
    from streamlit_extras.metric_cards import metric_card
    METRIC_CARDS_ENABLED = True
except ImportError:
    METRIC_CARDS_ENABLED = False

# =============================================
# FUNCIONES AUXILIARES MEJORADAS
# =============================================

def safe_divide(numerator, denominator):
    """Evita divisiones por cero"""
    try:
        return numerator / denominator if denominator != 0 else 0
    except:
        return 0

def normalize_column_names(df):
    """
    Normaliza los nombres de columnas con manejo de variantes comunes.
    Versión mejorada para manejar múltiples formatos de nombres.
    """
    # Primero hacer replacements específicos para casos conocidos
    df.columns = df.columns.str.strip()
    
    common_replacements = {
        'ganancias/perdidas brutas': 'ganancias_perdidas_brutas',
        'ganancias pérdidas brutas': 'ganancias_perdidas_brutas',
        'ganacias/perdidas brutas': 'ganancias_perdidas_brutas',
        'ganancias_perdidas brutas': 'ganancias_perdidas_brutas',
        'ganancias perdidas brutas': 'ganancias_perdidas_brutas',
        'capital invertido': 'capital_invertido',
        'comisiones 10 %': 'comisiones_pagadas',
        'comisiones pagadas': 'comisiones_pagadas',
        'retiro de fondos': 'retiro_fondos',
        'retiro fondos': 'retiro_fondos',
        'id inv': 'id_inversionista',
        'id inversionista': 'id_inversionista',
        'aumento capital': 'aumento_capital',
        'ganancias/perdidas netas': 'ganancias_perdidas_netas',
        'ganancias pérdidas netas': 'ganancias_perdidas_netas',
        'beneficio %': 'porcentaje_beneficio'
    }
    
    # Aplicar replacements específicos
    for old, new in common_replacements.items():
        if old in df.columns:
            df = df.rename(columns={old: new})
    
    # Normalización general
    df.columns = (
        df.columns.str.lower()
        .str.replace(' ', '_')
        .str.replace('ó', 'o')
        .str.replace('é', 'e')
        .str.replace('í', 'i')
        .str.replace('á', 'a')
        .str.replace('ú', 'u')
        .str.replace('ñ', 'n')
        .str.replace('/', '_')
        .str.replace('%', 'porcentaje')
        .str.replace('-', '_')
    )
    
    return df

def validate_dataframe(df):
    """
    Valida que el DataFrame tenga las columnas necesarias con mensajes descriptivos.
    Versión mejorada con sugerencias para nombres de columnas.
    """
    required_columns = {
        'fecha': {
            'description': 'Fecha de las operaciones',
            'alternatives': ['fecha_operacion', 'date', 'fecha_transaccion']
        },
        'capital_invertido': {
            'description': 'Monto de capital invertido',
            'alternatives': ['capital', 'monto_invertido', 'inversion']
        },
        'ganancias_perdidas_brutas': {
            'description': 'Ganancias o pérdidas brutas',
            'alternatives': ['ganancias_brutas', 'resultado_bruto', 'beneficio_bruto']
        }
    }
    
    missing_cols = []
    suggestions = {}
    
    for col, info in required_columns.items():
        if col not in df.columns:
            missing_cols.append(col)
            # Buscar alternativas
            for alt in info['alternatives']:
                if alt in df.columns:
                    df = df.rename(columns={alt: col})
                    if col not in missing_cols:  # Si ya se encontró y renombró
                        missing_cols.remove(col)
                    break
    
    if missing_cols:
        error_msg = "Faltan columnas requeridas:\n"
        for col in missing_cols:
            info = required_columns[col]
            error_msg += f"\n- {col} ({info['description']})"
            if info['alternatives']:
                error_msg += f"\n  Nombres alternativos aceptados: {', '.join(info['alternatives'])}"
        
        # Mostrar las columnas disponibles para ayudar en debugging
        error_msg += f"\n\nColumnas disponibles en el archivo: {', '.join(df.columns.tolist())}"
        return False, error_msg
    
    # Validar tipos de datos
    try:
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['capital_invertido'] = pd.to_numeric(df['capital_invertido'])
        df['ganancias_perdidas_brutas'] = pd.to_numeric(df['ganancias_perdidas_brutas'])
        return True, "Datos válidos"
    except Exception as e:
        return False, f"Error al convertir datos: {str(e)}\nTipos actuales:\n{df.dtypes}"

def load_custom_style():
    """Carga el estilo CSS personalizado mejorado"""
    st.markdown("""
    <style>
        /* Estilos base */
        .stApp {
            background-color: #121212;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        /* Sidebar */
        .stSidebar {
            background-color: #1e1e1e !important;
            border-right: 1px solid #333;
        }
        
        /* Inputs */
        .stTextInput input, 
        .stSelectbox select, 
        .stSlider div[role='slider'],
        .stDateInput input,
        .stNumberInput input {
            background-color: #2d2d2d !important;
            color: white !important;
            border: 1px solid #444 !important;
            border-radius: 4px !important;
        }
        
        /* Botones */
        .stButton>button {
            background-color: #3f33ff;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            transition: all 0.3s;
            font-weight: 500;
        }
        .stButton>button:hover {
            background-color: #2a22cc;
            transform: translateY(-2px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            padding: 0 1rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 1rem;
            border-radius: 4px 4px 0 0;
            background-color: #2d2d2d;
            transition: all 0.3s;
            font-weight: 500;
            margin: 0;
        }
        .stTabs [aria-selected="true"] {
            background-color: #3f33ff !important;
            color: white !important;
        }
        
        /* DataFrames */
        .stDataFrame {
            background-color: #1e1e1e !important;
            border: 1px solid #333 !important;
            border-radius: 4px;
        }
        
        /* Alertas */
        .stAlert {
            border-left: 4px solid #3f33ff !important;
            background-color: #1e1e1e !important;
        }
        
        /* Títulos */
        h1, h2, h3, h4, h5, h6 {
            color: #3f33ff !important;
        }
        
        /* Tooltips */
        .stTooltip {
            background-color: #2d2d2d !important;
            border: 1px solid #3f33ff !important;
        }
    </style>
    """, unsafe_allow_html=True)

# =============================================
# FUNCIÓN DE FILTROS AVANZADOS (MEJORADA)
# =============================================

def advanced_filters(df):
    """Función con selector de fechas por mes y año con validación mejorada"""
    with st.sidebar.expander("🔍 Filtros Avanzados", expanded=True):
        filtered_df = df.copy()
        
        # Filtro por fechas
        if 'fecha' in filtered_df.columns:
            try:
                min_date = filtered_df['fecha'].min().to_pydatetime()
                max_date = filtered_df['fecha'].max().to_pydatetime()
                
                st.write("**Seleccione el rango de fechas:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    start_date = st.date_input(
                        "Fecha inicial",
                        value=min_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="start_date"
                    )
                
                with col2:
                    end_date = st.date_input(
                        "Fecha final",
                        value=max_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="end_date"
                    )
                
                # Validar que la fecha inicial no sea mayor que la final
                if start_date > end_date:
                    st.error("⚠️ La fecha inicial no puede ser mayor que la final")
                    return df  # Retornar los datos sin filtrar
                
                # Convertir a datetime y filtrar
                start_date = pd.to_datetime(start_date)
                end_date = pd.to_datetime(end_date)
                
                filtered_df = filtered_df[
                    (filtered_df['fecha'] >= start_date) & 
                    (filtered_df['fecha'] <= end_date)
                ]
                
            except Exception as e:
                st.warning(f"⚠️ No se pudo aplicar el filtro de fechas: {str(e)}")
                return df  # Retornar los datos sin filtrar
        
        # Filtro por capital invertido
        if 'capital_invertido' in filtered_df.columns:
            try:
                capital_series = pd.to_numeric(
                    filtered_df['capital_invertido'], 
                    errors='coerce'
                ).dropna()
                
                if not capital_series.empty:
                    min_cap = float(capital_series.min())
                    max_cap = float(capital_series.max())
                    
                    # Si todos los valores son iguales, ajustar el rango
                    if min_cap == max_cap:
                        min_cap = max(0, min_cap - 1)
                        max_cap += 1
                    
                    cap_range = st.slider(
                        "Seleccione rango de capital",
                        min_value=min_cap,
                        max_value=max_cap,
                        value=(min_cap, max_cap),
                        help="Filtre por rango de capital invertido",
                        key="capital_range_filter"
                    )
                    
                    filtered_df = filtered_df[
                        (pd.to_numeric(filtered_df['capital_invertido'], errors='coerce') >= cap_range[0]) & 
                        (pd.to_numeric(filtered_df['capital_invertido'], errors='coerce') <= cap_range[1])
                    ]
                else:
                    st.warning("⚠️ No hay valores numéricos válidos en 'Capital Invertido'")
            except Exception as e:
                st.warning(f"⚠️ No se pudo aplicar el filtro de capital: {str(e)}")
        
        # Filtro por resultados (ganancias/pérdidas)
        if 'ganancias_perdidas_brutas' in filtered_df.columns:
            try:
                profit_filter = st.selectbox(
                    "Filtrar por resultados",
                    options=["Todos", "Solo ganancias", "Solo pérdidas"],
                    index=0,
                    help="Filtre por tipo de resultados financieros",
                    key="profit_filter"
                )
                
                if profit_filter == "Solo ganancias":
                    filtered_df = filtered_df[filtered_df['ganancias_perdidas_brutas'] >= 0]
                elif profit_filter == "Solo pérdidas":
                    filtered_df = filtered_df[filtered_df['ganancias_perdidas_brutas'] < 0]
            except Exception as e:
                st.warning(f"⚠️ No se pudo aplicar el filtro de ganancias: {str(e)}")
    
    return filtered_df

# =============================================
# VISUALIZACIÓN DE KPIs (MEJORADA)
# =============================================

def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False, delta=None):
    """
    Muestra un KPI con tooltip explicativo mejorado.
    
    Parámetros:
        title (str): Nombre del KPI
        value: Valor a mostrar
        icon (str): Emoji para el KPI
        is_currency (bool): Si es valor monetario
        is_percentage (bool): Si es porcentaje
        delta: Variación del valor
    """
    # Diccionario de explicaciones para cada KPI
    kpi_explanations = {
        "id_inversionista": "Identificador único del inversionista en el sistema.",
        "fecha_entrada": "Fecha inicial de participación en el fondo de inversión.",
        "capital_inicial": "Monto inicial invertido por el usuario.",
        "capital_actual": "Valor actual de la inversión (incluyendo ganancias/pérdidas).",
        "total_inyeccion": "Suma total de capital adicional aportado.",
        "ganancias_brutas": "Beneficios antes de deducir comisiones e impuestos.",
        "ganancias_netas": "Beneficios después de comisiones e impuestos.",
        "comisiones_pagadas": "Total acumulado en comisiones de gestión.",
        "retiro_dinero": "Capital retirado por el inversionista.",
        "roi": "Retorno sobre la inversión (Ganancias Netas / Capital Inicial).",
        "cagr_mensual": "Tasa de crecimiento anual compuesto mensualizada.",
        "drawdown_max": "Peor pérdida porcentual respecto al máximo histórico.",
        "ratio_sharpe": "Medida de rendimiento ajustado al riesgo (mayor = mejor)."
    }

    # Formatear el valor
    if pd.isna(value) or value is None:
        value_display = "N/D"
        delta_display = None
    else:
        if is_currency:
            value_display = f"${float(value):,.2f}"
        elif is_percentage:
            value_display = f"{float(value):.2f}%"
        else:
            value_display = f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
        
        delta_display = delta

    # Tooltip con explicación
    explanation = kpi_explanations.get(title.lower().replace(' ', '_'), "Métrica financiera clave.")
    
    if METRIC_CARDS_ENABLED:
        metric_card(
            title=f"{icon} {title}",
            value=value_display,
            delta=delta_display,
            key=f"card_{title.replace(' ', '_')}",
            background="#1e1e1e",
            border_color="#3f33ff",
            border_size_px=2,
            help=explanation
        )
    else:
        delta_color = "#4CAF50" if delta_display and str(delta_display).startswith('+') else "#F44336"
        delta_html = f"""
        <div style='color: {delta_color}; font-size: 14px; margin-top: 5px;'>
            {delta_display if delta_display else ''}
        </div>
        """ if delta_display else ""
        
        st.markdown(f"""
        <div style="
            background: #1e1e1e;
            color: #ffffff;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            margin-bottom: 20px;
            border-left: 4px solid #3f33ff;
            position: relative;
        ">
            <div style="font-weight: 600; font-size: 14px; color: #ffffff;">
                {icon} {title}
                <span style="font-size: 12px; color: #aaa; margin-left: 5px; cursor: pointer;" title="{explanation}">ℹ️</span>
            </div>
            <div style="font-weight: 700; font-size: 24px; margin: 10px 0;">{value_display}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

# =============================================
# FUNCIONES DE ANÁLISIS (MEJORADAS)
# =============================================

def calculate_roi(ganancias_netas, capital_inicial):
    """Calcula el ROI basado en ganancias netas con validación"""
    return safe_divide(ganancias_netas, capital_inicial) * 100

def calculate_cagr(df, capital_inicial, current_capital):
    """Calcula la tasa de crecimiento anual compuesta con validación"""
    if len(df) < 2 or capital_inicial == 0:
        return 0
    
    try:
        start_date = df['fecha'].iloc[0]
        end_date = df['fecha'].iloc[-1]
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if months <= 0:
            months = 1
        return ((float(current_capital) / float(capital_inicial)) ** (12/months) - 1) * 100
    except:
        return 0

def calculate_sharpe_ratio(df):
    """Calcula el ratio Sharpe simplificado con validación"""
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
    """Calcula el drawdown máximo con validación"""
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
# VISUALIZACIONES (MEJORADAS)
# =============================================

def plot_combined_capital_withdrawals(df, capital_inicial):
    """Muestra la evolución del capital invertido junto con retiros de dinero"""
    if not all(col in df.columns for col in ['fecha', 'capital_invertido', 'retiro_fondos']):
        st.warning("⚠️ No se pueden generar el gráfico combinado. Faltan columnas necesarias.")
        return
    
    try:
        fig = px.line(
            df,
            x='fecha',
            y='capital_invertido',
            title='<b>Evolución del Capital vs Retiros</b>',
            labels={'capital_invertido': 'Monto ($)', 'fecha': 'Fecha'},
            template="plotly_dark",
            line_shape='linear'
        )
        
        # Añadir retiros como barras
        fig.add_bar(
            x=df['fecha'],
            y=df['retiro_fondos'],
            name='Retiros',
            marker_color='#FF6B6B',
            opacity=0.7
        )
        
        # Línea de capital inicial
        fig.add_hline(
            y=capital_inicial,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Capital Inicial: ${capital_inicial:,.2f}",
            annotation_position="bottom right",
            annotation_font_color="#fff"
        )
        
        fig.update_layout(
            height=450,
            barmode='overlay',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error al generar gráfico combinado: {str(e)}")

def plot_capital_profit_relation(df):
    """Muestra la relación porcentual entre capital invertido y ganancias brutas"""
    if not all(col in df.columns for col in ['fecha', 'capital_invertido', 'ganancias_perdidas_brutas']):
        st.warning("⚠️ No se pueden calcular las métricas de relación. Faltan columnas necesarias.")
        return
    
    try:
        df['porcentaje_ganancias'] = safe_divide(
            df['ganancias_perdidas_brutas'], 
            df['capital_invertido']
        ) * 100
        
        fig = px.bar(
            df,
            x='fecha',
            y='porcentaje_ganancias',
            title='Relación Porcentual: Ganancias Brutas / Capital Invertido',
            labels={'porcentaje_ganancias': 'Porcentaje de Ganancias (%)', 'fecha': 'Fecha'},
            color='porcentaje_ganancias',
            color_continuous_scale=px.colors.diverging.RdYlGn,
            template="plotly_dark"
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="white")
        fig.update_layout(
            height=400, 
            yaxis_title="Porcentaje de Ganancias (%)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error al generar gráfico de relación: {str(e)}")

def plot_projection(df):
    """Gráficos de proyección a 3 años con validación mejorada"""
    if len(df) < 2 or not all(col in df.columns for col in ['fecha', 'capital_invertido', 'ganancias_perdidas_brutas']):
        st.warning("⚠️ No hay suficientes datos históricos para generar proyecciones")
        return
    
    try:
        # Preparar datos históricos
        historical_data = df[['fecha', 'capital_invertido', 'ganancias_perdidas_brutas']].copy()
        historical_data['tipo'] = 'Histórico'
        
        # Calcular métricas para proyección
        last_date = historical_data['fecha'].max()
        last_capital = historical_data['capital_invertido'].iloc[-1]
        last_profit = historical_data['ganancias_perdidas_brutas'].iloc[-1]
        
        # Calcular crecimiento promedio mensual con validación
        historical_data['crecimiento_capital'] = historical_data['capital_invertido'].pct_change()
        historical_data['crecimiento_ganancias'] = historical_data['ganancias_perdidas_brutas'].pct_change()
        
        avg_capital_growth = historical_data['crecimiento_capital'].mean()
        avg_profit_growth = historical_data['crecimiento_ganancias'].mean()
        
        # Valores por defecto si hay problemas con los cálculos
        if pd.isna(avg_capital_growth) or not np.isfinite(avg_capital_growth):
            avg_capital_growth = 0.02  # 2% mensual por defecto
        
        if pd.isna(avg_profit_growth) or not np.isfinite(avg_profit_growth):
            avg_profit_growth = 0.03  # 3% mensual por defecto
        
        # Crear fechas futuras (36 meses)
        future_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=36,
            freq='M'
        )
        
        # Escenario 1: Sin nueva inyección de capital
        scenario1 = pd.DataFrame({'fecha': future_dates})
        scenario1['capital_invertido'] = last_capital * (1 + avg_capital_growth) ** np.arange(1, 37)
        scenario1['ganancias_perdidas_brutas'] = last_profit * (1 + avg_profit_growth) ** np.arange(1, 37)
        scenario1['tipo'] = 'Escenario 1: Sin nueva inyección'
        
        # Escenario 2: Con inyección de capital de $5000 ahora y cada año
        scenario2 = pd.DataFrame({'fecha': future_dates})
        capital = last_capital + 5000  # Inyección inicial
        scenario2['capital_invertido'] = capital * (1 + avg_capital_growth) ** np.arange(1, 37)
        
        # Añadir inyecciones anuales
        for i, date in enumerate(scenario2['fecha']):
            if date.month == last_date.month and i > 0:  # Cada año
                scenario2.loc[i:, 'capital_invertido'] += 5000
        
        scenario2['ganancias_perdidas_brutas'] = (
            last_profit * (1 + avg_profit_growth) ** np.arange(1, 37) * 
            (scenario2['capital_invertido'] / last_capital))
        scenario2['tipo'] = 'Escenario 2: Con inyección de capital'
        
        # Combinar datos
        projection_data = pd.concat([historical_data, scenario1, scenario2])
        
        # Gráfico de proyección de capital
        st.markdown("### Proyección de Capital Invertido")
        fig_cap = px.line(
            projection_data,
            x='fecha',
            y='capital_invertido',
            color='tipo',
            title='Proyección de Capital Invertido (3 años)',
            labels={'capital_invertido': 'Monto ($)', 'fecha': 'Fecha'},
            template="plotly_dark"
        )
        fig_cap.update_layout(
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_cap, use_container_width=True)
        
        # Gráfico de proyección de ganancias
        st.markdown("### Proyección de Ganancias Brutas")
        fig_profit = px.line(
            projection_data,
            x='fecha',
            y='ganancias_perdidas_brutas',
            color='tipo',
            title='Proyección de Ganancias Brutas (3 años)',
            labels={'ganancias_perdidas_brutas': 'Monto ($)', 'fecha': 'Fecha'},
            template="plotly_dark"
        )
        fig_profit.update_layout(
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_profit, use_container_width=True)
        
        # Mostrar métricas clave de proyección
        st.markdown("### Resumen de Proyección")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Escenario 1: Sin nueva inyección**")
            st.metric("Capital final", f"${scenario1['capital_invertido'].iloc[-1]:,.2f}")
            st.metric("Ganancias acumuladas", f"${scenario1['ganancias_perdidas_brutas'].sum():,.2f}")
        
        with col2:
            st.markdown("**Escenario 2: Con inyección de capital**")
            st.metric("Capital final", f"${scenario2['capital_invertido'].iloc[-1]:,.2f}")
            st.metric("Ganancias acumuladas", f"${scenario2['ganancias_perdidas_brutas'].sum():,.2f}")
        
        # Explicación de supuestos
        st.markdown("---")
        st.markdown(f"""
        **Supuestos de la proyección:**
        - Tasas de crecimiento basadas en el desempeño histórico
        - Crecimiento mensual promedio del capital: {avg_capital_growth:.2%}
        - Crecimiento mensual promedio de ganancias: {avg_profit_growth:.2%}
        - Escenario 2 incluye inyección inicial de $5,000 y anualidades del mismo monto
        - Las proyecciones son estimativas y no garantizan resultados futuros
        """)
    except Exception as e:
        st.error(f"❌ Error al generar proyecciones: {str(e)}")

# =============================================
# INTERFAZ PRINCIPAL (MEJORADA)
# =============================================

def main():
    load_custom_style()
    st.title("📊 Fondo de Inversión Fallone Investment")
    
    # Mostrar información de ayuda
    with st.expander("ℹ️ Instrucciones", expanded=False):
        st.markdown("""
        1. **Sube tu archivo Excel** con los datos financieros
        2. **Selecciona la hoja** que contiene los datos
        3. **Usa los filtros** en la barra lateral para ajustar los datos
        4. **Explora las métricas** y gráficos en las diferentes pestañas
        
        **Columnas requeridas:**
        - Fecha (debe contener fechas válidas)
        - Capital Invertido (valores numéricos)
        - Ganancias/Pérdidas Brutas (valores numéricos)
        
        **Nota:** El sistema acepta variaciones en los nombres de estas columnas.
        """)
    
    uploaded_file = st.file_uploader("📤 Subir archivo Excel", type=['xlsx', 'xls'], help="Suba el archivo Excel con los datos financieros")
    
    if uploaded_file is not None:
        try:
            # Cargar datos
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            
            if not sheet_names:
                st.error("❌ El archivo Excel no contiene hojas válidas")
                st.stop()
            
            selected_sheet = st.selectbox(
                "📋 Seleccionar hoja de trabajo", 
                sheet_names,
                help="Seleccione la hoja que contiene los datos financieros"
            )
            
            @st.cache_data
            def load_data(file, sheet):
                df = pd.read_excel(file, sheet_name=sheet)
                df = normalize_column_names(df)
                return df.loc[:, ~df.columns.duplicated()]
            
            df = load_data(uploaded_file, selected_sheet)
            
            # Debug: Mostrar columnas disponibles
            if st.checkbox("🔍 Mostrar información de depuración", help="Muestra información técnica para resolver problemas"):
                st.write("### Columnas detectadas en el archivo:")
                st.write(df.columns.tolist())
                
                st.write("### Primeras filas de datos:")
                st.dataframe(df.head())
                
                st.write("### Tipos de datos detectados:")
                st.write(df.dtypes)
            
            # Validar datos
            is_valid, validation_msg = validate_dataframe(df)
            if not is_valid:
                st.error(f"❌ {validation_msg}")
                st.stop()
            
            # Obtener métricas iniciales
            capital_inicial = df['capital_invertido'].iloc[0] if len(df) > 0 else 0
            id_inversionista = df['id_inversionista'].iloc[0] if 'id_inversionista' in df.columns and len(df) > 0 else "N/D"
            
            fecha_entrada = df['fecha'].iloc[0] if len(df) > 0 else "N/D"
            if isinstance(fecha_entrada, pd.Timestamp):
                fecha_entrada = fecha_entrada.strftime('%d/%m/%Y')
            
            # Aplicar filtros
            filtered_df = advanced_filters(df)
            
            if len(filtered_df) == 0:
                st.warning("⚠️ No hay datos que coincidan con los filtros aplicados")
                st.stop()
            
            st.success(f"✅ Datos cargados correctamente ({len(filtered_df)} registros)")
            
            if not METRIC_CARDS_ENABLED:
                st.info("💡 Para mejores visualizaciones, instala: `pip install streamlit-extras`")
            
            # SECCIÓN DE KPIs
            st.markdown("---")
            st.markdown('<h2 style="color: #3f33ff; border-bottom: 2px solid #3f33ff; padding-bottom: 10px;">📊 KPIs Financieros</h2>', unsafe_allow_html=True)
            
            # Calcular métricas avanzadas
            current_capital = filtered_df['capital_invertido'].iloc[-1] if len(filtered_df) > 0 else 0
            delta_capital = current_capital - capital_inicial if len(filtered_df) > 0 else 0
            total_aumentos = filtered_df['aumento_capital'].sum() if 'aumento_capital' in filtered_df.columns else 0
            ganancias_brutas = filtered_df['ganancias_perdidas_brutas'].sum() if 'ganancias_perdidas_brutas' in filtered_df.columns else 0
            ganancias_netas = filtered_df['ganancias_perdidas_netas'].sum() if 'ganancias_perdidas_netas' in filtered_df.columns else 0
            comisiones = filtered_df['comisiones_pagadas'].sum() if 'comisiones_pagadas' in filtered_df.columns else 0
            retiros = filtered_df['retiro_fondos'].sum() if 'retiro_fondos' in filtered_df.columns else 0
            
            roi = calculate_roi(ganancias_netas, capital_inicial)
            cagr = calculate_cagr(filtered_df, capital_inicial, current_capital)
            sharpe_ratio = calculate_sharpe_ratio(filtered_df)
            max_drawdown = calculate_max_drawdown(filtered_df)
            
            # Mostrar KPIs
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                display_kpi("ID Inversionista", id_inversionista, "🆔", is_currency=False)
            with col2:
                display_kpi("Fecha de Entrada", fecha_entrada, "📅", is_currency=False)
            with col3:
                display_kpi("Capital Inicial", capital_inicial, "🏁")
            with col4:
                display_kpi("Capital Actual", current_capital, "🏦", delta=f"{delta_capital:+,.2f}")
            
            col5, col6, col7, col8 = st.columns(4)
            with col5:
                display_kpi("Total Inyección", total_aumentos, "📈")
            with col6:
                display_kpi("Ganancias Brutas", ganancias_brutas, "💵")
            with col7:
                display_kpi("Ganancias Netas", ganancias_netas, "💰")
            with col8:
                display_kpi("Comisiones Pagadas", comisiones, "💸")
            
            col9, col10, col11, col12 = st.columns(4)
            with col9:
                display_kpi("Retiro de Dinero", retiros, "↘️")
            with col10:
                display_kpi("ROI", roi, "📊", is_percentage=True)
            with col11:
                display_kpi("CAGR Mensual", cagr, "🚀", is_percentage=True)
            with col12:
                display_kpi("Drawdown Máximo", max_drawdown, "📉", is_percentage=True)
            
            # SECCIÓN DE GRÁFICOS PRINCIPALES
            st.markdown("---")
            tab1, tab2, tab3 = st.tabs(["📈 Visualizaciones Principales", "🔍 Detalle de Datos", "🔮 Proyección Futura"])
            
            with tab1:
                plot_combined_capital_withdrawals(filtered_df, capital_inicial)
                plot_capital_profit_relation(filtered_df)
                
                # Gráfico de ganancias/pérdidas
                if 'ganancias_perdidas_brutas' in filtered_df.columns:
                    fig = px.bar(
                        filtered_df,
                        x='fecha',
                        y='ganancias_perdidas_brutas',
                        title='Ganancias/Pérdidas Brutas por Periodo',
                        color='ganancias_perdidas_brutas',
                        color_continuous_scale=px.colors.diverging.RdYlGn,
                        labels={'ganancias_perdidas_brutas': 'Monto ($)', 'fecha': 'Fecha'},
                        template="plotly_dark"
                    )
                    fig.update_layout(
                        height=400,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Gráfico de comisiones acumuladas
                if 'comisiones_pagadas' in filtered_df.columns:
                    filtered_df['comisiones_acumuladas'] = filtered_df['comisiones_pagadas'].cumsum()
                    fig = px.area(
                        filtered_df,
                        x='fecha',
                        y='comisiones_acumuladas',
                        title='Comisiones Pagadas Acumuladas',
                        labels={'comisiones_acumuladas': 'Monto ($)', 'fecha': 'Fecha'},
                        template="plotly_dark"
                    )
                    fig.update_layout(
                        height=400,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                st.markdown("### Datos Filtrados")
                
                # Formatear DataFrame para visualización
                display_df = filtered_df.copy()
                numeric_cols = display_df.select_dtypes(include=['float64', 'int64']).columns
                format_dict = {col: "${:,.2f}" for col in numeric_col}
                
                st.dataframe(
                    display_df.style.format(format_dict),
                    use_container_width=True,
                    height=600
                )
                
                # Exportar datos
                st.markdown("---")
                st.markdown("### Exportar Datos")
                
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Descargar como CSV",
                    data=csv,
                    file_name="datos_filtrados_fallone.csv",
                    mime="text/csv",
                    help="Descarga los datos filtrados en formato CSV"
                )
            
            with tab3:
                plot_projection(filtered_df)
        
        except Exception as e:
            st.error(f"❌ Error crítico al procesar el archivo: {str(e)}")
            st.exception(e)
    else:
        st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")

if __name__ == "__main__":
    main()
