import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import base64
from io import BytesIO
import yfinance as yf
import ta  # Para análisis técnico

# Configuración inicial de la página
st.set_page_config(
    page_title="Dashboard Fallone Investments Pro",
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
# FUNCIONES PARA DATOS DE MERCADO EN TIEMPO REAL
# =============================================

@st.cache_data(ttl=60)  # Actualizar cada 60 segundos
def get_market_data(symbol, period='1d', interval='15m'):
    """Obtiene datos de mercado en tiempo real"""
    try:
        data = yf.download(
            tickers=symbol,
            period=period,
            interval=interval,
            progress=False
        )
        return data
    except Exception as e:
        st.error(f"Error al obtener datos para {symbol}: {str(e)}")
        return pd.DataFrame()

def add_technical_indicators(df):
    """Añade indicadores técnicos a los datos de mercado"""
    if df.empty:
        return df
    
    # Medias móviles
    df['MA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['MA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
    
    # RSI
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    # MACD
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    df['MACD_Hist'] = macd.macd_diff()
    
    return df.dropna()

def plot_market_chart(df, title):
    """Grafica los datos de mercado con indicadores técnicos"""
    if df.empty:
        st.warning(f"No hay datos disponibles para {title}")
        return
    
    fig = go.Figure()

    # Gráfico de velas
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Precio',
        increasing_line_color='#4CAF50',
        decreasing_line_color='#F44336'
    ))

    # Medias móviles
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['MA_20'],
        name='MA 20',
        line=dict(color='#FFA000', width=1.5)
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['MA_50'],
        name='MA 50',
        line=dict(color='#2196F3', width=1.5)
    ))

    fig.update_layout(
        title=f'{title} - Análisis Técnico',
        xaxis_title='Fecha/Hora',
        yaxis_title='Precio',
        template='plotly_dark',
        height=500,
        xaxis_rangeslider_visible=False,
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

# =============================================
# FUNCIONES ORIGINALES DEL DASHBOARD (CON CORRECCIONES)
# =============================================

def advanced_filters(df):
    """Función con selector de fechas por mes y año - Versión corregida"""
    with st.sidebar.expander("🔍 Filtros Avanzados", expanded=True):
        filtered_df = df.copy()
        
        if 'Fecha' in filtered_df.columns:
            try:
                filtered_df['Fecha'] = pd.to_datetime(filtered_df['Fecha'], errors='coerce')
                filtered_df = filtered_df.dropna(subset=['Fecha'])
                filtered_df['MesAño'] = filtered_df['Fecha'].dt.to_period('M')
                
                min_date = filtered_df['Fecha'].min().to_pydatetime()
                max_date = filtered_df['Fecha'].max().to_pydatetime()
                
                st.write("**Seleccione el rango de meses:**")
                col1, col2 = st.columns(2)
                
                with col1:
                    start_date = st.date_input(
                        "Mes inicial",
                        value=min_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="start_date"
                    )
                    start_date = datetime(start_date.year, start_date.month, 1)
                
                with col2:
                    end_date = st.date_input(
                        "Mes final",
                        value=max_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="end_date"
                    )
                    end_date = datetime(end_date.year, end_date.month, 1)
                
                start_period = pd.Period(start_date, freq='M')
                end_period = pd.Period(end_date, freq='M')
                
                filtered_df = filtered_df[
                    (filtered_df['MesAño'] >= start_period) & 
                    (filtered_df['MesAño'] <= end_period)
                ]
                
                filtered_df = filtered_df.drop(columns=['MesAño'])
                
            except Exception as e:
                st.warning(f"No se pudo aplicar el filtro de fechas: {str(e)}")
        
        if 'Capital Invertido' in filtered_df.columns:
            try:
                capital_series = pd.to_numeric(
                    filtered_df['Capital Invertido'], 
                    errors='coerce'
                ).dropna()
                
                if not capital_series.empty:
                    min_cap = float(capital_series.min())
                    max_cap = float(capital_series.max())
                    
                    cap_range = st.slider(
                        "Seleccione rango de capital",
                        min_value=min_cap,
                        max_value=max_cap,
                        value=(min_cap, max_cap),
                        help="Filtre por rango de capital invertido"
                    )
                    
                    filtered_df = filtered_df[
                        (pd.to_numeric(filtered_df['Capital Invertido'], errors='coerce') >= cap_range[0]) & 
                        (pd.to_numeric(filtered_df['Capital Invertido'], errors='coerce') <= cap_range[1])
                    ]
                else:
                    st.warning("No hay valores numéricos válidos en 'Capital Invertido'")
            except Exception as e:
                st.warning(f"No se pudo aplicar el filtro de capital: {str(e)}")
        
        if 'Ganancias/Pérdidas Brutas' in filtered_df.columns:
            try:
                profit_filter = st.selectbox(
                    "Filtrar por resultados",
                    options=["Todos", "Solo ganancias", "Solo pérdidas"],
                    index=0,
                    help="Filtre por tipo de resultados financieros"
                )
                
                if profit_filter == "Solo ganancias":
                    filtered_df = filtered_df[pd.to_numeric(filtered_df['Ganancias/Pérdidas Brutas'], errors='coerce') >= 0]
                elif profit_filter == "Solo pérdidas":
                    filtered_df = filtered_df[pd.to_numeric(filtered_df['Ganancias/Pérdidas Brutas'], errors='coerce') < 0]
            except Exception as e:
                st.warning(f"No se pudo aplicar el filtro de ganancias: {str(e)}")
    
    return filtered_df

def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False, delta=None):
    """Muestra un KPI con tooltip explicativo - Versión corregida"""
    kpi_explanations = {
        "ID Inversionista": "Identificador único del inversionista en el sistema.",
        "Fecha de Entrada al Fondo": "Fecha inicial de participación en el fondo de inversión.",
        "Capital Inicial": "Monto inicial invertido por el usuario.",
        "Capital Actual": "Valor actual de la inversión (incluyendo ganancias/pérdidas).",
        "Total Inyección de Capital": "Suma total de capital adicional aportado.",
        "Ganancias Brutas": "Beneficios antes de deducir comisiones e impuestos.",
        "Ganancias Netas": "Beneficios después de comisiones e impuestos.",
        "Comisiones Pagadas": "Total acumulado en comisiones de gestión.",
        "Retiro de Dinero": "Capital retirado por el inversionista.",
        "ROI": "Retorno sobre la inversión (Ganancias Netas / Capital Inicial).",
        "CAGR Mensual": "Tasa de crecimiento anual compuesto mensualizada.",
        "Drawdown Máximo": "Peor pérdida porcentual respecto al máximo histórico.",
        "Ratio Sharpe": "Medida de rendimiento ajustado al riesgo (mayor = mejor)."
    }

    # Formatear el valor de manera segura
    try:
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
    except:
        value_display = "Error"
        delta_display = None

    explanation = kpi_explanations.get(title, "Métrica financiera clave.")
    
    if METRIC_CARDS_ENABLED:
        metric_card(
            title=f"{icon} {title}",
            value=value_display,
            delta=delta_display,
            key=f"card_{title.replace(' ', '_')}",
            background="#1eca10",
            border_color="#8f10ca",
            border_size_px=4,
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
            background: #1024ca;
            color: #ffffff;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            margin-bottom: 20px;
            border-left: 4px solid #ca1040;
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

def plot_combined_capital_withdrawals(df, capital_inicial):
    """Gráfico combinado seguro"""
    if not all(col in df.columns for col in ['Fecha', 'Capital Invertido', 'Retiro de Fondos']):
        st.warning("Datos insuficientes para el gráfico combinado")
        return
        
    try:
        df = df.copy()
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha', 'Capital Invertido', 'Retiro de Fondos'])
        
        fig = go.Figure()

        # Gráfico de línea para capital
        fig.add_trace(go.Scatter(
            x=df['Fecha'],
            y=df['Capital Invertido'],
            name='Capital Invertido',
            line=dict(color='#4CAF50', width=2),
            mode='lines'
        ))
        
        # Barras para retiros
        fig.add_trace(go.Bar(
            x=df['Fecha'],
            y=df['Retiro de Fondos'],
            name='Retiros',
            marker_color='#FF6B6B',
            opacity=0.7
        ))
        
        # Línea de capital inicial
        if capital_inicial and not pd.isna(capital_inicial):
            fig.add_hline(
                y=float(capital_inicial),
                line_dash="dash",
                line_color="green",
                annotation_text=f"Capital Inicial: ${float(capital_inicial):,.2f}",
                annotation_position="bottom right"
            )
        
        fig.update_layout(
            title='Evolución del Capital vs Retiros',
            height=450,
            hovermode="x unified",
            template="plotly_dark",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error al generar gráfico: {str(e)}")

def plot_projection(df):
    """Gráficos de proyección a 3 años - Versión corregida"""
    if len(df) < 2 or 'Ganancias/Pérdidas Brutas' not in df.columns or 'Capital Invertido' not in df.columns:
        st.warning("No hay suficientes datos históricos para generar proyecciones")
        return
    
    try:
        # Preparar datos históricos
        historical_data = df[['Fecha', 'Capital Invertido', 'Ganancias/Pérdidas Brutas']].copy()
        historical_data['Tipo'] = 'Histórico'
        
        # Calcular métricas para proyección
        last_date = historical_data['Fecha'].max()
        last_capital = historical_data['Capital Invertido'].iloc[-1]
        last_profit = historical_data['Ganancias/Pérdidas Brutas'].iloc[-1]
        
        # Calcular crecimiento promedio mensual con manejo de errores
        historical_data['Crecimiento Capital'] = historical_data['Capital Invertido'].pct_change()
        historical_data['Crecimiento Ganancias'] = historical_data['Ganancias/Pérdidas Brutas'].pct_change()
        
        avg_capital_growth = historical_data['Crecimiento Capital'].mean()
        avg_profit_growth = historical_data['Crecimiento Ganancias'].mean()
        
        # Validar y ajustar tasas de crecimiento
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
        scenario1 = pd.DataFrame({'Fecha': future_dates})
        scenario1['Capital Invertido'] = last_capital * (1 + avg_capital_growth) ** np.arange(1, 37)
        scenario1['Ganancias/Pérdidas Brutas'] = last_profit * (1 + avg_profit_growth) ** np.arange(1, 37)
        scenario1['Tipo'] = 'Escenario 1: Sin nueva inyección'
        
        # Escenario 2: Con inyección de capital
        scenario2 = pd.DataFrame({'Fecha': future_dates})
        capital = last_capital + 5000  # Inyección inicial
        scenario2['Capital Invertido'] = capital * (1 + avg_capital_growth) ** np.arange(1, 37)
        
        # Añadir inyecciones anuales
        for i, date in enumerate(scenario2['Fecha']):
            if date.month == last_date.month and i > 0:  # Cada año
                scenario2.loc[i:, 'Capital Invertido'] += 5000
        
        scenario2['Ganancias/Pérdidas Brutas'] = last_profit * (1 + avg_profit_growth) ** np.arange(1, 37) * (scenario2['Capital Invertido'] / last_capital)
        scenario2['Tipo'] = 'Escenario 2: Con inyección de capital'
        
        # Combinar datos
        projection_data = pd.concat([historical_data, scenario1, scenario2])
        
        # Gráfico de proyección de capital
        st.markdown("### Proyección de Capital Invertido")
        fig_cap = px.line(
            projection_data,
            x='Fecha',
            y='Capital Invertido',
            color='Tipo',
            title='Proyección de Capital Invertido (3 años)',
            labels={'Capital Invertido': 'Monto ($)', 'Fecha': 'Fecha'},
            template="plotly_dark"
        )
        fig_cap.update_layout(height=500)
        st.plotly_chart(fig_cap, use_container_width=True)
        
        # Gráfico de proyección de ganancias
        st.markdown("### Proyección de Ganancias Brutas")
        fig_profit = px.line(
            projection_data,
            x='Fecha',
            y='Ganancias/Pérdidas Brutas',
            color='Tipo',
            title='Proyección de Ganancias Brutas (3 años)',
            labels={'Ganancias/Pérdidas Brutas': 'Monto ($)', 'Fecha': 'Fecha'},
            template="plotly_dark"
        )
        fig_profit.update_layout(height=500)
        st.plotly_chart(fig_profit, use_container_width=True)
        
        # Mostrar métricas clave de proyección
        st.markdown("### Resumen de Proyección")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Escenario 1: Sin nueva inyección**")
            st.metric("Capital final", f"${scenario1['Capital Invertido'].iloc[-1]:,.2f}")
            st.metric("Ganancias acumuladas", f"${scenario1['Ganancias/Pérdidas Brutas'].sum():,.2f}")
        
        with col2:
            st.markdown("**Escenario 2: Con inyección de capital**")
            st.metric("Capital final", f"${scenario2['Capital Invertido'].iloc[-1]:,.2f}")
            st.metric("Ganancias acumuladas", f"${scenario2['Ganancias/Pérdidas Brutas'].sum():,.2f}")
        
        # Explicación de supuestos
        st.markdown("---")
        st.markdown("""
        **Supuestos de la proyección:**
        - Tasas de crecimiento basadas en el desempeño histórico
        - Crecimiento mensual promedio del capital: {:.2%}
        - Crecimiento mensual promedio de ganancias: {:.2%}
        - Escenario 2 incluye inyección inicial de $5,000 y anualidades del mismo monto
        - Las proyecciones son estimativas y no garantizan resultados futuros
        """.format(avg_capital_growth, avg_profit_growth))
    
    except Exception as e:
        st.error(f"Error al generar proyecciones: {str(e)}")

# =============================================
# INTERFAZ PRINCIPAL MEJORADA
# =============================================

def main():
    st.title("📊 Dashboard Fallone Investments Pro")
    
    # Aplicar tema oscuro global
    st.markdown("""
    <style>
        .stApp {
            background-color: #121212;
            color: #ffffff;
        }
        .stSidebar {
            background-color: #1e1e1e !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1e88e5;
            color: white;
        }
        .technical-indicator {
            background-color: #1e1e1e;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Pestañas principales
    tab1, tab2 = st.tabs(["📊 Dashboard Inversiones", "📈 Mercados en Tiempo Real"])
    
    with tab1:
        # Carga de datos de inversión
        uploaded_file = st.file_uploader("📤 Subir archivo Excel", type=['xlsx', 'xls'])
        
        if uploaded_file is not None:
            try:
                xls = pd.ExcelFile(uploaded_file)
                sheet_names = xls.sheet_names
                selected_sheet = st.selectbox("📋 Seleccionar hoja de trabajo", sheet_names)
                
                @st.cache_data
                def load_data(file, sheet):
                    return pd.read_excel(file, sheet_name=sheet)

                df = load_data(uploaded_file, selected_sheet)
                df = df.loc[:, ~df.columns.duplicated()]
                
                # Limpieza de nombres de columnas
                rename_dict = {
                    'Ganacias/Pérdidas Brutas': 'Ganancias/Pérdidas Brutas',
                    'Ganacias/Pérdidas Netas': 'Ganancias/Pérdidas Netas',
                    'Beneficio en %': 'Beneficio %'
                }
                
                for old_name, new_name in rename_dict.items():
                    if old_name in df.columns and new_name not in df.columns:
                        df = df.rename(columns={old_name: new_name})
                
                if 'Comisiones 10 %' in df.columns:
                    if 'Comisiones Pagadas' not in df.columns:
                        df = df.rename(columns={'Comisiones 10 %': 'Comisiones Pagadas'})
                    else:
                        df = df.drop(columns=['Comisiones 10 %'])
                
                capital_inicial = df['Aumento Capital'].iloc[1] if len(df) > 1 else 0
                id_inversionista = df['ID Inv'].iloc[1] if len(df) > 1 else "N/D"
                
                fecha_entrada = df['Fecha'].iloc[1] if len(df) > 1 else "N/D"
                if isinstance(fecha_entrada, pd.Timestamp):
                    fecha_entrada = fecha_entrada.strftime('%d/%m/%Y')
                
                filtered_df = advanced_filters(df)
                
                # Validación de columnas requeridas
                required_columns = ['Fecha', 'Capital Invertido', 'Aumento Capital', 'ID Inv', 'Retiro de Fondos']
                missing_cols = [col for col in required_columns if col not in filtered_df.columns]
                
                if missing_cols:
                    st.error(f"🚨 Error: Faltan columnas críticas: {', '.join(missing_cols)}")
                    st.stop()
                
                st.success(f"✅ Datos cargados correctamente ({len(filtered_df)} registros)")
                
                if not METRIC_CARDS_ENABLED:
                    st.warning("Para mejores visualizaciones, instala: pip install streamlit-extras")
                
                # SECCIÓN DE KPIs
                st.markdown("---")
                st.markdown('<h2 style="color: #1024ca; border-bottom: 2px solid #8f10ca; padding-bottom: 10px;">📊 KPIs Financieros</h2>', unsafe_allow_html=True)
                
                # Calcular métricas avanzadas
                current_capital = filtered_df['Capital Invertido'].iloc[-1] if len(filtered_df) > 0 else 0
                delta_capital = current_capital - capital_inicial if len(filtered_df) > 0 else 0
                total_aumentos = filtered_df['Aumento Capital'].sum()
                ganancias_brutas = filtered_df['Ganancias/Pérdidas Brutas'].sum() if 'Ganancias/Pérdidas Brutas' in filtered_df.columns else None
                ganancias_netas = filtered_df['Ganancias/Pérdidas Netas'].sum() if 'Ganancias/Pérdidas Netas' in filtered_df.columns else None
                comisiones = filtered_df['Comisiones Pagadas'].sum() if 'Comisiones Pagadas' in filtered_df.columns else None
                retiros = filtered_df['Retiro de Fondos'].sum() if 'Retiro de Fondos' in filtered_df.columns else None
                
                roi = calculate_roi(filtered_df, capital_inicial)
                cagr = calculate_cagr(filtered_df, capital_inicial, current_capital)
                sharpe_ratio = calculate_sharpe_ratio(filtered_df)
                max_drawdown = calculate_max_drawdown(filtered_df)
                
                # Mostrar KPIs
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    display_kpi("ID Inversionista", id_inversionista, "🆔", is_currency=False)
                with col2:
                    display_kpi("Fecha de Entrada al Fondo", fecha_entrada, "📅", is_currency=False)
                with col3:
                    display_kpi("Capital Inicial", capital_inicial, "🏁")
                with col4:
                    display_kpi("Capital Actual", current_capital, "🏦", delta=f"{delta_capital:+,.2f}")
                
                # Más KPIs...
                
                # SECCIÓN DE GRÁFICOS PRINCIPALES
                st.markdown("---")
                st.markdown("### 📈 Visualizaciones Principales")
                
                # Gráfico combinado de capital y retiros
                plot_combined_capital_withdrawals(filtered_df, capital_inicial)
                
                # Más gráficos y análisis...
                
                # SECCIÓN DE PROYECCIÓN
                st.markdown("---")
                st.markdown("### 🔮 Proyección Futura")
                plot_projection(filtered_df)
                
                # Exportación de datos
                if st.button("📄 Exportar Datos Filtrados a CSV"):
                    csv = filtered_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Descargar CSV",
                        data=csv,
                        file_name="datos_filtrados_fallone.csv",
                        mime="text/csv"
                    )
            
            except Exception as e:
                st.error(f"🚨 Error crítico al procesar el archivo: {str(e)}")
        else:
            st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")
    
    with tab2:
        st.header("📈 Mercados en Tiempo Real")
        
        # Configuración del sidebar para datos de mercado
        with st.sidebar:
            st.header("⚙️ Configuración de Mercado")
            timeframe = st.selectbox(
                "Intervalo de tiempo",
                options=["15m", "1h", "4h", "1d"],
                index=0
            )
            
            period_map = {
                "15m": "1d",
                "1h": "1d",
                "4h": "5d",
                "1d": "1mo"
            }
            
            period = period_map[timeframe]
        
        # Pestañas para cada activo
        market_tab1, market_tab2 = st.tabs(["NASDAQ 100 (^NDX)", "Oro (XAU/USD)"])
        
        with market_tab1:
            st.subheader("NASDAQ 100 - Análisis en Tiempo Real")
            ndx_data = get_market_data("^NDX", period, timeframe)
            ndx_data = add_technical_indicators(ndx_data)
            
            plot_market_chart(ndx_data, "NASDAQ 100")
            
            if not ndx_data.empty:
                st.subheader("📊 Análisis Técnico NASDAQ 100")
                
                # Mostrar indicadores técnicos
                last_data = ndx_data.iloc[-1]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    rsi_status = "Sobrecomprado (>70)" if last_data['RSI'] > 70 else "Sobreventa (<30)" if last_data['RSI'] < 30 else "Neutro"
                    st.markdown(f"""
                    <div class="technical-indicator">
                        <h4>RSI (14 periodos)</h4>
                        <div class="indicator-value {'bearish' if last_data['RSI'] > 70 else 'bullish' if last_data['RSI'] < 30 else ''}">
                            {last_data['RSI']:.2f}
                        </div>
                        <p>{rsi_status}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    macd_trend = "Alcista" if last_data['MACD'] > last_data['MACD_Signal'] else "Bajista"
                    st.markdown(f"""
                    <div class="technical-indicator">
                        <h4>MACD</h4>
                        <div>Linea: {last_data['MACD']:.4f}</div>
                        <div>Señal: {last_data['MACD_Signal']:.4f}</div>
                        <div class="indicator-value {'bullish' if macd_trend == "Alcista" else 'bearish'}">
                            {macd_trend}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    ma_trend = "Alcista" if last_data['MA_20'] > last_data['MA_50'] else "Bajista"
                    st.markdown(f"""
                    <div class="technical-indicator">
                        <h4>Medias Móviles</h4>
                        <div>MA20: {last_data['MA_20']:.2f}</div>
                        <div>MA50: {last_data['MA_50']:.2f}</div>
                        <div class="indicator-value {'bullish' if ma_trend == "Alcista" else 'bearish'}">
                            {ma_trend}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with market_tab2:
            st.subheader("Oro (XAU/USD) - Análisis en Tiempo Real")
            gold_data = get_market_data("GC=F", period, timeframe)
            gold_data = add_technical_indicators(gold_data)
            
            plot_market_chart(gold_data, "XAU/USD")
            
            if not gold_data.empty:
                st.subheader("📊 Análisis Técnico XAU/USD")
                
                # Mostrar indicadores técnicos
                last_data = gold_data.iloc[-1]
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    rsi_status = "Sobrecomprado (>70)" if last_data['RSI'] > 70 else "Sobreventa (<30)" if last_data['RSI'] < 30 else "Neutro"
                    st.markdown(f"""
                    <div class="technical-indicator">
                        <h4>RSI (14 periodos)</h4>
                        <div class="indicator-value {'bearish' if last_data['RSI'] > 70 else 'bullish' if last_data['RSI'] < 30 else ''}">
                            {last_data['RSI']:.2f}
                        </div>
                        <p>{rsi_status}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    macd_trend = "Alcista" if last_data['MACD'] > last_data['MACD_Signal'] else "Bajista"
                    st.markdown(f"""
                    <div class="technical-indicator">
                        <h4>MACD</h4>
                        <div>Linea: {last_data['MACD']:.4f}</div>
                        <div>Señal: {last_data['MACD_Signal']:.4f}</div>
                        <div class="indicator-value {'bullish' if macd_trend == "Alcista" else 'bearish'}">
                            {macd_trend}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    ma_trend = "Alcista" if last_data['MA_20'] > last_data['MA_50'] else "Bajista"
                    st.markdown(f"""
                    <div class="technical-indicator">
                        <h4>Medias Móviles</h4>
                        <div>MA20: {last_data['MA_20']:.2f}</div>
                        <div>MA50: {last_data['MA_50']:.2f}</div>
                        <div class="indicator-value {'bullish' if ma_trend == "Alcista" else 'bearish'}">
                            {ma_trend}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

    # Pie de página
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #9E9E9E; font-size: 0.9rem;">
        <p>Datos de mercado proporcionados por Yahoo Finance. Actualizado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>⚠️ Este dashboard es para fines educativos. No constituye asesoramiento financiero.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
