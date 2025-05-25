import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuración inicial
st.set_page_config(page_title="Dashboard Fallone Investments", layout="wide", initial_sidebar_state="expanded")

# ======================
# FUNCIONES DE KPI
# ======================
def display_kpi(title, value, icon="💰", is_currency=True, is_percentage=False, delta=None):
    try:
        if pd.isna(value) or value is None:
            value_display = "N/D"
        elif is_currency:
            value_display = f"${value:,.2f}"
        elif is_percentage:
            value_display = f"{value:.2f}%"
        else:
            value_display = f"{value:.2f}"
    except:
        value_display = "N/D"

    st.markdown(f"""
    <div style="background-color:#1810ca; color:white; padding:12px;
                border-radius:10px; box-shadow:0 4px 8px rgba(0,0,0,0.2); margin-bottom:10px;">
        <div style="font-size:14px; font-weight:bold;">{icon} {title}</div>
        <div style="font-size:24px; font-weight:bold;">{value_display}</div>
    </div>
    """, unsafe_allow_html=True)

# ======================
# CARGA DE ARCHIVO
# ======================
@st.cache_data
def load_excel(file, sheet=None):
    try:
        return pd.read_excel(file, sheet_name=sheet) if sheet else pd.read_excel(file)
    except Exception as e:
        st.error(f"❌ Error al cargar el archivo: {e}")
        return pd.DataFrame()

# ======================
# FILTROS AVANZADOS
# ======================
def advanced_filters(df):
    try:
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
        df = df.dropna(subset=['Fecha'])
        df['MesAño'] = df['Fecha'].dt.to_period('M')

        with st.sidebar.expander("🔍 Filtros Avanzados", expanded=True):
            min_date = df['Fecha'].min().to_pydatetime()
            max_date = df['Fecha'].max().to_pydatetime()
            col1, col2 = st.columns(2)

            with col1:
                start = st.date_input("📅 Inicio", min_date)
            with col2:
                end = st.date_input("📅 Fin", max_date)

            df = df[(df['Fecha'] >= start) & (df['Fecha'] <= end)]

            if 'Capital Invertido' in df.columns:
                cap_values = pd.to_numeric(df['Capital Invertido'], errors='coerce').dropna()
                if not cap_values.empty:
                    min_cap, max_cap = cap_values.min(), cap_values.max()
                    rango = st.slider("💵 Rango Capital Invertido", min_value=float(min_cap), max_value=float(max_cap), value=(float(min_cap), float(max_cap)))
                    df = df[(df['Capital Invertido'] >= rango[0]) & (df['Capital Invertido'] <= rango[1])]

            if 'Ganancias/Pérdidas Brutas' in df.columns:
                tipo = st.radio("📈 Tipo de rendimiento", ["Todos", "Solo ganancias", "Solo pérdidas"])
                if tipo == "Solo ganancias":
                    df = df[df['Ganancias/Pérdidas Brutas'] >= 0]
                elif tipo == "Solo pérdidas":
                    df = df[df['Ganancias/Pérdidas Brutas'] < 0]

        return df
    except Exception as e:
        st.warning(f"Error en filtros: {e}")
        return df
# ==========================
# FUNCIONES DE ANÁLISIS
# ==========================
def calculate_roi(df, capital_inicial):
    try:
        if capital_inicial > 0 and 'Ganancias/Pérdidas Netas' in df.columns:
            return (df['Ganancias/Pérdidas Netas'].sum() / capital_inicial) * 100
    except:
        pass
    return 0

def calculate_cagr(df, capital_inicial, current_capital):
    try:
        if capital_inicial > 0 and len(df) > 1:
            start = df['Fecha'].iloc[0]
            end = df['Fecha'].iloc[-1]
            months = (end.year - start.year) * 12 + (end.month - start.month)
            if months > 0:
                return ((current_capital / capital_inicial) ** (12 / months) - 1) * 100
    except:
        pass
    return 0

def calculate_max_drawdown(df):
    try:
        if 'Capital Invertido' in df.columns:
            df['Max'] = df['Capital Invertido'].cummax()
            df['Drawdown'] = (df['Capital Invertido'] - df['Max']) / df['Max']
            return df['Drawdown'].min() * 100
    except:
        pass
    return 0

def calculate_sharpe_ratio(df):
    try:
        if 'Ganancias/Pérdidas Netas' in df.columns:
            returns = df['Ganancias/Pérdidas Netas'].pct_change().dropna()
            if len(returns) > 0:
                return (returns.mean() / returns.std()) * (np.sqrt(12))
    except:
        pass
    return 0

# ==========================
# FUNCIONES DE VISUALIZACIÓN
# ==========================
def plot_line(df, x_col, y_col, title, y_label):
    try:
        fig = px.line(df, x=x_col, y=y_col, title=title, labels={y_col: y_label, x_col: "Fecha"}, template="plotly_dark")
        fig.update_layout(hovermode="x unified", height=400)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Error al mostrar gráfico: {e}")

def plot_bar(df, x_col, y_col, title, y_label):
    try:
        fig = px.bar(df, x=x_col, y=y_col, title=title, labels={y_col: y_label, x_col: "Fecha"}, template="plotly_dark",
                     color=y_col, color_continuous_scale=px.colors.sequential.Teal)
        fig.update_layout(hovermode="x unified", height=400)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Error al mostrar gráfico: {e}")
