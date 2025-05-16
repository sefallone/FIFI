import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime
import base64
from io import BytesIO
import hashlib  # Para seguridad de archivos

# =============================================
# CONFIGURACIÓN SEGURA DE LA PÁGINA
# =============================================
st.set_page_config(
    page_title="Dashboard Fallone Investments (Seguro)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# MEJORAS DE SEGURIDAD Y VALIDACIÓN
# =============================================
def validate_file(file):
    """Valida el archivo subido"""
    if not file:
        return False
    
    # Verificar tipo de archivo por contenido y extensión
    if file.type not in ["application/vnd.ms-excel", 
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
        return False
    
    # Verificar tamaño (max 10MB)
    if file.size > 10 * 1024 * 1024:
        return False
        
    return True

def sanitize_df(df):
    """Limpia y protege el DataFrame"""
    # Eliminar columnas potencialmente peligrosas
    dangerous_cols = ['formula', 'object', 'macro']
    df = df.loc[:, ~df.columns.str.lower().isin(dangerous_cols)]
    
    # Convertir todas las celdas a string y limpiar
    for col in df.columns:
        df[col] = df[col].astype(str).str[:500]  # Limitar longitud
        
    return df

# =============================================
# FUNCIÓN DE FILTROS AVANZADOS (MEJORADA)
# =============================================
def advanced_filters(df):
    """Función con selector de fechas por mes y año - Versión segura"""
    with st.sidebar.expander("🔍 Filtros Avanzados", expanded=True):
        filtered_df = df.copy()
        
        # Validación de columnas requeridas
        required_cols = ['Fecha', 'Capital Invertido']
        missing = [col for col in required_cols if col not in filtered_df.columns]
        if missing:
            st.error(f"Faltan columnas requeridas: {', '.join(missing)}")
            return df  # Devuelve el original sin filtrar
        
        try:
            # Manejo robusto de fechas
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
# FUNCIONES DE CÁLCULO SEGURAS
# =============================================
@st.cache_data(ttl=3600, show_spinner=False)
def calculate_roi(df, capital_inicial):
    """Calcula el ROI con validación completa"""
    try:
        capital_inicial = float(capital_inicial)
        if capital_inicial <= 0:
            return 0.0
            
        if 'Ganancias/Pérdidas Netas' not in df.columns:
            return 0.0
            
        ganancias_netas = pd.to_numeric(df['Ganancias/Pérdidas Netas'], errors='coerce').sum()
        return (ganancias_netas / capital_inicial) * 100
    except:
        return 0.0

@st.cache_data(ttl=3600, show_spinner=False)
def calculate_cagr(df, capital_inicial, current_capital):
    """Calcula la CAGR con validación robusta"""
    try:
        capital_inicial = float(capital_inicial)
        current_capital = float(current_capital)
        
        if capital_inicial <= 0 or current_capital < 0:
            return 0.0
            
        if 'Fecha' not in df.columns:
            return 0.0
            
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha'])
        
        if len(df) < 2:
            return 0.0
            
        start_date = df['Fecha'].min()
        end_date = df['Fecha'].max()
        
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if months <= 0:
            months = 1
            
        return ((current_capital / capital_inicial) ** (12/months) - 1) * 100
    except:
        return 0.0

@st.cache_data(ttl=3600, show_spinner=False)
def calculate_sharpe_ratio(df):
    """Ratio Sharpe con manejo de errores"""
    try:
        if 'Ganancias/Pérdidas Netas' not in df.columns:
            return 0.0
            
        returns = pd.to_numeric(df['Ganancias/Pérdidas Netas'], errors='coerce').pct_change().dropna()
        
        if len(returns) < 2 or returns.std() == 0:
            return 0.0
            
        return (returns.mean() / returns.std()) * np.sqrt(12)
    except:
        return 0.0

# =============================================
# VISUALIZACIONES MEJORADAS
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
        
        fig = px.line(
            df,
            x='Fecha',
            y='Capital Invertido',
            title='<b>Evolución del Capital vs Retiros</b>',
            labels={'Capital Invertido': 'Monto ($)', 'Fecha': 'Fecha'},
            template="plotly_dark"
        )
        
        fig.add_bar(
            x=df['Fecha'],
            y=df['Retiro de Fondos'],
            name='Retiros',
            marker_color='#FF6B6B',
            opacity=0.7
        )
        
        fig.add_hline(
            y=float(capital_inicial),
            line_dash="dash",
            line_color="green",
            annotation_text=f"Capital Inicial: ${float(capital_inicial):,.2f}",
            annotation_position="bottom right"
        )
        
        fig.update_layout(
            height=450,
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor="rgba(0,0,0,0.8)",
                font_size=12,
                font_family="Arial"
            ),
            xaxis=dict(
                rangeslider=dict(visible=True),
                type="date"
            )
        )
        
        # Tooltips personalizados
        fig.update_traces(
            hovertemplate="<b>Fecha</b>: %{x|%d-%m-%Y}<br><b>Monto</b>: $%{y:,.2f}<extra></extra>"
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True})
        
    except Exception as e:
        st.error(f"Error al generar gráfico: {str(e)}")

