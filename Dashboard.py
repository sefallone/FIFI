import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import base64
from io import BytesIO
import hashlib
import yfinance as yf
import ta  # Para análisis técnico
from streamlit_extras.metric_cards import metric_card

# =============================================
# CONFIGURACIÓN INICIAL
# =============================================
st.set_page_config(
    page_title="Dashboard Fallone Investments Pro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# FUNCIONES DE SEGURIDAD Y VALIDACIÓN
# =============================================
def validate_file(file):
    """Valida el archivo subido"""
    if not file:
        return False
    
    if file.type not in ["application/vnd.ms-excel", 
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        return False
    
    if file.size > 10 * 1024 * 1024:  # 10MB máximo
        return False
        
    return True

def sanitize_df(df):
    """Limpia y protege el DataFrame"""
    dangerous_cols = ['formula', 'object', 'macro']
    df = df.loc[:, ~df.columns.str.lower().isin(dangerous_cols)]
    
    for col in df.columns:
        df[col] = df[col].astype(str).str[:500]
        
    return df

# =============================================
# FUNCIONES PARA DATOS EN TIEMPO REAL (MERCADOS)
# =============================================
@st.cache_data(ttl=60)  # Actualizar cada 60 segundos
def get_realtime_data(symbol, period='1d', interval='15m'):
    """Obtiene datos de mercado en tiempo real"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7) if period == '1wk' else end_date - timedelta(days=1)
    
    try:
        data = yf.download(
            tickers=symbol,
            start=start_date,
            end=end_date,
            interval=interval,
            progress=False
        )
        return data
    except Exception as e:
        st.error(f"Error al obtener datos para {symbol}: {str(e)}")
        return pd.DataFrame()

def calculate_technical_indicators(df):
    """Calcula indicadores técnicos"""
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
    
    # Bollinger Bands
    bollinger = ta.volatility.BollingerBands(df['Close'])
    df['BB_Upper'] = bollinger.bollinger_hband()
    df['BB_Lower'] = bollinger.bollinger_lband()
    
    return df.dropna()

# =============================================
# FUNCIONES PARA EL DASHBOARD DE INVERSIONES
# =============================================
def advanced_filters(df):
    """Filtros avanzados con validación mejorada"""
    with st.sidebar.expander("🔍 Filtros Avanzados", expanded=True):
        filtered_df = df.copy()
        
        # Validación de columnas requeridas
        required_cols = ['Fecha', 'Capital Invertido']
        missing = [col for col in required_cols if col not in filtered_df.columns]
        if missing:
            st.error(f"Faltan columnas requeridas: {', '.join(missing)}")
            return df
        
        # Manejo de fechas
        try:
            filtered_df['Fecha'] = pd.to_datetime(filtered_df['Fecha'], errors='coerce')
            if filtered_df['Fecha'].isnull().all():
                st.warning("No hay fechas válidas para filtrar")
                return filtered_df
            
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
                    key="secure_start_date"
                )
                start_date = datetime(start_date.year, start_date.month, 1)
            
            with col2:
                end_date = st.date_input(
                    "Mes final",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date,
                    key="secure_end_date"
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
            st.error(f"Error en filtro de fechas: {str(e)}")
            return df
        
        # Filtro de capital con validación
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
        
        # Filtro de ganancias/pérdidas con validación
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
    
    return filtered_df.dropna(subset=['Fecha'])

# =============================================
# FUNCIONES DE VISUALIZACIÓN MEJORADAS
# =============================================
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

def plot_market_data(df, symbol):
    """Grafica datos de mercado con indicadores técnicos"""
    if df.empty:
        st.warning(f"No hay datos disponibles para {symbol}")
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

    # Bollinger Bands
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['BB_Upper'],
        name='BB Superior',
        line=dict(color='#9E9E9E', width=1, dash='dot')
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['BB_Lower'],
        name='BB Inferior',
        line=dict(color='#9E9E9E', width=1, dash='dot'),
        fill='tonexty',
        fillcolor='rgba(158, 158, 158, 0.1)'
    ))

    fig.update_layout(
        title=f'{symbol} - Análisis Técnico',
        xaxis_title='Fecha/Hora',
        yaxis_title='Precio',
        template='plotly_dark',
        height=600,
        xaxis_rangeslider_visible=False,
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

# =============================================
# INTERFAZ PRINCIPAL
# =============================================
def main():
    # Configuración de estilo
    st.markdown("""
    <style>
        .stApp {
            background-color: #121212;
            color: #ffffff;
        }
        .stAlert {
            background-color: #2d2d2d !important;
        }
        .technical-indicator {
            background-color: #1e1e1e;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
        }
        .indicator-value {
            font-size: 1.2rem;
            font-weight: bold;
        }
        .bullish {
            color: #4CAF50;
        }
        .bearish {
            color: #F44336;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Tabs principales
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard Inversiones", "📈 Mercado en Tiempo Real", "🔍 Comparativas"])
    
    with tab1:
        st.title("📊 Dashboard de Inversiones Fallone")
        
        # Carga de datos de inversión
        with st.sidebar:
            st.header("📤 Carga de Datos")
            uploaded_file = st.file_uploader(
                "Subir archivo Excel", 
                type=['xlsx', 'xls'],
                help="Suba un archivo Excel con datos de inversión"
            )
            
            if not uploaded_file:
                st.info("Por favor, suba un archivo Excel para comenzar")
                st.stop()
                
            if not validate_file(uploaded_file):
                st.error("Archivo no válido. Por favor suba un archivo Excel válido (max 10MB)")
                st.stop()
                
            try:
                @st.cache_data(ttl=3600)
                def load_data(file):
                    xls = pd.ExcelFile(file)
                    sheets = xls.sheet_names
                    return {sheet: sanitize_df(pd.read_excel(xls, sheet_name=sheet)) for sheet in sheets}
                    
                data = load_data(uploaded_file)
                selected_sheet = st.selectbox("Seleccionar hoja", list(data.keys()))
                df = data[selected_sheet]
                
                if df.empty:
                    st.error("La hoja seleccionada está vacía")
                    st.stop()
                    
                capital_inicial = pd.to_numeric(df['Aumento Capital'].iloc[1], errors='coerce') if len(df) > 1 else 0
                if pd.isna(capital_inicial) or capital_inicial <= 0:
                    st.error("El capital inicial no es válido")
                    st.stop()
                    
                filtered_df = advanced_filters(df)
                
            except Exception as e:
                st.error(f"Error al procesar el archivo: {str(e)}")
                st.stop()
        
        # Visualización de datos de inversión
        if not filtered_df.empty:
            current_capital = pd.to_numeric(filtered_df['Capital Invertido'].iloc[-1], errors='coerce') if len(filtered_df) > 0 else 0
            delta_capital = current_capital - capital_inicial if current_capital else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Capital Inicial", f"${capital_inicial:,.2f}")
            with col2:
                st.metric("Capital Actual", f"${current_capital:,.2f}", delta=f"{delta_capital:+,.2f}")
            
            plot_combined_capital_withdrawals(filtered_df, capital_inicial)
            
            if st.button("Exportar Datos Filtrados"):
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Descargar CSV",
                    data=csv,
                    file_name="datos_filtrados.csv",
                    mime="text/csv"
                )
    
    with tab2:
        st.title("📈 Mercados en Tiempo Real")
        
        # Configuración de mercado
        with st.sidebar:
            st.header("⚙️ Configuración de Mercado")
            timeframe = st.selectbox(
                "Intervalo de tiempo",
                options=["15 Minutos", "1 Hora", "4 Horas", "1 Día"],
                index=0
            )
            
            period_map = {
                "15 Minutos": ("1d", "15m"),
                "1 Hora": ("1d", "60m"),
                "4 Horas": ("5d", "60m"),
                "1 Día": ("1mo", "1d")
            }
            
            period, interval = period_map[timeframe]
        
        # Pestañas para cada activo
        market_tab1, market_tab2 = st.tabs(["NASDAQ 100 (NAS100)", "Oro (XAU/USD)"])
        
        with market_tab1:
            nasdaq_data = get_realtime_data("^NDX", period, interval)
            nasdaq_data = calculate_technical_indicators(nasdaq_data)
            
            plot_market_data(nasdaq_data, "NAS100")
            
            # Análisis técnico
            if not nasdaq_data.empty:
                last_data = nasdaq_data.iloc[-1]
                
                st.subheader("📊 Análisis Técnico NAS100")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div class="technical-indicator">
                        <h4>RSI (14)</h4>
                        <div class="indicator-value {'bearish' if last_data['RSI'] > 70 else 'bullish' if last_data['RSI'] < 30 else ''}">
                            {last_data['RSI']:.2f}
                        </div>
                        <p>{'Sobrecomprado (>70)' if last_data['RSI'] > 70 else 'Sobreventa (<30)' if last_data['RSI'] < 30 else 'Neutro'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    macd_trend = "Alcista" if last_data['MACD'] > last_data['MACD_Signal'] else "Bajista"
                    st.markdown(f"""
                    <div class="technical-indicator">
                        <h4>MACD</h4>
                        <div>Linea: {last_data['MACD']:.4f}</div>
                        <div>Señal: {last_data['MACD_Signal']:.4f}</div>
                        <div class="indicator-value {'bullish' if macd_trend == 'Alcista' else 'bearish'}">
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
                        <div class="indicator-value {'bullish' if ma_trend == 'Alcista' else 'bearish'}">
                            {ma_trend}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        with market_tab2:
            gold_data = get_realtime_data("GC=F", period, interval)
            gold_data = calculate_technical_indicators(gold_data)
            
            plot_market_data(gold_data, "XAU/USD")
            
            # Análisis técnico para oro
            if not gold_data.empty:
                last_data = gold_data.iloc[-1]
                
                st.subheader("📊 Análisis Técnico XAU/USD")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div class="technical-indicator">
                        <h4>RSI (14)</h4>
                        <div class="indicator-value {'bearish' if last_data['RSI'] > 70 else 'bullish' if last_data['RSI'] < 30 else ''}">
                            {last_data['RSI']:.2f}
                        </div>
                        <p>{'Sobrecomprado (>70)' if last_data['RSI'] > 70 else 'Sobreventa (<30)' if last_data['RSI'] < 30 else 'Neutro'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    macd_trend = "Alcista" if last_data['MACD'] > last_data['MACD_Signal'] else "Bajista"
                    st.markdown(f"""
                    <div class="technical-indicator">
                        <h4>MACD</h4>
                        <div>Linea: {last_data['MACD']:.4f}</div>
                        <div>Señal: {last_data['MACD_Signal']:.4f}</div>
                        <div class="indicator-value {'bullish' if macd_trend == 'Alcista' else 'bearish'}">
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
                        <div class="indicator-value {'bullish' if ma_trend == 'Alcista' else 'bearish'}">
                            {ma_trend}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    with tab3:
        st.title("🔍 Comparativa de Mercados")
        
        if 'nasdaq_data' in locals() and 'gold_data' in locals():
            if not nasdaq_data.empty and not gold_data.empty:
                # Normalizar precios para comparación
                norm_nasdaq = (nasdaq_data['Close'] / nasdaq_data['Close'].iloc[0]) * 100
                norm_gold = (gold_data['Close'] / gold_data['Close'].iloc[0]) * 100
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=norm_nasdaq.index,
                    y=norm_nasdaq,
                    name='NAS100',
                    line=dict(color='#2196F3', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=norm_gold.index,
                    y=norm_gold,
                    name='XAU/USD',
                    line=dict(color='#FFC107', width=2)
                ))
                
                fig.update_layout(
                    title='Comparativa de Rendimiento Normalizado',
                    yaxis_title='Rendimiento (%)',
                    template='plotly_dark',
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Análisis de correlación
                merged_data = pd.concat([nasdaq_data['Close'], gold_data['Close']], axis=1)
                merged_data.columns = ['NAS100', 'XAU/USD']
                merged_data = merged_data.dropna()
                
                if len(merged_data) > 1:
                    correlation = merged_data.corr().iloc[0,1]
                    
                    st.markdown(f"""
                    <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px;">
                        <h4>📊 Correlación NAS100 vs XAU/USD</h4>
                        <p>Correlación en el periodo seleccionado: <strong>{correlation:.2f}</strong></p>
                        <p>
                            {'🔹 Correlación positiva: Ambos activos tienden a moverse en la misma dirección' if correlation > 0.3 else
                             '🔹 Correlación negativa: Los activos tienden a moverse en direcciones opuestas' if correlation < -0.3 else
                             '🔹 Correlación neutra: No hay relación clara entre los movimientos'}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No hay suficientes datos para realizar la comparación")
        else:
            st.info("Consulta primero los datos de mercado en la pestaña anterior")

    # Notas al pie
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #9E9E9E; font-size: 0.9rem;">
        <p>Datos de mercado proporcionados por Yahoo Finance. Actualizado: {}</p>
        <p>⚠️ Este dashboard es para fines educativos. No constituye asesoramiento financiero.</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
