import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
# FUNCIÓN DE FILTROS AVANZADOS (Optimizada)
# =============================================

def advanced_filters(df):
    """Función optimizada para filtrado de datos"""
    with st.sidebar.expander("🔍 Filtros Avanzados", expanded=True):
        filtered_df = df.copy()
        
        # Filtro por fechas
        if 'Fecha' in filtered_df.columns:
            try:
                filtered_df['Fecha'] = pd.to_datetime(filtered_df['Fecha'], errors='coerce')
                filtered_df = filtered_df.dropna(subset=['Fecha'])
                
                min_date = filtered_df['Fecha'].min().to_pydatetime()
                max_date = filtered_df['Fecha'].max().to_pydatetime()
                
                st.write("**Rango de fechas:**")
                date_range = st.date_input(
                    "Seleccione el rango",
                    [min_date, max_date],
                    min_value=min_date,
                    max_value=max_date,
                    key="date_range"
                )
                
                if len(date_range) == 2:
                    start_date = datetime.combine(date_range[0], datetime.min.time())
                    end_date = datetime.combine(date_range[1], datetime.max.time())
                    filtered_df = filtered_df[(filtered_df['Fecha'] >= start_date) & 
                                            (filtered_df['Fecha'] <= end_date)]
            except Exception as e:
                st.warning(f"Error en filtro de fechas: {str(e)}")
        
        # Filtro por capital
        if 'Capital Invertido' in filtered_df.columns:
            try:
                capital_series = pd.to_numeric(filtered_df['Capital Invertido'], errors='coerce').dropna()
                if not capital_series.empty:
                    min_val, max_val = float(capital_series.min()), float(capital_series.max())
                    val_range = st.slider(
                        "Rango de capital",
                        min_val, max_val,
                        (min_val, max_val),
                        key="capital_range"
                    )
                    filtered_df = filtered_df[
                        (pd.to_numeric(filtered_df['Capital Invertido'], errors='coerce') >= val_range[0]) & 
                        (pd.to_numeric(filtered_df['Capital Invertido'], errors='coerce') <= val_range[1])
                    ]
            except Exception as e:
                st.warning(f"Error en filtro de capital: {str(e)}")
        
        # Filtro por resultados
        if 'Ganancias/Pérdidas Brutas' in filtered_df.columns:
            try:
                result_filter = st.radio(
                    "Filtrar por resultados:",
                    ["Todos", "Solo ganancias", "Solo pérdidas"],
                    index=0,
                    key="result_filter"
                )
                
                if result_filter == "Solo ganancias":
                    filtered_df = filtered_df[filtered_df['Ganancias/Pérdidas Brutas'] >= 0]
                elif result_filter == "Solo pérdidas":
                    filtered_df = filtered_df[filtered_df['Ganancias/Pérdidas Brutas'] < 0]
            except Exception as e:
                st.warning(f"Error en filtro de resultados: {str(e)}")
    
    return filtered_df

# =============================================
# FUNCIÓN PARA KPIs (Mejorada)
# =============================================

def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False, delta=None):
    """Función optimizada para mostrar KPIs"""
    kpi_explanations = {
        "ID Inversionista": "Identificador único del inversionista",
        "Capital Inicial": "Monto inicial invertido",
        "ROI": "Retorno sobre la inversión (Ganancias Netas / Capital Inicial)",
        # ... (otros tooltips)
    }
    
    # Formateo del valor
    if pd.isna(value) or value is None:
        value_display = "N/D"
    else:
        if is_currency:
            value_display = f"${float(value):,.2f}"
        elif is_percentage:
            value_display = f"{float(value):.2f}%"
        else:
            value_display = f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
    
    # Tooltip
    explanation = kpi_explanations.get(title, "Métrica financiera clave.")
    
    if METRIC_CARDS_ENABLED:
        metric_card(
            title=f"{icon} {title}",
            value=value_display,
            delta=delta,
            key=f"card_{title.replace(' ', '_')}",
            help=explanation
        )
    else:
        st.markdown(f"""
        <div style="
            background: #1024ca;
            color: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            border-left: 4px solid #ca1040;
        ">
            <div style="font-weight: 600; font-size: 14px;">
                {icon} {title}
                <span title="{explanation}" style="cursor: help;">ℹ️</span>
            </div>
            <div style="font-weight: 700; font-size: 24px; margin: 10px 0;">{value_display}</div>
        </div>
        """, unsafe_allow_html=True)

