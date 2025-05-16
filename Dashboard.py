import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import ta

# Configuración de la página
st.set_page_config(
    page_title="Dashboard Financiero Completo",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 20px;
        border-radius: 4px 4px 0 0;
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

# Función para obtener datos de mercado
@st.cache_data(ttl=60)
def get_market_data(symbol, period='1d', interval='15m'):
    try:
        data = yf.download(
            tickers=symbol,
            period=period,
            interval=interval,
            progress=False
        )
        return data
    except Exception as e:
        st.error(f"Error al obtener datos: {str(e)}")
        return pd.DataFrame()

# Función para calcular indicadores técnicos
def add_technical_indicators(df):
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

# Función para graficar datos de mercado
def plot_market_chart(df, title):
    if df.empty:
        st.warning("No hay datos disponibles")
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
        title=f'{title} - Análisis Técnico',
        xaxis_title='Fecha/Hora',
        yaxis_title='Precio',
        template='plotly_dark',
        height=600,
        xaxis_rangeslider_visible=False,
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Función para mostrar análisis técnico
def show_technical_analysis(df, asset_name):
    if df.empty:
        return
    
    last_data = df.iloc[-1]
    
    st.subheader(f"📊 Análisis Técnico: {asset_name}")
    
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

# Función principal
def main():
    st.title("📈 Dashboard Financiero Completo")
    
    # Configuración del sidebar
    with st.sidebar:
        st.header("⚙️ Configuración")
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
    
    # Pestañas principales
    tab1, tab2, tab3 = st.tabs(["NASDAQ 100", "Oro (XAU/USD)", "Comparativa"])
    
    with tab1:
        st.header("NASDAQ 100 (^NDX)")
        
        ndx_data = get_market_data("^NDX", period, timeframe)
        ndx_data = add_technical_indicators(ndx_data)
        
        plot_market_chart(ndx_data, "NASDAQ 100")
        show_technical_analysis(ndx_data, "NASDAQ 100")
    
    with tab2:
        st.header("Oro (XAU/USD)")
        
        gold_data = get_market_data("GC=F", period, timeframe)
        gold_data = add_technical_indicators(gold_data)
        
        plot_market_chart(gold_data, "XAU/USD")
        show_technical_analysis(gold_data, "XAU/USD")
    
    with tab3:
        st.header("Comparativa de Mercados")
        
        if 'ndx_data' in locals() and 'gold_data' in locals():
            if not ndx_data.empty and not gold_data.empty:
                # Normalización de precios
                norm_ndx = (ndx_data['Close'] / ndx_data['Close'].iloc[0]) * 100
                norm_gold = (gold_data['Close'] / gold_data['Close'].iloc[0]) * 100
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=norm_ndx.index,
                    y=norm_ndx,
                    name='NASDAQ 100',
                    line=dict(color='#2196F3', width=2)
                ))
                
                fig.add_trace(go.Scatter(
                    x=norm_gold.index,
                    y=norm_gold,
                    name='Oro (XAU/USD)',
                    line=dict(color='#FFC107', width=2)
                ))
                
                fig.update_layout(
                    title='Comparativa de Rendimiento Normalizado',
                    yaxis_title='Rendimiento (%)',
                    template='plotly_dark',
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Cálculo de correlación
                merged_data = pd.concat([ndx_data['Close'], gold_data['Close']], axis=1)
                merged_data.columns = ['NASDAQ', 'Oro']
                merged_data = merged_data.dropna()
                
                if len(merged_data) > 1:
                    correlation = merged_data.corr().iloc[0,1]
                    
                    st.markdown(f"""
                    <div style="background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin-top: 20px;">
                        <h4>📊 Correlación NASDAQ 100 vs Oro</h4>
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
            st.info("Por favor, consulte primero los datos en las pestañas individuales")

    # Pie de página
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #9E9E9E; font-size: 0.9rem;">
        <p>Datos proporcionados por Yahoo Finance. Actualizado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>⚠️ Este dashboard es para fines educativos. No constituye asesoramiento financiero.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
