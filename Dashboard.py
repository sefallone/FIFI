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
# FUNCIÓN DE FILTROS AVANZADOS
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
# FUNCIÓN PARA MOSTRAR KPIs CON TOOLTIPS
# =============================================

def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False, delta=None):
    """
    Muestra un KPI con tooltip explicativo al pasar el mouse.
    
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
    explanation = kpi_explanations.get(title, "Métrica financiera clave.")
    
    if METRIC_CARDS_ENABLED:
        metric_card(
            title=f"{icon} {title}",
            value=value_display,
            delta=delta_display,
            key=f"card_{title.replace(' ', '_')}",
            background="#4834c8",
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
            background: #4834c8;
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

# =============================================
# GRÁFICOS MEJORADOS
# =============================================

def plot_combined_capital_withdrawals(df, capital_inicial):
    """Muestra la evolución del capital invertido junto con retiros de dinero"""
    if 'Capital Invertido' not in df.columns or 'Retiro de Fondos' not in df.columns:
        st.warning("No se pueden generar el gráfico combinado. Faltan columnas necesarias.")
        return
    
    fig = px.line(
        df,
        x='Fecha',
        y='Capital Invertido',
        title='<b>Evolución del Capital vs Retiros</b><br><sup>Línea: Capital Invertido | Barras: Retiros</sup>',
        labels={'Capital Invertido': 'Monto ($)', 'Fecha': 'Fecha'},
        template="plotly_dark"
    )
    
    # Añadir retiros como barras
    fig.add_bar(
        x=df['Fecha'],
        y=df['Retiro de Fondos'],
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
        annotation_position="bottom right"
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
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_capital_profit_relation(df):
    """Muestra la relación porcentual entre capital invertido y ganancias brutas"""
    if 'Capital Invertido' not in df.columns or 'Ganancias/Pérdidas Brutas' not in df.columns:
        st.warning("No se pueden calcular las métricas de relación. Faltan columnas necesarias.")
        return
    
    df['Porcentaje_Ganancias'] = (df['Ganancias/Pérdidas Brutas'] / df['Capital Invertido']) * 100
    
    fig = px.bar(
        df,
        x='Fecha',
        y='Porcentaje_Ganancias',
        title='Relación Porcentual: Ganancias Brutas / Capital Invertido',
        labels={'Porcentaje_Ganancias': 'Porcentaje de Ganancias (%)', 'Fecha': 'Fecha'},
        color='Porcentaje_Ganancias',
        color_continuous_scale=px.colors.diverging.RdYlGn,
        template="plotly_dark"
    )
    
    fig.add_hline(y=0, line_dash="dash", line_color="white")
    fig.update_layout(height=400, yaxis_title="Porcentaje de Ganancias (%)")
    st.plotly_chart(fig, use_container_width=True)

def plot_bubble_chart(df):
    """Gráfico de burbujas para relación capital-ganancias"""
    if all(col in df.columns for col in ['Capital Invertido', 'Ganancias/Pérdidas Brutas', 'Fecha']):
        fig = px.scatter(
            df,
            x='Fecha',
            y='Ganancias/Pérdidas Brutas',
            size='Capital Invertido',
            color='Ganancias/Pérdidas Brutas',
            title='Relación Capital vs Ganancias',
            color_continuous_scale=px.colors.diverging.RdYlGn,
            template="plotly_dark",
            hover_data=['Capital Invertido']
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

def plot_waterfall(df):
    """Gráfico de cascada para flujo de capital"""
    if all(col in df.columns for col in ['Aumento Capital', 'Retiro de Fondos', 'Ganancias/Pérdidas Netas']):
        # Crear datos para el gráfico de cascada
        changes = []
        running_total = 0
        
        for _, row in df.iterrows():
            change = row['Ganancias/Pérdidas Netas']
            changes.append({
                'Fecha': row['Fecha'],
                'Cambio': change,
                'Total Acumulado': running_total + change
            })
            running_total += change
        
        waterfall_df = pd.DataFrame(changes)
        
        fig = px.bar(
            waterfall_df,
            x='Fecha',
            y='Cambio',
            title='Flujo de Ganancias/Pérdidas Netas',
            template="plotly_dark"
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

def plot_correlation_heatmap(df):
    """Mapa de calor de correlaciones mejorado con análisis"""
    st.markdown("""
    <style>
        .correlation-analysis {
            background-color: #1e1e1e;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        }
        .correlation-highlight {
            background-color: #1e3e1e;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .negative-correlation {
            background-color: #3e1e1e;
        }
    </style>
    """, unsafe_allow_html=True)
    
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    
    if len(numeric_cols) > 1:
        st.markdown("### 🔥 Mapa de Correlación entre Variables")
        
        # Calcular matriz de correlación
        corr_matrix = df[numeric_cols].corr()
        
        # Crear figura más grande con diseño mejorado
        fig = px.imshow(
            corr_matrix,
            text_auto=".2f",
            color_continuous_scale=px.colors.diverging.RdYlGn,
            title='<b>Correlación entre Variables Financieras</b>',
            template="plotly_dark",
            width=800,
            height=650,
            aspect="auto",
            zmin=-1,
            zmax=1
        )
        
        # Configuración avanzada del layout
        fig.update_layout(
            margin=dict(l=50, r=50, t=100, b=50),
            title_font=dict(size=24, family="Arial, sans-serif"),
            xaxis=dict(
                title="Variables",
                tickangle=45,
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                title="Variables",
                tickfont=dict(size=12)
            ),
            coloraxis_colorbar=dict(
                title="Nivel de Correlación",
                thickness=20,
                len=0.75,
                tickvals=[-1, -0.5, 0, 0.5, 1],
                ticktext=["-1 (Negativa)", "-0.5", "0 (No correlación)", "0.5", "1 (Positiva)"]
            )
        )
        
        # Mostrar el gráfico
        st.plotly_chart(fig, use_container_width=True)
        
        # Análisis de correlaciones
        st.markdown("""
        <div class="correlation-analysis">
            <h4 style="color: #42e8ff; margin-bottom: 15px;">📊 Análisis de Correlaciones</h4>
            <div style="text-align: justify; margin-bottom: 15px;">
                <p>Este mapa de calor muestra las relaciones estadísticas entre las diferentes variables financieras. 
                Los valores oscilan entre <strong>-1</strong> (correlación negativa perfecta) y <strong>+1</strong> (correlación positiva perfecta), 
                donde <strong>0</strong> indica ausencia de relación lineal.</p>
                
                <p style="margin-top: 10px;"><strong>Interpretación clave:</strong> Las correlaciones significativas pueden revelar relaciones importantes como:
                cómo los cambios en el capital invertido afectan las ganancias, o si existe relación entre retiros y comisiones.
                Sin embargo, <em style="color: #FF6B6B;">correlación no implica causalidad</em> - siempre investigue las relaciones subyacentes.</p>
            </div>
            
            <div style="display: flex; gap: 15px; margin-bottom: 15px;">
                <div style="flex: 1; background-color: #1e3e1e; padding: 10px; border-radius: 5px;">
                    <h5 style="margin-top: 0; color: #4CAF50;">📈 Correlación Positiva</h5>
                    <p>Valores cercanos a 1 indican que cuando una variable aumenta, la otra también tiende a aumentar.</p>
                </div>
                <div style="flex: 1; background-color: #3e1e1e; padding: 10px; border-radius: 5px;">
                    <h5 style="margin-top: 0; color: #F44336;">📉 Correlación Negativa</h5>
                    <p>Valores cercanos a -1 indican que cuando una variable aumenta, la otra tiende a disminuir.</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Análisis específico de las correlaciones más fuertes
        corr_values = corr_matrix.unstack().sort_values(ascending=False)
        corr_values = corr_values[corr_values != 1]  # Eliminar autocorrelaciones
        
        if not corr_values.empty:
            st.markdown("""
            <div class="correlation-analysis">
                <h4 style="color: #42e8ff; margin-bottom: 15px;">🔍 Correlaciones Destacadas</h4>
            """, unsafe_allow_html=True)
            
            top_positive = corr_values.head(3)
            top_negative = corr_values.tail(3)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="correlation-highlight">
                    <h5 style="margin-top: 0; color: #4CAF50;">📈 Mayores Correlaciones Positivas</h5>
                """, unsafe_allow_html=True)
                for pair, value in top_positive.items():
                    st.markdown(f"""
                    <div style="margin: 8px 0; padding: 8px; background-color: rgba(76, 175, 80, 0.2); border-radius: 4px;">
                        <strong>{pair[0]}</strong> ↔ <strong>{pair[1]}</strong>: 
                        <span style="font-weight: bold; color: {'#4CAF50' if value > 0 else '#F44336'}">{value:.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="correlation-highlight negative-correlation">
                    <h5 style="margin-top: 0; color: #F44336;">📉 Mayores Correlaciones Negativas</h5>
                """, unsafe_allow_html=True)
                for pair, value in top_negative.items():
                    st.markdown(f"""
                    <div style="margin: 8px 0; padding: 8px; background-color: rgba(244, 67, 54, 0.2); border-radius: 4px;">
                        <strong>{pair[0]}</strong> ↔ <strong>{pair[1]}</strong>: 
                        <span style="font-weight: bold; color: {'#4CAF50' if value > 0 else '#F44336'}">{value:.2f}</span>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("No hay suficientes variables numéricas para calcular correlaciones")

def plot_projection(df):
    """Gráficos de proyección a 3 años - Versión Mejorada"""
    if len(df) > 1 and 'Ganancias/Pérdidas Brutas' in df.columns and 'Capital Invertido' in df.columns:
        # Configuración de parámetros en el sidebar
        with st.sidebar.expander("⚙️ Configuración de Proyección"):
            monthly_growth = st.slider(
                "Crecimiento mensual del capital (%)",
                min_value=0.1,
                max_value=10.0,
                value=2.0,
                step=0.1,
                help="Tasa de crecimiento mensual porcentual del capital"
            ) / 100
            
            initial_injection = st.number_input(
                "Inyección inicial de capital ($)",
                min_value=0,
                value=5000,
                step=1000
            )
            
            annual_injection = st.number_input(
                "Inyección anual de capital ($)",
                min_value=0,
                value=5000,
                step=1000
            )
        
        # Preparar datos históricos
        historical_data = df[['Fecha', 'Capital Invertido', 'Ganancias/Pérdidas Brutas']].copy()
        historical_data['Tipo'] = 'Histórico'
        
        # Calcular métricas para proyección
        last_date = historical_data['Fecha'].max()
        last_capital = historical_data['Capital Invertido'].iloc[-1]
        last_profit = historical_data['Ganancias/Pérdidas Brutas'].iloc[-1]
        
        # Calcular ratio ganancias/capital histórico
        historical_data['Profit_Ratio'] = historical_data['Ganancias/Pérdidas Brutas'] / historical_data['Capital Invertido']
        avg_profit_ratio = historical_data['Profit_Ratio'].mean()
        
        # Si no hay ratio válido, usar valor conservador (2%)
        if pd.isna(avg_profit_ratio) or not np.isfinite(avg_profit_ratio):
            avg_profit_ratio = 0.02
        
        # Crear fechas futuras (36 meses)
        future_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=36,
            freq='M'
        )
        
        # Escenario 1: Sin nueva inyección de capital
        scenario1 = pd.DataFrame({'Fecha': future_dates})
        scenario1['Capital Invertido'] = last_capital * (1 + monthly_growth) ** np.arange(1, 37)
        scenario1['Ganancias/Pérdidas Brutas'] = scenario1['Capital Invertido'] * avg_profit_ratio
        scenario1['Tipo'] = 'Escenario 1: Sin nueva inyección'
        
        # Escenario 2: Con inyección de capital
        scenario2 = pd.DataFrame({'Fecha': future_dates})
        capital = last_capital + initial_injection  # Inyección inicial
        scenario2_capital = [capital]
        
        for i in range(1, 36):
            new_capital = scenario2_capital[-1] * (1 + monthly_growth)
            if i % 12 == 0:  # Cada 12 meses (1 año)
                new_capital += annual_injection  # Inyección anual
            scenario2_capital.append(new_capital)
        
        scenario2['Capital Invertido'] = scenario2_capital
        scenario2['Ganancias/Pérdidas Brutas'] = scenario2['Capital Invertido'] * avg_profit_ratio
        scenario2['Tipo'] = 'Escenario 2: Con inyección de capital'
        
        # Combinar datos
        projection_data = pd.concat([historical_data, scenario1, scenario2])
        
        # Gráfico de proyección de capital
        st.markdown("### Proyección de Capital Invertido (3 años)")
        fig_cap = px.line(
            projection_data,
            x='Fecha',
            y='Capital Invertido',
            color='Tipo',
            title=f'<b>Proyección de Capital Invertido (3 años)</b><br><sup>Tasa de crecimiento: {monthly_growth*100:.1f}% mensual</sup>',
            labels={'Capital Invertido': 'Monto ($)', 'Fecha': 'Fecha'},
            template="plotly_dark",
            line_shape='linear'
        )
        
        # Añadir línea vertical para separar histórico de proyección
        fig_cap.add_vline(
            x=last_date,
            line_dash="dash",
            line_color="yellow",
            annotation_text="Inicio Proyección",
            annotation_position="top left"
        )
        
        fig_cap.update_layout(
            height=500,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        st.plotly_chart(fig_cap, use_container_width=True)
        
        # Gráfico de proyección de ganancias
        st.markdown("### Proyección de Ganancias Brutas (3 años)")
        fig_profit = px.line(
            projection_data,
            x='Fecha',
            y='Ganancias/Pérdidas Brutas',
            color='Tipo',
            title=f'<b>Proyección de Ganancias Brutas (3 años)</b><br><sup>Ratio ganancias/capital: {avg_profit_ratio*100:.1f}%</sup>',
            labels={'Ganancias/Pérdidas Brutas': 'Monto ($)', 'Fecha': 'Fecha'},
            template="plotly_dark",
            line_shape='linear'
        )
        
        # Añadir línea vertical para separar histórico de proyección
        fig_profit.add_vline(
            x=last_date,
            line_dash="dash",
            line_color="yellow",
            annotation_text="Inicio Proyección",
            annotation_position="top left"
        )
        
        fig_profit.update_layout(
            height=500,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        st.plotly_chart(fig_profit, use_container_width=True)
        
        # Mostrar métricas clave de proyección
        st.markdown("### 📌 Resumen de Proyección")
        cols = st.columns(3)
        
        with cols[0]:
            st.metric(
                "Capital Final - Escenario 1",
                f"${scenario1['Capital Invertido'].iloc[-1]:,.2f}",
                delta=f"{(scenario1['Capital Invertido'].iloc[-1]/last_capital-1)*100:.1f}% vs actual"
            )
        
        with cols[1]:
            st.metric(
                "Ganancias Acumuladas - Escenario 1",
                f"${scenario1['Ganancias/Pérdidas Brutas'].sum():,.2f}",
                delta=f"Ratio: {avg_profit_ratio*100:.1f}%"
            )
        
        with cols[2]:
            st.metric(
                "ROI Proyectado - Escenario 1",
                f"{(scenario1['Ganancias/Pérdidas Brutas'].sum()/last_capital)*100:.1f}%",
                delta=f"vs histórico: {historical_data['Ganancias/Pérdidas Brutas'].sum()/historical_data['Capital Invertido'].iloc[0]*100:.1f}%"
            )
        
        # Explicación de supuestos
        st.markdown("---")
        st.markdown(f"""
        **📝 Supuestos de la proyección:**
        - Se asume un **crecimiento mensual del capital del {monthly_growth*100:.1f}%** (compuesto)
        - Las **ganancias brutas** se calculan como **{avg_profit_ratio*100:.1f}% del capital invertido** (ratio histórico promedio)
        - Escenario 2 incluye:
          - Inyección inicial de **${initial_injection:,.0f}**
          - **${annual_injection:,.0f} adicionales** cada 12 meses
        - Las proyecciones son **estimativas** y no garantizan resultados futuros
        """)
    else:
        st.warning("⚠️ No hay suficientes datos históricos para generar proyecciones")

# =============================================
# FUNCIONES DE ANÁLISIS
# =============================================

def calculate_roi(df, capital_inicial):
    """Calcula el ROI basado en ganancias netas"""
    if 'Ganancias/Pérdidas Netas' in df.columns and capital_inicial and float(current_capital) != 0:
        ganancias_netas = df['Ganancias/Pérdidas Netas'].sum()
        return (float(ganancias_netas) / float(current_capital)) * 100
    return 0

def calculate_cagr(df, capital_inicial, current_capital):
    """Calcula la tasa de crecimiento anual compuesta"""
    if len(df) > 1 and capital_inicial and float(current_capital) != 0:
        start_date = df['Fecha'].iloc[0]
        end_date = df['Fecha'].iloc[-1]
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if months <= 0:
            months = 1
        return ((float(current_capital) / float(capital_inicial)) ** (12/months) - 1) * 100
    return 0

def calculate_sharpe_ratio(df):
    """Calcula el ratio Sharpe simplificado"""
    if 'Ganancias/Pérdidas Netas' in df.columns:
        returns = df['Ganancias/Pérdidas Netas'].pct_change().dropna()
        if len(returns) > 0:
            return (returns.mean() / returns.std()) * (np.sqrt(12))
    return 0

def calculate_max_drawdown(df):
    """Calcula el drawdown máximo"""
    if 'Capital Invertido' in df.columns:
        df['Capital Acumulado'] = df['Capital Invertido'].cummax()
        df['Drawdown'] = (df['Capital Invertido'] - df['Capital Acumulado']) / df['Capital Acumulado']
        return df['Drawdown'].min() * 100 if len(df) > 0 else 0
    return 0

# =============================================
# INTERFAZ PRINCIPAL (CON CARGA EN SIDEBAR)
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
            background-color: #42e8ff;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # =============================================
    # SECCIÓN DE CARGA DE ARCHIVOS EN SIDEBAR
    # =============================================
    with st.sidebar:
        st.header("📤 Carga de Datos")
        uploaded_file = st.file_uploader("Subir archivo Excel", type=['xlsx', 'xls'], help="Suba un archivo Excel con los datos de inversión")
        
        if uploaded_file is None:
            st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")
            st.stop()
        
        try:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            selected_sheet = st.selectbox("Seleccionar hoja de trabajo", sheet_names)
            
            @st.cache_data
            def load_data(file, sheet):
                return pd.read_excel(file, sheet_name=sheet)

            df = load_data(uploaded_file, selected_sheet)
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
            
            capital_inicial = df['Aumento Capital'].iloc[1] if len(df) > 1 else 0
            id_inversionista = df['ID Inv'].iloc[1] if len(df) > 1 else "N/D"
            
            fecha_entrada = df['Fecha'].iloc[1] if len(df) > 1 else "N/D"
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
        except Exception as e:
            st.error(f"🚨 Error crítico al procesar el archivo: {str(e)}")
            st.stop()
    
    # =============================================
    # SECCIÓN PRINCIPAL DEL DASHBOARD
    # =============================================
    
    # SECCIÓN DE KPIs
    st.markdown("---")
    st.markdown('<h2 style="color: #105cca; border-bottom: 2px solid #8f10ca; padding-bottom: 10px;">📊 KPIs Financieros</h2>', unsafe_allow_html=True)
    
    # Calcular métricas avanzadas
    current_capital = filtered_df['Capital Invertido'].iloc[-1] if len(filtered_df) > 0 else 0
    total_aumentos = filtered_df['Aumento Capital'].sum()
    delta_capital = current_capital - total_aumentos if len(filtered_df) > 0 else 0
    ganancias_brutas = filtered_df['Ganancias/Pérdidas Brutas'].sum() if 'Ganancias/Pérdidas Brutas' in filtered_df.columns else None
    ganancias_netas = filtered_df['Ganancias/Pérdidas Netas'].sum() if 'Ganancias/Pérdidas Netas' in filtered_df.columns else None
    comisiones = filtered_df['Comisiones Pagadas'].sum() if 'Comisiones Pagadas' in filtered_df.columns else None
    retiros = filtered_df['Retiro de Fondos'].sum() if 'Retiro de Fondos' in filtered_df.columns else None
    
    roi = calculate_roi(filtered_df, capital_inicial)
    cagr = calculate_cagr(filtered_df, capital_inicial, current_capital)
    sharpe_ratio = calculate_sharpe_ratio(filtered_df)
    max_drawdown = calculate_max_drawdown(filtered_df)
    
    # Primera fila de KPIs
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        display_kpi("ID Inversionista", id_inversionista, "🆔", is_currency=False)
    with col2:
        display_kpi("Fecha de Entrada al Fondo", fecha_entrada, "📅", is_currency=False)
    with col3:
        display_kpi("Capital Inicial", capital_inicial, "🏁")
    with col4:
        display_kpi("Capital Actual", current_capital, "🏦", delta=f"{delta_capital:+,.2f}")
    
    # Segunda fila de KPIs
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        display_kpi("Total Inyección de Capital", total_aumentos, "📈")
    with col6:
        display_kpi("Ganancias Brutas", ganancias_brutas, "💵")
    with col7:
        display_kpi("Ganancias Netas", ganancias_netas, "💰")
    with col8:
        display_kpi("Comisiones Pagadas", comisiones, "💸")
    
    # Tercera fila de KPIs
    col9, col10, col11, col12 = st.columns(4)
    with col9:
        display_kpi("Retiro de Dinero", retiros, "↘️")
    with col10:
        display_kpi("ROI", roi, "📊", is_percentage=True)
    with col11:
        display_kpi("CAGR Mensual", cagr, "🚀", is_percentage=True)
    with col12:
        display_kpi("Drawdown Máximo", max_drawdown, "📉", is_percentage=True)
    
    # Cuarta fila de KPIs
    col13, col14, col15, col16 = st.columns(4)
    with col13:
        display_kpi("Ratio Sharpe", sharpe_ratio, "⚖️", is_percentage=False)
    
    # SECCIÓN DE GRÁFICOS PRINCIPALES
    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Visualizaciones Principales", "📊 Análisis Avanzado", "🔍 Detalle de Datos", "🔮 Proyección Futura"])
    
    with tab1:
        # Gráfico combinado de capital y retiros
        if all(col in filtered_df.columns for col in ['Fecha', 'Capital Invertido', 'Retiro de Fondos']):
            try:
                plot_combined_capital_withdrawals(filtered_df, capital_inicial)
            except Exception as e:
                st.error(f"Error al generar gráfico combinado: {str(e)}")
        else:
            st.warning("Se requieren las columnas: Fecha, Capital Invertido y Retiro de Fondos")
        
        # Gráfico de relación porcentual capital-ganancias
        if 'Capital Invertido' in filtered_df.columns and 'Ganancias/Pérdidas Brutas' in filtered_df.columns:
            plot_capital_profit_relation(filtered_df)
        
        # Gráfico de ganancias/pérdidas
        if 'Ganancias/Pérdidas Brutas' in filtered_df.columns and 'Fecha' in filtered_df.columns:
            try:
                fig3 = px.bar(
                    filtered_df,
                    x='Fecha',
                    y='Ganancias/Pérdidas Brutas',
                    title='Ganancias/Pérdidas Brutas por Periodo',
                    color='Ganancias/Pérdidas Brutas',
                    color_continuous_scale=px.colors.diverging.RdYlGn,
                    labels={'Ganancias/Pérdidas Brutas': 'Monto ($)', 'Fecha': 'Fecha'},
                    template="plotly_dark"
                )
                fig3.update_layout(height=400)
                st.plotly_chart(fig3, use_container_width=True)
            except Exception as e:
                st.error(f"Error al generar gráfico de ganancias: {str(e)}")
        
        # Gráfico de comisiones acumuladas
        if 'Comisiones Pagadas' in filtered_df.columns and 'Fecha' in filtered_df.columns:
            try:
                filtered_df['Comisiones Acumuladas'] = filtered_df['Comisiones Pagadas'].cumsum()
                fig4 = px.area(
                    filtered_df,
                    x='Fecha',
                    y='Comisiones Acumuladas',
                    title='Comisiones Pagadas Acumuladas',
                    labels={'Comisiones Acumuladas': 'Monto ($)', 'Fecha': 'Fecha'},
                    template="plotly_dark"
                )
                fig4.update_layout(height=400)
                st.plotly_chart(fig4, use_container_width=True)
            except Exception as e:
                st.error(f"Error al generar gráfico de comisiones: {str(e)}")
    
    with tab2:
        st.markdown("### Análisis Avanzado de Rendimiento")
        
        # Gráfico de burbujas
        plot_bubble_chart(filtered_df)
        
        # Gráfico de cascada
        plot_waterfall(filtered_df)
        
        # Mapa de calor de correlaciones
        plot_correlation_heatmap(filtered_df)
        
        # Análisis de drawdown
        if 'Capital Invertido' in filtered_df.columns:
            filtered_df['Capital Acumulado'] = filtered_df['Capital Invertido'].cummax()
            filtered_df['Drawdown'] = (filtered_df['Capital Invertido'] - filtered_df['Capital Acumulado']) / filtered_df['Capital Acumulado']
            
            fig_drawdown = px.area(
                filtered_df,
                x='Fecha',
                y='Drawdown',
                title='Evolución del Drawdown',
                labels={'Drawdown': 'Drawdown (%)', 'Fecha': 'Fecha'},
                template="plotly_dark"
            )
            fig_drawdown.update_yaxes(tickformat=".0%")
            fig_drawdown.update_layout(height=400)
            st.plotly_chart(fig_drawdown, use_container_width=True)
    
    with tab3:
        st.markdown("### Datos Filtrados")
        st.dataframe(filtered_df.style.format({
            'Capital Invertido': '${:,.2f}',
            'Ganancias/Pérdidas Brutas': '${:,.2f}',
            'Ganancias/Pérdidas Netas': '${:,.2f}',
            'Comisiones Pagadas': '${:,.2f}',
            'Retiro de Fondos': '${:,.2f}'
        }), use_container_width=True)
        
        # SECCIÓN DE EXPORTACIÓN DE DATOS
        st.markdown("---")
        st.markdown('<h3 style="color: #3f33ff;">Exportar Datos</h3>', unsafe_allow_html=True)
        
        if st.button("📄 Exportar Datos Filtrados a CSV"):
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar CSV",
                data=csv,
                file_name="datos_filtrados_fallone.csv",
                mime="text/csv"
            )
    
    with tab4:
        plot_projection(filtered_df)

if __name__ == "__main__":
    main()