# =============================================
# GRÁFICOS PRINCIPALES (Optimizados)
# =============================================

def plot_combined_capital_withdrawals(df, capital_inicial):
    """Gráfico combinado optimizado"""
    if not all(col in df.columns for col in ['Fecha', 'Capital Invertido', 'Retiro de Fondos']):
        return st.warning("Datos insuficientes para el gráfico")
    
    fig = go.Figure()
    
    # Línea de capital
    fig.add_trace(go.Scatter(
        x=df['Fecha'],
        y=df['Capital Invertido'],
        name='Capital',
        line=dict(color='#636EFA'),
        mode='lines'
    ))
    
    # Barras de retiros
    fig.add_trace(go.Bar(
        x=df['Fecha'],
        y=df['Retiro de Fondos'],
        name='Retiros',
        marker_color='#FF6B6B',
        opacity=0.7
    ))
    
    # Línea de capital inicial
    fig.add_hline(
        y=capital_inicial,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Capital Inicial: ${capital_inicial:,.2f}"
    )
    
    fig.update_layout(
        title='<b>Evolución del Capital vs Retiros</b>',
        template="plotly_dark",
        height=450,
        barmode='overlay',
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

# =============================================
# PROYECCIÓN FUTURA (Versión Mejorada)
# =============================================

def plot_projection(df):
    """Función optimizada de proyección futura"""
    # Validación de datos
    if len(df) < 3 or not all(col in df.columns for col in ['Fecha', 'Capital Invertido', 'Ganancias/Pérdidas Brutas']):
        return st.warning("Se requieren al menos 3 meses de datos para proyecciones")
    
    try:
        # Preparación de datos
        hist_data = df[['Fecha', 'Capital Invertido', 'Ganancias/Pérdidas Brutas']].copy().dropna()
        hist_data['Tipo'] = 'Histórico'
        
        # Cálculo de tendencias con media móvil
        hist_data['Capital_MA'] = hist_data['Capital Invertido'].rolling(3, min_periods=1).mean()
        hist_data['Ganancias_MA'] = hist_data['Ganancias/Pérdidas Brutas'].rolling(3, min_periods=1).mean()
        
        # Tasas de crecimiento
        cap_growth = hist_data['Capital_MA'].pct_change().iloc[-6:].mean()
        profit_growth = hist_data['Ganancias_MA'].pct_change().iloc[-6:].mean()
        
        # Escenarios
        scenarios = {
            'Pesimista': {'cap_factor': 0.8, 'profit_factor': 0.7, 'color': '#EF553B'},
            'Conservador': {'cap_factor': 1.0, 'profit_factor': 0.9, 'color': '#FFA15A'},
            'Moderado': {'cap_factor': 1.2, 'profit_factor': 1.1, 'color': '#00CC96'},
            'Optimista': {'cap_factor': 1.5, 'profit_factor': 1.3, 'color': '#AB63FA'}
        }
        
        # Generación de proyecciones
        last_date = hist_data['Fecha'].iloc[-1]
        projection_data = hist_data.copy()
        
        for name, params in scenarios.items():
            future_dates = pd.date_range(last_date + pd.DateOffset(months=1), periods=36, freq='M')
            scenario_df = pd.DataFrame({
                'Fecha': future_dates,
                'Capital Invertido': hist_data['Capital Invertido'].iloc[-1] * 
                                    (1 + cap_growth * params['cap_factor']) ** np.arange(1, 37),
                'Ganancias/Pérdidas Brutas': hist_data['Ganancias/Pérdidas Brutas'].iloc[-1] * 
                                            (1 + profit_growth * params['profit_factor']) ** np.arange(1, 37),
                'Tipo': name,
                'color': params['color']
            })
            projection_data = pd.concat([projection_data, scenario_df])
        
        # Visualización
        st.markdown("### 📈 Proyección de Ganancias (3 años)")
        
        fig = px.line(
            projection_data,
            x='Fecha',
            y='Ganancias/Pérdidas Brutas',
            color='Tipo',
            color_discrete_map={k: v['color'] for k, v in scenarios.items()},
            template="plotly_dark",
            height=500
        )
        
        # Rango probable
        fig.add_trace(go.Scatter(
            x=projection_data[projection_data['Tipo'].isin(['Conservador', 'Moderado'])].groupby('Fecha')['Ganancias/Pérdidas Brutas'].max().index,
            y=projection_data[projection_data['Tipo'].isin(['Conservador', 'Moderado'])].groupby('Fecha')['Ganancias/Pérdidas Brutas'].max(),
            fill=None,
            mode='lines',
            line=dict(width=0),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=projection_data[projection_data['Tipo'].isin(['Conservador', 'Moderado'])].groupby('Fecha')['Ganancias/Pérdidas Brutas'].min().index,
            y=projection_data[projection_data['Tipo'].isin(['Conservador', 'Moderado'])].groupby('Fecha')['Ganancias/Pérdidas Brutas'].min(),
            fill='tonexty',
            mode='lines',
            line=dict(width=0),
            fillcolor='rgba(100, 200, 100, 0.2)',
            showlegend=False
        ))
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Resumen de métricas
        st.markdown("### 📊 Resumen por Escenario")
        cols = st.columns(len(scenarios))
        
        for idx, (name, params) in enumerate(scenarios.items()):
            with cols[idx]:
                scenario_df = projection_data[projection_data['Tipo'] == name]
                st.markdown(f"<div style='border-left: 4px solid {params['color']}; padding-left: 10px;'>", unsafe_allow_html=True)
                st.markdown(f"**{name}**")
                st.metric("Ganancias finales", f"${scenario_df['Ganancias/Pérdidas Brutas'].iloc[-1]:,.0f}")
                st.metric("Crecimiento anual", 
                         f"{((scenario_df['Capital Invertido'].iloc[-1] / scenario_df['Capital Invertido'].iloc[0]) ** (1/3) - 1):.1%}")
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Explicación
        with st.expander("📌 Detalles de la Proyección"):
            st.markdown(f"""
            **Metodología:**
            - Tasas base: Capital {cap_growth:.2%} mensual, Ganancias {profit_growth:.2%} mensual
            - Escenarios ajustan estas tasas según factores
            - Rango probable entre Conservador y Moderado
            """)
            
    except Exception as e:
        st.error(f"Error en proyección: {str(e)}")

# =============================================
# INTERFAZ PRINCIPAL (Optimizada)
# =============================================

def main():
    # Configuración de estilo
    st.markdown("""
    <style>
        .stApp { background-color: #121212; color: white; }
        .stSidebar { background-color: #1e1e1e !important; }
        .stTextInput, .stSelectbox, .stSlider { background-color: #2d2d2d; }
        .stButton>button { background-color: #3f33ff; color: white; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📊 Dashboard Financiero Fallone")
    
    # Carga de datos
    uploaded_file = st.file_uploader("Subir archivo Excel", type=['xlsx', 'xls'])
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Limpieza de nombres de columnas
            df.columns = df.columns.str.replace('Ganacias', 'Ganancias')
            
            # Filtrado
            filtered_df = advanced_filters(df)
            
            # KPIs
            st.markdown("## 📈 Métricas Clave")
            cols = st.columns(4)
            with cols[0]:
                display_kpi("Capital Actual", filtered_df['Capital Invertido'].iloc[-1])
            with cols[1]:
                display_kpi("ROI", calculate_roi(filtered_df, filtered_df['Capital Invertido'].iloc[0]), is_percentage=True)
            # ... más KPIs
            
            # Pestañas principales
            tab1, tab2, tab3 = st.tabs(["Visualizaciones", "Análisis", "Proyección"])
            
            with tab1:
                plot_combined_capital_withdrawals(filtered_df, filtered_df['Capital Invertido'].iloc[0])
                # ... más gráficos
                
            with tab3:
                plot_projection(filtered_df)
                
        except Exception as e:
            st.error(f"Error al procesar datos: {str(e)}")

if __name__ == "__main__":
    main()
