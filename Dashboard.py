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

# =============================================
# FUNCIONES AUXILIARES (CORREGIDAS)
# =============================================

def safe_divide(numerator, denominator):
    """Evita divisiones por cero"""
    try:
        return numerator / denominator if denominator != 0 else 0
    except:
        return 0

def normalize_column_names(df):
    """
    Normalización robusta de nombres de columnas que maneja:
    - Mapeo exacto de nombres de columnas
    - Verificación sensible a mayúsculas/espacios
    - Diagnóstico detallado de problemas
    """
    # Mapeo exacto de nombres de columnas (conservando mayúsculas y espacios)
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
    
    # Diagnóstico inicial (para debugging)
    original_columns = df.columns.tolist()
    st.write("🔍 Columnas originales recibidas:", original_columns)
    
    # Verificación sensible de columnas existentes
    existing_columns = []
    missing_columns = []
    
    for original_name in column_mapping.keys():
        # Verificación flexible que ignora espacios adicionales y mayúsculas
        found = False
        for actual_col in df.columns:
            if str(actual_col).strip().lower() == original_name.strip().lower():
                existing_columns.append(actual_col)  # Conservamos el nombre exacto del dataframe
                found = True
                break
        
        if not found:
            missing_columns.append(original_name)
    
    # Mostrar advertencias detalladas
    if missing_columns:
        st.warning(f"⚠️ Columnas esperadas no encontradas ({len(missing_columns)}):")
        for col in missing_columns:
            st.write(f"- {col} (se esperaba: {column_mapping[col]})")
        
        st.warning("ℹ️ Columnas disponibles en el archivo:")
        st.write(df.columns.tolist())
    
    # Crear diccionario de renombrado (usando los nombres exactos del dataframe)
    rename_dict = {}
    for original_map_name, new_name in column_mapping.items():
        for actual_col in df.columns:
            if str(actual_col).strip().lower() == original_map_name.strip().lower():
                rename_dict[actual_col] = new_name
                break
    
    # Aplicar el renombrado
    if rename_dict:
        df = df.rename(columns=rename_dict)
    
    # Diagnóstico final
    st.write("✅ Columnas después de normalización:", df.columns.tolist())
    
    return df