# =============================================
# INTERFAZ PRINCIPAL SEGURA
# =============================================
def main():
    # Configuración de estilo seguro
    st.markdown("""
    <style>
        .stApp {
            background-color: #121212;
            color: #ffffff;
        }
        .stAlert {
            background-color: #2d2d2d !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📊 Dashboard Seguro de Inversiones")
    
    # Carga segura de archivos
    with st.sidebar:
        st.header("📤 Carga de Datos Segura")
        uploaded_file = st.file_uploader(
            "Subir archivo Excel", 
            type=['xlsx', 'xls'],
            help="Suba un archivo Excel seguro (max 10MB)"
        )
        
        if not uploaded_file:
            st.info("Por favor, suba un archivo Excel válido")
            st.stop()
            
        if not validate_file(uploaded_file):
            st.error("Archivo no válido. Por favor suba un archivo Excel válido (max 10MB)")
            st.stop()
            
        try:
            # Carga segura con sanitización
            @st.cache_data(ttl=3600, show_spinner="Cargando datos...")
            def load_data(file):
                xls = pd.ExcelFile(file)
                sheets = xls.sheet_names
                return {sheet: sanitize_df(pd.read_excel(xls, sheet_name=sheet)) for sheet in sheets}
                
            data = load_data(uploaded_file)
            selected_sheet = st.selectbox("Seleccionar hoja", list(data.keys()))
            df = data[selected_sheet]
            
            # Validación básica de datos
            if df.empty:
                st.error("La hoja seleccionada está vacía")
                st.stop()
                
            # Procesamiento seguro
            capital_inicial = pd.to_numeric(df['Aumento Capital'].iloc[1], errors='coerce') if len(df) > 1 else 0
            if pd.isna(capital_inicial) or capital_inicial <= 0:
                st.error("El capital inicial no es válido")
                st.stop()
                
            filtered_df = advanced_filters(df)
            
        except Exception as e:
            st.error(f"Error crítico al procesar el archivo: {str(e)}")
            st.stop()
    
    # Visualización principal segura
    try:
        # KPIs con validación
        current_capital = pd.to_numeric(filtered_df['Capital Invertido'].iloc[-1], errors='coerce') if len(filtered_df) > 0 else 0
        delta_capital = current_capital - capital_inicial if current_capital else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Capital Inicial", f"${capital_inicial:,.2f}")
        with col2:
            st.metric("Capital Actual", f"${current_capital:,.2f}", delta=f"{delta_capital:+,.2f}")
        
        # Gráficos principales
        plot_combined_capital_withdrawals(filtered_df, capital_inicial)
        
        # Exportación segura
        if st.button("Exportar Datos Filtrados"):
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar CSV Seguro",
                data=csv,
                file_name="datos_filtrados_seguros.csv",
                mime="text/csv"
            )
            
    except Exception as e:
        st.error(f"Error en la visualización: {str(e)}")

if __name__ == "__main__":
    main()
