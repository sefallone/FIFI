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

# =============================================
# GRÁFICOS MEJORADOS
# =============================================

def plot_combined_capital_withdrawals(df, capital_inicial):
    """Muestra la evolución del capital invertido junto con retiros de dinero"""
    if 'Capital Invertido' not in df.columns or 'Retiro de Fondos' not in df.columns:
        st.warning("No se pueden generar el gráfico combinado. Faltan columnas necesarias.")
        return
    
    df['Fecha'] = pd.to_datetime(df['Fecha'])
    
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
    
    df['Fecha'] = pd.to_datetime(df['Fecha'])
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
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
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
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        
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
    """Gráficos de proyección a 3 años con 3 escenarios personalizados"""
    if len(df) > 1 and 'Ganancias/Pérdidas Netas' in df.columns and 'Capital Invertido' in df.columns:
        # Configuración de parámetros en el sidebar
        with st.sidebar.expander("⚙️ Configuración de Proyección"):
            st.markdown("**Parámetros generales**")
            tasa_crecimiento = st.slider(
                "Tasa de crecimiento mensual promedio (%)",
                min_value=0.1,
                max_value=20.0,
                value=5.0,
                step=0.1,
                help="Tasa de crecimiento mensual porcentual esperada"
            ) / 100
            
            st.markdown("**Escenario 3: Inyección anual**")
            porcentaje_inyeccion = st.slider(
                "Porcentaje de inyección anual",
                min_value=1,
                max_value=50,
                value=10,
                step=1,
                help="Porcentaje del capital actual que se inyecta cada año"
            ) / 100
        
        # Preparar datos históricos
        historical_data = df[['Fecha', 'Capital Invertido', 'Ganancias/Pérdidas Netas']].copy()
        historical_data['Tipo'] = 'Histórico'
        historical_data['Escenario'] = 'Histórico'
        
        # Convertir fechas a datetime si no lo están
        historical_data['Fecha'] = pd.to_datetime(historical_data['Fecha'])
        
        # Obtener último mes histórico
        last_date = historical_data['Fecha'].max()
        last_capital = historical_data['Capital Invertido'].iloc[-1]
        last_profit = historical_data['Ganancias/Pérdidas Netas'].iloc[-1]
        
        # Crear fechas futuras (36 meses)
        future_dates = pd.date_range(
            start=last_date + pd.DateOffset(months=1),
            periods=36,
            freq='M'
        )
        
        # ----------------------------------------------------------------------
        # ESCENARIO 1: Retiro de ganancias netas cada 4 meses
        # ----------------------------------------------------------------------
        escenario1 = pd.DataFrame({'Fecha': future_dates})
        escenario1['Capital Invertido'] = last_capital
        escenario1['Ganancias Netas'] = 0
        escenario1['Retiros'] = 0
        escenario1['Tipo'] = 'Escenario 1'
        escenario1['Descripción'] = 'Retiro ganancias cada 4 meses'
        
        for i in range(36):
            # Calcular ganancias del mes
            ganancias_mes = escenario1.at[i, 'Capital Invertido'] * tasa_crecimiento
            escenario1.at[i, 'Ganancias Netas'] = ganancias_mes
            
            # Cada 4 meses retirar las ganancias acumuladas de los últimos 4 meses
            if (i + 1) % 4 == 0:
                ganancias_acumuladas = escenario1.loc[i-3:i, 'Ganancias Netas'].sum()
                escenario1.at[i, 'Retiros'] = ganancias_acumuladas
                escenario1.at[i, 'Ganancias Netas'] = 0  # Se retiran todas
            
            # Mantener el capital constante (solo crece por la tasa mes a mes)
            if i < 35:
                escenario1.at[i+1, 'Capital Invertido'] = escenario1.at[i, 'Capital Invertido']
        
        # ----------------------------------------------------------------------
        # ESCENARIO 2: Interés compuesto (ganancias se reinvierten)
        # ----------------------------------------------------------------------
        escenario2 = pd.DataFrame({'Fecha': future_dates})
        escenario2['Capital Invertido'] = last_capital
        escenario2['Tipo'] = 'Escenario 2'
        escenario2['Descripción'] = 'Interés compuesto mensual'
        
        for i in range(1, 36):
            # Cada mes el capital crece con las ganancias
            escenario2.at[i, 'Capital Invertido'] = escenario2.at[i-1, 'Capital Invertido'] * (1 + tasa_crecimiento)
        
        # ----------------------------------------------------------------------
        # ESCENARIO 3: Inyección anual del 10% del capital
        # ----------------------------------------------------------------------
        escenario3 = pd.DataFrame({'Fecha': future_dates})
        escenario3['Capital Invertido'] = last_capital
        escenario3['Inyecciones'] = 0
        escenario3['Tipo'] = 'Escenario 3'
        escenario3['Descripción'] = f'Inyección anual del {porcentaje_inyeccion*100:.0f}%'
        
        for i in range(36):
            # Cada 12 meses inyectar capital adicional
            if i > 0 and i % 12 == 0:
                inyeccion = escenario3.at[i-1, 'Capital Invertido'] * porcentaje_inyeccion
                escenario3.at[i, 'Inyecciones'] = inyeccion
                escenario3.at[i, 'Capital Invertido'] += inyeccion
            
            # Crecimiento normal del capital
            if i < 35:
                escenario3.at[i+1, 'Capital Invertido'] = escenario3.at[i, 'Capital Invertido'] * (1 + tasa_crecimiento)
        
        # ----------------------------------------------------------------------
        # VISUALIZACIÓN DE RESULTADOS
        # ----------------------------------------------------------------------
        
        # Combinar datos para gráfico
        projection_data = pd.concat([
            historical_data[['Fecha', 'Capital Invertido', 'Tipo']],
            escenario1[['Fecha', 'Capital Invertido', 'Tipo']],
            escenario2[['Fecha', 'Capital Invertido', 'Tipo']],
            escenario3[['Fecha', 'Capital Invertido', 'Tipo']]
        ])
        
        # Convertir fechas a string para evitar problemas con Plotly
        projection_data['Fecha'] = projection_data['Fecha'].dt.strftime('%Y-%m-%d')
        last_date_str = last_date.strftime('%Y-%m-%d')
        
        # Gráfico de proyección de capital
        st.markdown("### 📈 Proyección de Capital a 3 años (3 escenarios)")
        fig = px.line(
            projection_data,
            x='Fecha',
            y='Capital Invertido',
            color='Tipo',
            title=f'<b>Proyección de Capital Invertido (3 años)</b><br><sup>Tasa de crecimiento mensual: {tasa_crecimiento*100:.1f}%</sup>',
            labels={'Capital Invertido': 'Monto ($)', 'Fecha': 'Fecha'},
            template="plotly_dark",
            line_shape='linear',
            color_discrete_map={
                'Histórico': '#636EFA',
                'Escenario 1': '#EF553B',
                'Escenario 2': '#00CC96',
                'Escenario 3': '#AB63FA'
            }
        )
        
        # Añadir línea vertical para separar histórico de proyección
        fig.add_vline(
            x=last_date_str,
            line_dash="dash",
            line_color="yellow",
            annotation_text="Inicio Proyección",
            annotation_position="top left"
        )
        
        fig.update_layout(
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
        st.plotly_chart(fig, use_container_width=True)
        
        # ----------------------------------------------------------------------
        # COMPARATIVA DE ESCENARIOS
        # ----------------------------------------------------------------------
        st.markdown("### 📊 Comparativa de Escenarios")
        
        # Calcular métricas clave
        capital_final_esc1 = escenario1['Capital Invertido'].iloc[-1]
        capital_final_esc2 = escenario2['Capital Invertido'].iloc[-1]
        capital_final_esc3 = escenario3['Capital Invertido'].iloc[-1]
        
        retiros_totales = escenario1['Retiros'].sum()
        inyecciones_totales = escenario3['Inyecciones'].sum()
        
        # Mostrar métricas en columnas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Escenario 1 - Retiro cada 4 meses",
                f"${capital_final_esc1:,.2f}",
                delta=f"Retiros totales: ${retiros_totales:,.2f}",
                delta_color="off"
            )
            st.markdown("""
            <div style="background-color: #1e1e1e; padding: 10px; border-radius: 5px; margin-top: -15px;">
                <p style="font-size: 14px;">Capital se mantiene constante. Retiras ganancias netas acumuladas cada 4 meses.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.metric(
                "Escenario 2 - Interés compuesto",
                f"${capital_final_esc2:,.2f}",
                delta=f"{(capital_final_esc2/last_capital-1)*100:.1f}% total",
                delta_color="normal"
            )
            st.markdown("""
            <div style="background-color: #1e1e1e; padding: 10px; border-radius: 5px; margin-top: -15px;">
                <p style="font-size: 14px;">Ganancias netas se reinvierten mensualmente (capitalización compuesta).</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.metric(
                "Escenario 3 - Inyección anual",
                f"${capital_final_esc3:,.2f}",
                delta=f"Inyecciones totales: ${inyecciones_totales:,.2f}",
                delta_color="off"
            )
            st.markdown("""
            <div style="background-color: #1e1e1e; padding: 10px; border-radius: 5px; margin-top: -15px;">
                <p style="font-size: 14px;">Cada año inyectas {porcentaje_inyeccion*100:.0f}% del capital actual como nuevo capital.</p>
            </div>
            """.format(porcentaje_inyeccion=porcentaje_inyeccion), unsafe_allow_html=True)
        
        # ----------------------------------------------------------------------
        # DETALLE DE CADA ESCENARIO
        # ----------------------------------------------------------------------
        st.markdown("### 📝 Detalle por Escenario")
        
        tab1, tab2, tab3 = st.tabs(["Escenario 1", "Escenario 2", "Escenario 3"])
        
        with tab1:
            st.markdown("#### Retiro de ganancias cada 4 meses")
            escenario1['Ganancias Acumuladas'] = escenario1['Ganancias Netas'].cumsum()
            escenario1['Retiros Acumulados'] = escenario1['Retiros'].cumsum()
            
            fig_esc1 = px.line(
                escenario1,
                x='Fecha',
                y=['Ganancias Acumuladas', 'Retiros Acumulados'],
                title='Ganancias y Retiros Acumulados',
                template="plotly_dark"
            )
            fig_esc1.update_layout(height=400)
            st.plotly_chart(fig_esc1, use_container_width=True)
            
            st.dataframe(
                escenario1[['Fecha', 'Capital Invertido', 'Ganancias Netas', 'Retiros']].tail(12).style.format({
                    'Capital Invertido': '${:,.2f}',
                    'Ganancias Netas': '${:,.2f}',
                    'Retiros': '${:,.2f}'
                }),
                use_container_width=True
            )
        
        with tab2:
            st.markdown("#### Interés compuesto mensual")
            escenario2['Crecimiento Mensual'] = escenario2['Capital Invertido'].pct_change() * 100
            
            fig_esc2 = px.line(
                escenario2,
                x='Fecha',
                y='Capital Invertido',
                title='Crecimiento del Capital con Interés Compuesto',
                template="plotly_dark"
            )
            fig_esc2.update_layout(height=400)
            st.plotly_chart(fig_esc2, use_container_width=True)
            
            st.dataframe(
                escenario2[['Fecha', 'Capital Invertido', 'Crecimiento Mensual']].tail(12).style.format({
                    'Capital Invertido': '${:,.2f}',
                    'Crecimiento Mensual': '{:.2f}%'
                }),
                use_container_width=True
            )
        
        with tab3:
            st.markdown("#### Inyección anual del capital")
            escenario3['Crecimiento Anual'] = escenario3['Capital Invertido'].pct_change(periods=12) * 100
            
            fig_esc3 = px.bar(
                escenario3,
                x='Fecha',
                y='Inyecciones',
                title='Inyecciones Anuales de Capital',
                template="plotly_dark"
            )
            fig_esc3.update_layout(height=400)
            st.plotly_chart(fig_esc3, use_container_width=True)
            
            st.dataframe(
                escenario3[['Fecha', 'Capital Invertido', 'Inyecciones', 'Crecimiento Anual']].tail(24).style.format({
                    'Capital Invertido': '${:,.2f}',
                    'Inyecciones': '${:,.2f}',
                    'Crecimiento Anual': '{:.2f}%'
                }),
                use_container_width=True
            )
        
        # ----------------------------------------------------------------------
        # RESUMEN Y SUPUESTOS
        # ----------------------------------------------------------------------
        st.markdown("---")
        st.markdown("""
        **📌 Supuestos y consideraciones:**
        - **Tasa de crecimiento mensual**: {tasa_crecimiento*100:.1f}% aplicada sobre el capital
        - **Escenario 1**: 
          - Capital inicial se mantiene constante
          - Ganancias netas se calculan cada mes pero solo se retiran cada 4 meses
          - No hay reinversión de ganancias
        - **Escenario 2**:
          - Ganancias netas se reinvierten completamente cada mes (interés compuesto)
          - Máximo crecimiento potencial pero sin retiros
        - **Escenario 3**:
          - Cada 12 meses se inyecta un {porcentaje_inyeccion*100:.0f}% del capital actual como nuevo capital
          - Las ganancias netas se reinvierten mensualmente
        - Las proyecciones son estimativas y asumen condiciones de mercado constantes
        """.format(tasa_crecimiento=tasa_crecimiento, porcentaje_inyeccion=porcentaje_inyeccion))
    else:
        st.warning("⚠️ No hay suficientes datos históricos para generar proyecciones. Se requieren columnas 'Capital Invertido' y 'Ganancias/Pérdidas Netas'")

# =============================================
# FUNCIONES DE ANÁLISIS
# =============================================

def calculate_roi(df, capital_inicial):
    """Calcula el ROI basado en ganancias netas"""
    if 'Ganancias/Pérdidas Netas' in df.columns and capital_inicial and float(capital_inicial) != 0:
        ganancias_netas = df['Ganancias/Pérdidas Netas'].sum()
        return (float(ganancias_netas) / float(capital_inicial)) * 100
    return 0

def calculate_cagr(df, capital_inicial, current_capital):
    """Calcula la tasa de crecimiento anual compuesta"""
    if len(df) > 1 and capital_inicial and float(capital_inicial) != 0:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
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
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        returns = df['Ganancias/Pérdidas Netas'].pct_change().dropna()
        if len(returns) > 0:
            return (returns.mean() / returns.std()) * (np.sqrt(12))
    return 0

def calculate_max_drawdown(df):
    """Calcula el drawdown máximo"""
    if 'Capital Invertido' in df.columns:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
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
