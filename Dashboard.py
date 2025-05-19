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
    Normalización mejorada que maneja múltiples formatos de columnas.
    Versión corregida para aceptar todas las variantes de nombres.
    """
    # Primero hacer replacements específicos para casos conocidos
    df.columns = df.columns.str.strip()
    
    # Mapeo completo de todas las variantes posibles
    column_mappings = {
        'ganancias_perdidas_brutas': [
            'ganancias', 'perdidas', 'resultado', 'profit', 'g/p', 'rentabilidad',
            'ganancias brutas', 'perdidas brutas', 'resultado bruto', 
            'ganancias perdidas', 'ganancias y perdidas', 'ganancias-perdidas',
            'ganancias/perdidas', 'ganancias & perdidas', 'ganancias pérdidas',
            'ganancias_perdidas', 'gananciasperdidas', 'gananciasperdidas brutas'
        ],
        'capital_invertido': [
            'capital', 'inversion', 'monto', 'invest', 'principal', 'amount',
            'capital invertido', 'monto invertido', 'inversion total',
            'capital_inversion', 'capital-inversion', 'capital/inversion'
        ],
        'fecha': [
            'date', 'fecha', 'time', 'periodo', 'dia', 'mes',
            'fecha operacion', 'fecha operación', 'fecha transaccion',
            'fecha movimiento', 'fecha registro', 'fecha valor'
        ],
        'aumento_capital': [
            'inyeccion', 'aumento', 'adicional', 'extra', 'deposito',
            'aumento capital', 'capital adicional', 'inyeccion capital',
            'deposito capital', 'capital extra', 'aumento de capital'
        ],
        'comisiones_pagadas': [
            'comisiones', 'fee', 'costo', 'gastos', 'tarifa',
            'comisiones pagadas', 'comisiones 10%', 'comisiones 10 %',
            'comisiones pagadas', 'comisiones cobradas', 'comisiones de gestion'
        ],
        'retiro_fondos': [
            'retiro', 'retiros', 'withdrawal', 'extraccion', 'salida',
            'retiro fondos', 'retiro de fondos', 'retiros de capital',
            'extraccion fondos', 'retiro dinero', 'retiro de dinero'
        ]
    }

    # Construir mapeo inverso para búsqueda eficiente
    reverse_mapping = {}
    for standard_name, variants in column_mappings.items():
        for variant in variants:
            reverse_mapping[variant.lower().replace(' ', '').replace('_', '').replace('-', '').replace('/', '')] = standard_name

    # Normalizar nombres de columnas
    new_columns = []
    for col in df.columns:
        normalized_col = col.lower().strip().replace(' ', '').replace('_', '').replace('-', '').replace('/', '')
        found = False
        
        # Buscar en el mapeo inverso
        for variant, standard in reverse_mapping.items():
            if variant in normalized_col:
                new_columns.append(standard)
                found = True
                break
                
        if not found:
            # Conservar el nombre original si no se encuentra en el mapeo
            new_columns.append(col)
    
    df.columns = new_columns
    return df

def validate_dataframe(df):
    """
    Validación mejorada con mensajes de error descriptivos.
    Versión corregida para manejar casos especiales.
    """
    required_columns = {
        'fecha': {
            'description': 'Fecha de las operaciones (columna temporal)',
            'alternatives': ['date', 'fecha', 'periodo', 'dia', 'mes']
        },
        'capital_invertido': {
            'description': 'Monto de capital invertido (valores numéricos)',
            'alternatives': ['capital', 'inversion', 'monto', 'principal']
        },
        'ganancias_perdidas_brutas': {
            'description': 'Ganancias o pérdidas brutas (valores numéricos)',
            'alternatives': ['ganancias', 'perdidas', 'resultado', 'profit']
        }
    }
    
    missing_cols = []
    suggestions = {}
    
    # Verificar columnas requeridas
    for col, info in required_columns.items():
        if col not in df.columns:
            missing_cols.append(col)
            suggestions[col] = info['alternatives']
    
    if missing_cols:
        error_msg = "🚨 Error en los datos - Faltan columnas requeridas:\n"
        for col in missing_cols:
            info = required_columns[col]
            error_msg += f"\n- {col} ({info['description']})"
            if info['alternatives']:
                error_msg += f"\n  Nombres alternativos aceptados: {', '.join(info['alternatives'])}"
        
        # Mostrar columnas disponibles para ayudar en debugging
        error_msg += f"\n\n📋 Columnas disponibles en tu archivo: {', '.join(df.columns.tolist())}"
        error_msg += "\n\n💡 Sugerencia: Verifica si alguna de tus columnas coincide con los nombres alternativos mencionados."
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
# INTERFAZ PRINCIPAL (CORREGIDA)
# =============================================

def main():
    load_custom_style()
    st.title("📊 Fondo de Inversión Fallone Investment")
    
    # Mostrar información de ayuda
    with st.expander("ℹ️ Instrucciones (Leer antes de comenzar)", expanded=False):
        st.markdown("""
        1. **Sube tu archivo Excel** con los datos financieros
        2. **Selecciona la hoja** que contiene los datos
        3. **Usa los filtros** en la barra lateral para ajustar los datos
        4. **Explora las métricas** y gráficos en las diferentes pestañas
        
        **Columnas requeridas:**
        - `fecha` (debe contener fechas válidas)
        - `capital_invertido` (valores numéricos)
        - `ganancias_perdidas_brutas` (valores numéricos)
        
        **El sistema acepta variantes de estos nombres** como "Ganancias Brutas", "Capital", "Fecha Operación", etc.
        """)
    
    uploaded_file = st.file_uploader("📤 Subir archivo Excel", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
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
            
            # Opción para debugging avanzado
            debug_mode = st.checkbox("🛠️ Modo depuración (mostrar datos sin procesar)")
            
            @st.cache_data
            def load_data(file, sheet):
                df = pd.read_excel(file, sheet_name=sheet)
                if debug_mode:
                    st.write("### Datos sin procesar (antes de normalización):")
                    st.write("Columnas:", df.columns.tolist())
                    st.dataframe(df.head(3))
                df = normalize_column_names(df)
                if debug_mode:
                    st.write("### Datos después de normalización:")
                    st.write("Columnas:", df.columns.tolist())
                    st.dataframe(df.head(3))
                return df.loc[:, ~df.columns.duplicated()]
            
            df = load_data(uploaded_file, selected_sheet)
            
            # Validar datos
            is_valid, validation_msg = validate_dataframe(df)
            if not is_valid:
                st.error(validation_msg)
                st.stop()
            
            # Obtener métricas iniciales
            capital_inicial = df['capital_invertido'].iloc[0] if len(df) > 0 else 0
            id_inversionista = df.get('id_inversionista', pd.Series(["N/D"])).iloc[0]
            
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
            total_aumentos = filtered_df.get('aumento_capital', pd.Series([0])).sum()
            ganancias_brutas = filtered_df['ganancias_perdidas_brutas'].sum()
            ganancias_netas = filtered_df.get('ganancias_perdidas_netas', pd.Series([ganancias_brutas])).sum()
            comisiones = filtered_df.get('comisiones_pagadas', pd.Series([0])).sum()
            retiros = filtered_df.get('retiro_fondos', pd.Series([0])).sum()
            
            roi = calculate_roi(ganancias_netas, capital_inicial)
            cagr = calculate_cagr(filtered_df, capital_inicial, current_capital)
            sharpe_ratio = calculate_sharpe_ratio(filtered_df)
            max_drawdown = calculate_max_drawdown(filtered_df)
            
            # Mostrar KPIs en un layout organizado
            kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
            
            with kpi_col1:
                display_kpi("ID Inversionista", id_inversionista, "🆔", is_currency=False)
                display_kpi("Capital Inicial", capital_inicial, "🏁")
                display_kpi("Ganancias Netas", ganancias_netas, "💰")
                
            with kpi_col2:
                display_kpi("Fecha de Entrada", fecha_entrada, "📅", is_currency=False)
                display_kpi("Capital Actual", current_capital, "🏦", delta=f"{delta_capital:+,.2f}")
                display_kpi("Comisiones Pagadas", comisiones, "💸")
                
            with kpi_col3:
                display_kpi("Total Inyección", total_aumentos, "📈")
                display_kpi("Ganancias Brutas", ganancias_brutas, "💵")
                display_kpi("Retiro de Dinero", retiros, "↘️")
                
            with kpi_col4:
                display_kpi("ROI", roi, "📊", is_percentage=True)
                display_kpi("CAGR Mensual", cagr, "🚀", is_percentage=True)
                display_kpi("Drawdown Máx.", max_drawdown, "📉", is_percentage=True)
            
            # SECCIÓN DE GRÁFICOS PRINCIPALES
            st.markdown("---")
            tab1, tab2, tab3 = st.tabs(["📈 Visualizaciones Principales", "🔍 Detalle de Datos", "🔮 Proyección Futura"])
            
            with tab1:
                plot_combined_capital_withdrawals(filtered_df, capital_inicial)
                plot_capital_profit_relation(filtered_df)
                
                # Gráfico de ganancias/pérdidas
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
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Gráfico de comisiones si existe la columna
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
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab2:
                st.markdown("### Datos Filtrados")
                
                # Formatear DataFrame para visualización
                display_df = filtered_df.copy()
                numeric_cols = display_df.select_dtypes(include=['float64', 'int64']).columns
                format_dict = {col: "${:,.2f}" for col in numeric_cols}
                
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
            if debug_mode:
                st.exception(e)
    else:
        st.info("👋 Por favor, sube un archivo Excel para comenzar el análisis")

# =============================================
# FUNCIONES DE VISUALIZACIÓN (CORREGIDAS)
# =============================================

def plot_combined_capital_withdrawals(df, capital_inicial):
    """Muestra la evolución del capital vs retiros"""
    if not all(col in df.columns for col in ['fecha', 'capital_invertido']):
        st.warning("⚠️ No se pueden generar el gráfico. Faltan columnas requeridas.")
        return
    
    try:
        fig = px.line(
            df,
            x='fecha',
            y='capital_invertido',
            title='<b>Evolución del Capital</b>',
            labels={'capital_invertido': 'Monto ($)', 'fecha': 'Fecha'},
            template="plotly_dark"
        )
        
        # Añadir retiros si existe la columna
        if 'retiro_fondos' in df.columns:
            fig.add_bar(
                x=df['fecha'],
                y=df['retiro_fondos'],
                name='Retiros',
                marker_color='#FF6B6B',
                opacity=0.7
            )
            fig.update_layout(title='<b>Evolución del Capital vs Retiros</b>')
        
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
            hovermode="x unified",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error al generar gráfico: {str(e)}")

def plot_capital_profit_relation(df):
    """Muestra la relación entre capital y ganancias"""
    if not all(col in df.columns for col in ['fecha', 'capital_invertido', 'ganancias_perdidas_brutas']):
        st.warning("⚠️ No se puede generar el gráfico de relación. Faltan datos.")
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
            title='Relación: Ganancias Brutas / Capital Invertido',
            labels={'porcentaje_ganancias': 'Porcentaje (%)', 'fecha': 'Fecha'},
            color='porcentaje_ganancias',
            color_continuous_scale=px.colors.diverging.RdYlGn,
            template="plotly_dark"
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="white")
        fig.update_layout(height=400, yaxis_title="Porcentaje de Ganancias (%)")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"❌ Error al generar gráfico: {str(e)}")

def plot_projection(df):
    """Proyección futura basada en datos históricos"""
    if len(df) < 2 or not all(col in df.columns for col in ['fecha', 'capital_invertido']):
        st.warning("⚠️ No hay suficientes datos para generar proyecciones")
        return
    
    try:
        # Preparar datos históricos
        historical_data = df[['fecha', 'capital_invertido']].copy()
        historical_data['tipo'] = 'Histórico'
        
        # Calcular crecimiento promedio
        historical_data['crecimiento'] = historical_data['capital_invertido'].pct_change()
        avg_growth = historical_data['crecimiento'].mean()
        
        # Valores por defecto si hay problemas con los cálculos
        if pd.isna(avg_growth) or not np.isfinite(avg_growth):
            avg_growth = 0.02  # 2% mensual por defecto
        
        # Crear fechas futuras (36 meses)
        last_date = historical_data['fecha'].max()
        last_capital = historical_data['capital_invertido'].iloc[-1]
        future_dates = pd.date_range(start=last_date, periods=36, freq='M')
        
        # Escenario base
        scenario1 = pd.DataFrame({'fecha': future_dates})
        scenario1['capital_invertido'] = last_capital * (1 + avg_growth) ** np.arange(1, 37)
        scenario1['tipo'] = 'Proyección Base'
        
        # Combinar datos
        projection_data = pd.concat([historical_data, scenario1])
        
        # Gráfico de proyección
        fig = px.line(
            projection_data,
            x='fecha',
            y='capital_invertido',
            color='tipo',
            title='Proyección de Capital (3 años)',
            labels={'capital_invertido': 'Monto ($)', 'fecha': 'Fecha'},
            template="plotly_dark"
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar métricas clave
        st.metric("Tasa de crecimiento mensual", f"{avg_growth:.2%}")
        st.metric("Capital proyectado (36 meses)", f"${scenario1['capital_invertido'].iloc[-1]:,.2f}")
        
        # Explicación de supuestos
        st.info("""
        **Supuestos de la proyección:**
        - Basada en el crecimiento histórico promedio
        - No considera cambios en las condiciones del mercado
        - Para análisis ilustrativo solamente
        """)
    except Exception as e:
        st.error(f"❌ Error al generar proyección: {str(e)}")

# =============================================
# FUNCIÓN DE FILTROS (CORREGIDA)
# =============================================

def advanced_filters(df):
    """Filtros mejorados con manejo robusto de errores"""
    with st.sidebar.expander("🔍 Filtros Avanzados", expanded=True):
        filtered_df = df.copy()
        
        # Filtro por fechas
        if 'fecha' in filtered_df.columns:
            try:
                min_date = filtered_df['fecha'].min().to_pydatetime()
                max_date = filtered_df['fecha'].max().to_pydatetime()
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Fecha inicial", min_value=min_date, max_value=max_date, value=min_date)
                with col2:
                    end_date = st.date_input("Fecha final", min_value=min_date, max_value=max_date, value=max_date)
                
                if start_date > end_date:
                    st.error("La fecha inicial no puede ser mayor que la final")
                else:
                    filtered_df = filtered_df[
                        (filtered_df['fecha'] >= pd.to_datetime(start_date)) & 
                        (filtered_df['fecha'] <= pd.to_datetime(end_date))
                    ]
            except Exception as e:
                st.warning(f"Error en filtro de fechas: {str(e)}")
        
        # Filtro por capital
        if 'capital_invertido' in filtered_df.columns:
            try:
                min_val = float(filtered_df['capital_invertido'].min())
                max_val = float(filtered_df['capital_invertido'].max())
                val_range = st.slider("Rango de capital", min_val, max_val, (min_val, max_val))
                filtered_df = filtered_df[
                    (filtered_df['capital_invertido'] >= val_range[0]) & 
                    (filtered_df['capital_invertido'] <= val_range[1])
            except:
                pass
        
        # Filtro por resultados
        if 'ganancias_perdidas_brutas' in filtered_df.columns:
            try:
                option = st.selectbox("Filtrar por", ["Todos", "Solo ganancias", "Solo pérdidas"])
                if option == "Solo ganancias":
                    filtered_df = filtered_df[filtered_df['ganancias_perdidas_brutas'] >= 0]
                elif option == "Solo pérdidas":
                    filtered_df = filtered_df[filtered_df['ganancias_perdidas_brutas'] < 0]
            except:
                pass
    
    return filtered_df

if __name__ == "__main__":
    main()
