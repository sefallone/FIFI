import streamlit as st
import pandas as pd
import plotly.express as px
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
                filtered_df['Fecha'] = pd.to_datetime(filtered_df['Fecha'])
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
                    ).replace(day=1)
                
                with col2:
                    end_date = st.date_input(
                        "Mes final",
                        value=max_date,
                        min_value=min_date,
                        max_value=max_date,
                        key="end_date"
                    ).replace(day=1)
                
                start_period = pd.to_datetime(start_date).to_period('M')
                end_period = pd.to_datetime(end_date).to_period('M')
                
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
# FUNCIÓN PARA MOSTRAR KPIs CON ESTILOS MEJORADOS
# =============================================

def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False, delta=None):
    if pd.isna(value) or value is None:
        value_display = "N/D"
        delta_display = None
    else:
        if is_currency:
            value_display = f"${value:,.2f}"
        elif is_percentage:
            value_display = f"{value:.2f}%"
        else:
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
# GRÁFICO DE RELACIÓN CAPITAL-GANANCIAS
# =============================================

def plot_capital_profit_relation(df):
    """Muestra la relación porcentual entre capital invertido y ganancias brutas"""
    if 'Capital Invertido' not in df.columns or 'Ganancias/Pérdidas Brutas' not in df.columns:
        st.warning("No se pueden calcular las métricas de relación. Faltan columnas necesarias.")
        return
    
    # Calcular el porcentaje de ganancias sobre el capital
    df['Porcentaje_Ganancias'] = (df['Ganancias/Pérdidas Brutas'] / df['Capital Invertido']) * 100
    
    # Crear el gráfico
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
    
    # Añadir línea en el 0% como referencia
    fig.add_hline(y=0, line_dash="dash", line_color="white")
    
    # Personalizar el gráfico
    fig.update_layout(
        height=400,
        yaxis_title="Porcentaje de Ganancias (%)",
        coloraxis_colorbar=dict(title="% Ganancias")
    )
    
    st.plotly_chart(fig, use_container_width=True)

# =============================================
# INTERFAZ PRINCIPAL
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
            df = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
            
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
            
            # Obtener fecha de entrada (primera fecha disponible)
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
            
            # SECCIÓN DE KPIs
            st.markdown("---")
            st.markdown('<h2 style="color: #1024ca; border-bottom: 2px solid #1024ca; padding-bottom: 10px;">📊 KPIs Financieros</h2>', unsafe_allow_html=True)
            
            # Primera fila de KPIs
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                display_kpi("ID Inversionista", id_inversionista, "🆔", is_currency=False)
            with col2:
                display_kpi("Fecha de Entrada al Fondo", fecha_entrada, "📅", is_currency=False)
            with col3:
                display_kpi("Capital Inicial al entrar al fondo", capital_inicial, "🏁")
            with col4:
                current_capital = filtered_df['Capital Invertido'].iloc[-1] if len(filtered_df) > 0 else 0
                delta_capital = current_capital - capital_inicial if len(filtered_df) > 0 else 0
                display_kpi("Capital Actual", current_capital, "🏦", delta=f"{delta_capital:+,.2f}")
            
            # Segunda fila de KPIs
            col5, col6, col7, col8 = st.columns(4)
            with col5:
                total_aumentos = filtered_df['Aumento Capital'].sum()
                display_kpi("Total Inyección de Capital", total_aumentos, "📈")
            with col6:
                ganancias_brutas = filtered_df['Ganancias/Pérdidas Brutas'].sum() if 'Ganancias/Pérdidas Brutas' in filtered_df.columns else None
                display_kpi("Ganancias Brutas", ganancias_brutas, "💵")
            with col7:
                ganancias_netas = filtered_df['Ganancias/Pérdidas Netas'].sum() if 'Ganancias/Pérdidas Netas' in filtered_df.columns else None
                display_kpi("Ganancias Netas", ganancias_netas, "💰")
            with col8:
                comisiones = filtered_df['Comisiones Pagadas'].sum() if 'Comisiones Pagadas' in filtered_df.columns else None
                display_kpi("Comisiones Pagadas", comisiones, "💸")
            
            # Tercera fila de KPIs
            col9, col10, col11, col12 = st.columns(4)
            with col9:
                retiros = filtered_df['Retiro de Fondos'].sum() if 'Retiro de Fondos' in filtered_df.columns else None
                display_kpi("Retiro de Dinero", retiros, "↘️")
            
            # SECCIÓN DE GRÁFICOS PRINCIPALES
            st.markdown("---")
            st.markdown('<h2 style="color: #1024ca; border-bottom: 2px solid #67e4da; padding-bottom: 10px;">📈 Visualizaciones Principales</h2>', unsafe_allow_html=True)
            
            # Gráfico de evolución del capital
            if 'Fecha' in filtered_df.columns and 'Capital Invertido' in filtered_df.columns:
                try:
                    fig1 = px.line(
                        filtered_df,
                        x='Fecha',
                        y='Capital Invertido',
                        title='Evolución del Capital Invertido',
                        labels={'Capital Invertido': 'Monto ($)', 'Fecha': 'Fecha'},
                        template="plotly_dark"
                    )
                    fig1.add_hline(y=capital_inicial, line_dash="dash", line_color="green", 
                                annotation_text=f"Capital Inicial: ${capital_inicial:,.2f}", 
                                annotation_position="bottom right")
                    fig1.update_layout(height=400)
                    st.plotly_chart(fig1, use_container_width=True)
                except Exception as e:
                    st.error(f"Error al generar gráfico de capital: {str(e)}")
            
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
        
        except Exception as e:
            st.error(f"🚨 Error crítico al procesar el archivo: {str(e)}")
    else:
        st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")

if __name__ == "__main__":
    main()
