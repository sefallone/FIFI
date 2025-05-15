import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime
import base64
from io import BytesIO

# Configuración inicial de la página
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
# FUNCIÓN DE FILTROS AVANZADOS - CORREGIDO
# =============================================

def advanced_filters(df):
    """Función con selector de fechas por mes y año"""
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
                    filtered_df = filtered_df[filtered_df['Ganancias/Pérdidas Brutas'] >= 0]
                elif profit_filter == "Solo pérdidas":
                    filtered_df = filtered_df[filtered_df['Ganancias/Pérdidas Brutas'] < 0]
            except Exception as e:
                st.warning(f"No se pudo aplicar el filtro de ganancias: {str(e)}")
    
    return filtered_df

# =============================================
# FUNCIÓN PARA MOSTRAR KPIs - CORREGIDO
# =============================================

def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False, delta=None):
    if pd.isna(value) or value is None:
        value_display = "N/D"
        delta_display = None
    else:
        try:
            if is_currency:
                value_display = f"${float(value):,.2f}"
            elif is_percentage:
                value_display = f"{float(value):.2f}%"
            else:
                value_display = f"{value:.2f}" if isinstance(value, (int, float)) else str(value)
        except (ValueError, TypeError):
            value_display = str(value)
        
        delta_display = delta
    
    # Estilos mejorados para tema oscuro
    bg_color = "#1024ca"
    text_color = "#ffffff"
    border_color = "#3f33ff"
    highlight_color = "#1024ca"
    
    if METRIC_CARDS_ENABLED:
        metric_card(
            title=f"{icon} {title}",
            value=value_display,
            delta=delta_display,
            key=f"card_{title.replace(' ', '_')}",
            background=bg_color,
            border_color=border_color,
            border_size_px=2
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
            background: {bg_color};
            color: {text_color};
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            margin-bottom: 20px;
            border-left: 4px solid {highlight_color};
        ">
            <div style="font-weight: 600; font-size: 14px; color: {highlight_color};">{icon} {title}</div>
            <div style="font-weight: 700; font-size: 24px; margin: 10px 0;">{value_display}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

# =============================================
# GRÁFICO DE PROYECCIÓN - VERSIÓN CORREGIDA
# =============================================

def plot_projection(df):
    """Gráficos de proyección a 3 años con explicaciones detalladas"""
    if len(df) > 1 and 'Ganancias/Pérdidas Brutas' in df.columns and 'Capital Invertido' in df.columns:
        # Preparar datos históricos
        historical_data = df[['Fecha', 'Capital Invertido', 'Ganancias/Pérdidas Brutas']].copy()
        historical_data['Tipo'] = 'Histórico'
        
        # Calcular métricas para proyección
        last_date = historical_data['Fecha'].max()
        last_capital = historical_data['Capital Invertido'].iloc[-1]
        last_profit = historical_data['Ganancias/Pérdidas Brutas'].iloc[-1]
        
        # Calcular crecimiento promedio mensual
        historical_data['Crecimiento Capital'] = historical_data['Capital Invertido'].pct_change()
        historical_data['Crecimiento Ganancias'] = historical_data['Ganancias/Pérdidas Brutas'].pct_change()
        
        avg_capital_growth = historical_data['Crecimiento Capital'].mean()
        avg_profit_growth = historical_data['Crecimiento Ganancias'].mean()
        
        # Si hay valores NaN o infinitos, usar valores conservadores
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
        
        # Escenario 2: Con inyección de capital de $5000 ahora y cada año
        scenario2 = pd.DataFrame({'Fecha': future_dates})
        capital = last_capital + 5000  # Inyección inicial
        scenario2['Capital Invertido'] = capital * (1 + avg_capital_growth) ** np.arange(1, 37)
        
        # Añadir inyecciones anuales (CORRECCIÓN: usar range(len(scenario2)) en lugar de enumerate
        for i in range(len(scenario2)):
            if i % 12 == 0 and i > 0:  # Cada 12 meses (1 año)
                scenario2.loc[i:, 'Capital Invertido'] += 5000
        
        scenario2['Ganancias/Pérdidas Brutas'] = last_profit * (1 + avg_profit_growth) ** np.arange(1, 37) * (scenario2['Capital Invertido'] / last_capital)
        scenario2['Tipo'] = 'Escenario 2: Con inyección de capital'
        
        # Combinar datos
        projection_data = pd.concat([historical_data, scenario1, scenario2])
        
        # Gráfico de proyección de capital con explicación
        st.markdown("### Proyección de Capital Invertido")
        
        explanation = """
        **Cómo interpretar este gráfico:**
        - **Línea histórica (azul):** Muestra la evolución real de tu capital hasta la fecha actual
        - **Escenario 1 (verde):** Proyección si NO realizas nuevas inyecciones de capital
        - **Escenario 2 (naranja):** Proyección si inyectas $5,000 ahora y $5,000 adicionales cada año
        - El eje Y muestra el monto proyectado en dólares
        - El eje X muestra la línea de tiempo mes a mes
        """
        st.markdown(explanation)
        
        fig_cap = px.line(
            projection_data,
            x='Fecha',
            y='Capital Invertido',
            color='Tipo',
            title='Proyección de Capital Invertido (3 años)',
            labels={'Capital Invertido': 'Monto ($)', 'Fecha': 'Fecha'},
            template="plotly_dark",
            color_discrete_map={
                'Histórico': '#1f77b4',
                'Escenario 1: Sin nueva inyección': '#2ca02c',
                'Escenario 2: Con inyección de capital': '#ff7f0e'
            }
        )
        fig_cap.update_layout(
            height=500,
            annotations=[
                dict(
                    x=0.5,
                    y=-0.2,
                    xref='paper',
                    yref='paper',
                    text="Nota: Las proyecciones se basan en el crecimiento histórico promedio",
                    showarrow=False,
                    font=dict(size=10))
            ]
        )
        st.plotly_chart(fig_cap, use_container_width=True)
        
        # Gráfico de proyección de ganancias con explicación
        st.markdown("### Proyección de Ganancias Brutas")
        
        explanation = """
        **Cómo interpretar este gráfico:**
        - **Línea histórica (azul):** Muestra tus ganancias reales hasta la fecha actual
        - **Escenario 1 (verde):** Ganancias proyectadas sin nuevas inyecciones de capital
        - **Escenario 2 (naranja):** Ganancias proyectadas CON inyecciones de capital
        - Las ganancias crecen proporcionalmente al capital invertido
        - El eje Y muestra el monto de ganancias en dólares por mes
        - El eje X muestra la línea de tiempo mes a mes
        """
        st.markdown(explanation)
        
        fig_profit = px.line(
            projection_data,
            x='Fecha',
            y='Ganancias/Pérdidas Brutas',
            color='Tipo',
            title='Proyección de Ganancias Brutas (3 años)',
            labels={'Ganancias/Pérdidas Brutas': 'Monto ($)', 'Fecha': 'Fecha'},
            template="plotly_dark",
            color_discrete_map={
                'Histórico': '#1f77b4',
                'Escenario 1: Sin nueva inyección': '#2ca02c',
                'Escenario 2: Con inyección de capital': '#ff7f0e'
            }
        )
        fig_profit.update_layout(
            height=500,
            annotations=[
                dict(
                    x=0.5,
                    y=-0.2,
                    xref='paper',
                    yref='paper',
                    text="Nota: Las ganancias proyectadas asumen el mismo rendimiento porcentual histórico",
                    showarrow=False,
                    font=dict(size=10))
            ]
        )
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
        
        **Limitaciones:**
        - No considera cambios en las condiciones del mercado
        - Asume rendimientos consistentes
        - No incluye impuestos ni inflación
        """.format(avg_capital_growth, avg_profit_growth))
    else:
        st.warning("No hay suficientes datos históricos para generar proyecciones")

# =============================================
# INTERFAZ PRINCIPAL - CORREGIDA
# =============================================

def main():
    st.title("📊 Fondo de Inversión Fallone Investment")
    
    # Aplicar tema oscuro global
    st.markdown("""
    <style>
        .stApp {
            background-color: #121212;
            color: #ffffff;
        }
        .stSidebar {
            background-color: #1e1e1e !important;
            color: #ffffff;
        }
        .css-1aumxhk {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        .st-b7 {
            color: #ffffff;
        }
        .stTextInput, .stTextArea, .stSelectbox, .stSlider, .stDateInput {
            background-color: #2d2d2d;
            color: #ffffff;
        }
        .st-bb {
            background-color: transparent;
        }
        .st-cb {
            background-color: #2d2d2d;
        }
        .stButton>button {
            background-color: #3f33ff;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
        }
        .stButton>button:hover {
            background-color: #4d42ff;
        }
    </style>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("📤 Subir archivo Excel", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            selected_sheet = st.selectbox("📋 Seleccionar hoja de trabajo", sheet_names)
            
            @st.cache_data
            def load_data():
                return pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            
            df = load_data()
            
            # Verificar si el DataFrame está vacío
            if df.empty:
                st.warning("El archivo no contiene datos")
                return
                
            df = df.loc[:, ~df.columns.duplicated()]
            
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
            
            # Verificar que haya suficientes filas antes de acceder a índices
            if len(df) > 1:
                capital_inicial = df['Aumento Capital'].iloc[1] if 'Aumento Capital' in df.columns else 0
                id_inversionista = df['ID Inv'].iloc[1] if 'ID Inv' in df.columns else "N/D"
                fecha_entrada = df['Fecha'].iloc[1] if 'Fecha' in df.columns else "N/D"
            else:
                capital_inicial = 0
                id_inversionista = "N/D"
                fecha_entrada = "N/D"
            
            if isinstance(fecha_entrada, pd.Timestamp):
                fecha_entrada = fecha_entrada.strftime('%d/%m/%Y')
            
            filtered_df = advanced_filters(df)
            
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
            st.markdown('<h2 style="color: #1024ca; border-bottom: 2px solid #1024ca; padding-bottom: 10px;">📊 KPIs Financieros</h2>', unsafe_allow_html=True)
            
            # Calcular métricas avanzadas con verificaciones
            current_capital = filtered_df['Capital Invertido'].iloc[-1] if len(filtered_df) > 0 and 'Capital Invertido' in filtered_df.columns else 0
            delta_capital = current_capital - capital_inicial if len(filtered_df) > 0 else 0
            
            total_aumentos = filtered_df['Aumento Capital'].sum() if 'Aumento Capital' in filtered_df.columns else None
            ganancias_brutas = filtered_df['Ganancias/Pérdidas Brutas'].sum() if 'Ganancias/Pérdidas Brutas' in filtered_df.columns else None
            ganancias_netas = filtered_df['Ganancias/Pérdidas Netas'].sum() if 'Ganancias/Pérdidas Netas' in filtered_df.columns else None
            comisiones = filtered_df['Comisiones Pagadas'].sum() if 'Comisiones Pagadas' in filtered_df.columns else None
            retiros = filtered_df['Retiro de Fondos'].sum() if 'Retiro de Fondos' in filtered_df.columns else None
            
            roi = calculate_roi(filtered_df, capital_inicial)
            cagr = calculate_cagr(filtered_df, capital_inicial, current_capital)
            sharpe_ratio = calculate_sharpe_ratio(filtered_df)
            max_drawdown = calculate_max_drawdown(filtered_df)
            
            # [Resto del código de la función main() permanece igual...]

if __name__ == "__main__":
    main()