def validate_dataframe(df):
    """Validación mejorada con mensajes de error descriptivos"""
    required_columns = {
        'fecha': 'Fecha de las operaciones',
        'capital_invertido': 'Monto de capital invertido',
        'ganancias_perdidas_brutas': 'Ganancias o pérdidas brutas'
    }
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        error_msg = "🚨 Error en los datos - Faltan columnas requeridas:\n"
        for col in missing_cols:
            error_msg += f"\n- {col} ({required_columns[col]})"
        
        # Mostrar columnas disponibles para ayudar en debugging
        error_msg += f"\n\n📋 Columnas disponibles en tu archivo: {', '.join(df.columns.tolist())}"
        return False, error_msg
    
    # Validar tipos de datos
    try:
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['capital_invertido'] = pd.to_numeric(df['capital_invertido'])
        df['ganancias_perdidas_brutas'] = pd.to_numeric(df['ganancias_perdidas_brutas'])
        return True, "✅ Datos validados correctamente"
    except Exception as e:
        return False, f"❌ Error en tipos de datos: {str(e)}\n\nTipos actuales:\n{df.dtypes}"

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
    </style>
    """, unsafe_allow_html=True)

# =============================================
# FUNCIONES DE ANÁLISIS (CORREGIDAS)
# =============================================

def calculate_metrics(df):
    """Cálculo completo de métricas financieras"""
    metrics = {}
    
    # Métricas básicas
    metrics['capital_inicial'] = df['capital_invertido'].iloc[0] if len(df) > 0 else 0
    metrics['capital_actual'] = df['capital_invertido'].iloc[-1] if len(df) > 0 else 0
    metrics['delta_capital'] = metrics['capital_actual'] - metrics['capital_inicial']
    
    # Métricas de ganancias
    metrics['ganancias_brutas'] = df['ganancias_perdidas_brutas'].sum()
    metrics['ganancias_netas'] = df.get('ganancias_perdidas_netas', pd.Series([metrics['ganancias_brutas'])).sum()
    
    # Métricas adicionales
    metrics['comisiones'] = df.get('comisiones_pagadas', pd.Series([0])).sum()
    metrics['retiros'] = df.get('retiro_fondos', pd.Series([0])).sum()
    metrics['inyecciones'] = df.get('aumento_capital', pd.Series([0])).sum()
    
    # Métricas calculadas
    metrics['roi'] = safe_divide(metrics['ganancias_netas'], metrics['capital_inicial']) * 100
    metrics['cagr'] = calculate_cagr(df, metrics['capital_inicial'], metrics['capital_actual'])
    metrics['sharpe_ratio'] = calculate_sharpe_ratio(df)
    metrics['max_drawdown'] = calculate_max_drawdown(df)
    
    return metrics

def calculate_cagr(df, capital_inicial, current_capital):
    """Calcula la tasa de crecimiento anual compuesta"""
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
    """Calcula el ratio Sharpe simplificado"""
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
    """Calcula el drawdown máximo"""
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
# VISUALIZACIONES (CORREGIDAS)
# =============================================

def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False, delta=None):
    """
    Muestra un KPI con tooltip explicativo
    Versión mejorada con estilos consistentes
    """
    # Formatear el valor
    if pd.isna(value) or value is None:
        value_display = "N/D"
    else:
        if is_currency:
            value_display = f"${float(value):,.2f}"
        elif is_percentage:
            value_display = f"{float(value):.2f}%"
        else:
            value_display = str(value)
    
    # Determinar color del delta
    delta_color = "#4CAF50" if delta and str(delta).startswith('+') else "#F44336"
    
    st.markdown(f"""
    <div style="
        background: #1e1e1e;
        color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        border-left: 4px solid #3f33ff;
    ">
        <div style="font-weight: 600; font-size: 14px; color: #ffffff;">
            {icon} {title}
        </div>
        <div style="font-weight: 700; font-size: 24px; margin: 10px 0;">{value_display}</div>
        {f'<div style="color: {delta_color}; font-size: 14px;">{delta}</div>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)

def plot_combined_capital(df, capital_inicial):
    """Gráfico combinado de capital y retiros"""
    if not all(col in df.columns for col in ['fecha', 'capital_invertido']):
        st.warning("No se pueden generar el gráfico. Faltan columnas requeridas.")
        return
    
    try:
        fig = px.line(
            df, x='fecha', y='capital_invertido',
            title='<b>Evolución del Capital Invertido</b>',
            labels={'capital_invertido': 'Monto ($)', 'fecha': 'Fecha'},
            template="plotly_dark"
        )
        
        # Añadir retiros si existen
        if 'retiro_fondos' in df.columns:
            fig.add_bar(
                x=df['fecha'], y=df['retiro_fondos'],
                name='Retiros', marker_color='#FF6B6B', opacity=0.7
            )
        
        # Línea de capital inicial
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
    """Análisis visual de ganancias/pérdidas"""
    if 'ganancias_perdidas_brutas' not in df.columns:
        return
    
    try:
        # Gráfico de barras para ganancias/pérdidas por periodo
        fig = px.bar(
            df, x='fecha', y='ganancias_perdidas_brutas',
            title='<b>Ganancias/Pérdidas Brutas por Periodo</b>',
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
                title='<b>Ganancias/Pérdidas Brutas Acumuladas</b>',
                template="plotly_dark"
            )
            fig_acum.update_layout(height=400)
            st.plotly_chart(fig_acum, use_container_width=True)
    except Exception as e:
        st.error(f"Error al generar gráficos de ganancias: {str(e)}")

# =============================================
# INTERFAZ PRINCIPAL (CORREGIDA)
# =============================================

def main():
    load_custom_style()
    st.title("📊 Dashboard Financiero Fallone Investments")
    
    # Mostrar información de ayuda
    with st.expander("ℹ️ Instrucciones de Uso", expanded=False):
        st.markdown("""
        1. **Sube tu archivo Excel** con los datos financieros
        2. **Selecciona la hoja** que contiene los datos
        3. **Usa los filtros** para ajustar los datos
        4. **Explora las métricas** y gráficos
        
        **Columnas requeridas:**
        - Fecha (debe contener fechas válidas)
        - Capital Invertido (valores numéricos)
        - Ganacias/Pérdidas Brutas (valores numéricos)
        """)
    
    uploaded_file = st.file_uploader("📤 Subir archivo Excel", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            # Cargar datos
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            selected_sheet = st.selectbox("📋 Seleccionar hoja", sheet_names)
            
            @st.cache_data
            def load_data(file, sheet):
                df = pd.read_excel(file, sheet_name=sheet)
                df = normalize_column_names(df)
                return df.loc[:, ~df.columns.duplicated()]
            
            df = load_data(uploaded_file, selected_sheet)
            
            # Validación de datos
            is_valid, validation_msg = validate_dataframe(df)
            if not is_valid:
                st.error(validation_msg)
                st.stop()
            
            # Filtros avanzados
            with st.sidebar.expander("🔍 Filtros Avanzados", expanded=True):
                # Filtro por fechas
                min_date = df['fecha'].min().to_pydatetime()
                max_date = df['fecha'].max().to_pydatetime()
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Fecha inicial", min_date, min_date, max_date)
                with col2:
                    end_date = st.date_input("Fecha final", max_date, min_date, max_date)
                
                # Aplicar filtro de fechas
                filtered_df = df[
                    (df['fecha'] >= pd.to_datetime(start_date)) & 
                    (df['fecha'] <= pd.to_datetime(end_date))
                ]
                
                # Filtro adicional por capital
                if 'capital_invertido' in filtered_df.columns:
                    min_cap = float(filtered_df['capital_invertido'].min())
                    max_cap = float(filtered_df['capital_invertido'].max())
                    cap_range = st.slider("Rango de capital", min_cap, max_cap, (min_cap, max_cap))
                    filtered_df = filtered_df[
                        (filtered_df['capital_invertido'] >= cap_range[0]) & 
                        (filtered_df['capital_invertido'] <= cap_range[1])
            
            if len(filtered_df) == 0:
                st.warning("⚠️ No hay datos que coincidan con los filtros aplicados")
                st.stop()
            
            st.success(f"✅ Datos cargados correctamente ({len(filtered_df)} registros)")
            
            # Calcular métricas
            metrics = calculate_metrics(filtered_df)
            id_inversionista = filtered_df.get('id_inversionista', pd.Series(["N/D"])).iloc[0]
            nombre_inversionista = filtered_df.get('nombre_inversionista', pd.Series(["N/D"])).iloc[0]
            fecha_entrada = filtered_df['fecha'].iloc[0].strftime('%d/%m/%Y') if len(filtered_df) > 0 else "N/D"
            
            # Mostrar KPIs
            st.markdown("---")
            st.markdown('<h2 style="color: #3f33ff;">📊 KPIs Principales</h2>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                display_kpi("ID Inversionista", id_inversionista, "🆔", False)
                display_kpi("Nombre", nombre_inversionista, "👤", False)
                display_kpi("Fecha Inicio", fecha_entrada, "📅", False)
                
            with col2:
                display_kpi("Capital Inicial", metrics['capital_inicial'], "🏁")
                display_kpi("Capital Actual", metrics['capital_actual'], "🏦", 
                           delta=f"{metrics['delta_capital']:+,.2f}")
                display_kpi("Inyecciones", metrics['inyecciones'], "💉")
                
            with col3:
                display_kpi("Ganancias Brutas", metrics['ganancias_brutas'], "💵")
                display_kpi("Ganancias Netas", metrics['ganancias_netas'], "💰")
                display_kpi("Comisiones", metrics['comisiones'], "💸")
                
            with col4:
                display_kpi("Retiros", metrics['retiros'], "↘️")
                display_kpi("ROI", metrics['roi'], "📊", False, True)
                display_kpi("CAGR Mensual", metrics['cagr'], "🚀", False, True)
            
            # Gráficos principales
            st.markdown("---")
            tab1, tab2 = st.tabs(["📈 Visualizaciones", "🔍 Datos Completos"])
            
            with tab1:
                plot_combined_capital(filtered_df, metrics['capital_inicial'])
                plot_profit_analysis(filtered_df)
                
                # Gráfico de comisiones si existe
                if 'comisiones_pagadas' in filtered_df.columns:
                    filtered_df['comisiones_acum'] = filtered_df['comisiones_pagadas'].cumsum()
                    fig_com = px.area(
                        filtered_df, x='fecha', y='comisiones_acum',
                        title='<b>Comisiones Pagadas Acumuladas</b>',
                        template="plotly_dark"
                    )
                    fig_com.update_layout(height=400)
                    st.plotly_chart(fig_com, use_container_width=True)
            
            with tab2:
                st.markdown("### Datos Filtrados")
                
                # Formatear DataFrame para visualización
                display_df = filtered_df.copy()
                numeric_cols = display_df.select_dtypes(include=['float64', 'int64']).columns
                format_dict = {col: '${:,.2f}' for col in numeric_cols}
                
                st.dataframe(
                    display_df.style.format(format_dict),
                    use_container_width=True,
                    height=500
                )
                
                # Exportar datos
                st.markdown("---")
                st.markdown("### Exportar Datos")
                
                csv = filtered_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Descargar como CSV",
                    data=csv,
                    file_name="datos_fallone.csv",
                    mime="text/csv"
                )
        
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {str(e)}")
    else:
        st.info("👋 Por favor, sube un archivo Excel para comenzar")

if __name__ == "__main__":
    main()