# ==========================
# INTERFAZ PRINCIPAL
# ==========================
def main():
    st.title("📊 Dashboard Fallone Investments")

    uploaded_file = st.file_uploader("📥 Cargar archivo Excel", type=["xlsx"])

    if uploaded_file:
        try:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            selected_sheet = st.selectbox("📋 Seleccionar hoja", sheet_names)
            df = load_excel(uploaded_file, selected_sheet)
        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {e}")
            return

        if df.empty:
            st.warning("⚠️ El archivo está vacío o no tiene datos válidos.")
            return

        # Eliminar columnas duplicadas
        df = df.loc[:, ~df.columns.duplicated()]

        # Renombrar columnas si es necesario y evitar duplicación
        if 'Comisiones 10 %' in df.columns:
            if 'Comisiones Pagadas' not in df.columns:
                df.rename(columns={'Comisiones 10 %': 'Comisiones Pagadas'}, inplace=True)
            else:
                df.drop(columns=['Comisiones 10 %'], inplace=True)

        df.rename(columns={
            'Ganacias/Pérdidas Brutas': 'Ganancias/Pérdidas Brutas',
            'Ganacias/Pérdidas Netas': 'Ganancias/Pérdidas Netas'
        }, inplace=True)

        # Conversión de fecha
        if 'Fecha' not in df.columns:
            st.error("❌ La columna 'Fecha' es obligatoria.")
            return
        df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')

        # Aplicar filtros
        filtered_df = advanced_filters(df)

        if filtered_df.empty:
            st.warning("⚠️ No hay datos después de aplicar los filtros.")
            return

        capital_inicial = float(df['Aumento Capital'].dropna().values[0]) if 'Aumento Capital' in df.columns and not df['Aumento Capital'].dropna().empty else 0.0
        current_capital = filtered_df['Capital Invertido'].iloc[-1] if 'Capital Invertido' in filtered_df.columns else 0.0

        roi = calculate_roi(filtered_df, capital_inicial)
        cagr = calculate_cagr(filtered_df, capital_inicial, current_capital)
        drawdown = calculate_max_drawdown(filtered_df)
        sharpe = calculate_sharpe_ratio(filtered_df)

        # KPIs y Tabs seguirían aquí...

        # ==========================
        # KPIs FINANCIEROS
        # ==========================
        st.markdown("## 📈 Indicadores Financieros")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            display_kpi("Capital Inicial", capital_inicial)
        with col2:
            display_kpi("Capital Actual", current_capital)
        with col3:
            display_kpi("ROI", roi, is_currency=False, is_percentage=True)
        with col4:
            display_kpi("CAGR Mensual", cagr, is_currency=False, is_percentage=True)

        col5, col6, col7, col8 = st.columns(4)
        with col5:
            display_kpi("Drawdown Máximo", drawdown, is_currency=False, is_percentage=True)
        with col6:
            display_kpi("Ratio Sharpe", sharpe, is_currency=False)
        with col7:
            display_kpi("Ganancias Netas", filtered_df['Ganancias/Pérdidas Netas'].sum() if 'Ganancias/Pérdidas Netas' in filtered_df.columns else 0)
        with col8:
            display_kpi("Comisiones Pagadas", filtered_df['Comisiones Pagadas'].iloc[-1] if 'Comisiones Pagadas' in filtered_df.columns else 0)

        # ==========================
        # TABS DE VISUALIZACIÓN
        # ==========================
        tab1, tab2, tab3 = st.tabs(["📊 Capital", "💵 Ganancias", "📉 Comisiones"])

        with tab1:
            if 'Capital Invertido' in filtered_df.columns:
                plot_line(filtered_df, 'Fecha', 'Capital Invertido', "Evolución del Capital Invertido", "Capital ($)")
        
        with tab2:
            if 'Ganancias/Pérdidas Brutas' in filtered_df.columns:
                plot_bar(filtered_df, 'Fecha', 'Ganancias/Pérdidas Brutas', "Ganancias Brutas", "Ganancia ($)")

        with tab3:
            if 'Comisiones Pagadas' in filtered_df.columns:
                plot_line(filtered_df, 'Fecha', 'Comisiones Pagadas', "Comisiones Pagadas", "Comisión ($)")
        # ==========================
        # TABLA DE DATOS Y DESCARGA
        # ==========================
        st.markdown("## 🔍 Datos Filtrados")
        st.dataframe(filtered_df.style.format({
            'Capital Invertido': '${:,.2f}',
            'Ganancias/Pérdidas Brutas': '${:,.2f}',
            'Ganancias/Pérdidas Netas': '${:,.2f}',
            'Comisiones Pagadas': '${:,.2f}',
            'Retiro de Fondos': '${:,.2f}'
        }), use_container_width=True)

        st.download_button(
            label="⬇️ Descargar datos filtrados en CSV",
            data=filtered_df.to_csv(index=False).encode("utf-8"),
            file_name="datos_filtrados.csv",
            mime="text/csv"
        )

    else:
        st.info("👆 Por favor, sube un archivo Excel para comenzar el análisis.")

# Ejecutar app
if __name__ == "__main__":
    main()


