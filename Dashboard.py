import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

# =============================================
# CONFIGURACIÓN INICIAL
# =============================================

st.set_page_config(
    page_title="Dashboard Fallone Investments",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================
# FUNCIONES AUXILIARES
# =============================================

def safe_divide(numerator, denominator):
    try:
        return numerator / denominator if denominator != 0 else 0
    except:
        return 0

def normalize_column_names(df):
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace('á','a')
        .str.replace('é','e')
        .str.replace('í','i')
        .str.replace('ó','o')
        .str.replace('ú','u')
    )

    column_mapping = {
        'fecha': 'fecha',
        'id inv': 'id_inversionista',
        'nombre inversionista': 'nombre_inversionista',
        'capital invertido': 'capital_invertido',
        'aumento capital': 'aumento_capital',
        'retiro de fondos': 'retiro_fondos',
        'ganacias/perdidas brutas': 'ganancias_perdidas_brutas',
        'ganancias/perdidas brutas': 'ganancias_perdidas_brutas',
        'ganancias': 'ganancias_perdidas_brutas',
        'perdidas': 'ganancias_perdidas_brutas',
        'resultado': 'ganancias_perdidas_brutas',
        'profit': 'ganancias_perdidas_brutas',
        'comisiones 10 %': 'comisiones_pagadas',
        'comisiones pagadas': 'comisiones_pagadas',
        'ganacias/perdidas netas': 'ganancias_perdidas_netas',
        'ganancias/perdidas netas': 'ganancias_perdidas_netas',
        'ganancias/perdidas netas acumuladas': 'ganancias_perdidas_netas_acum',
        'beneficio en %': 'beneficio_porcentaje'
    }

    df = df.rename(columns={col: column_mapping.get(col, col) for col in df.columns})
    return df

def validate_dataframe(df):
    required_columns = {
        'fecha': 'Fecha de las operaciones',
        'capital_invertido': 'Monto de capital invertido',
        'ganancias_perdidas_brutas': 'Ganancias o pérdidas brutas'
    }
    missing_cols = [col for col in required_columns if col not in df.columns]

    if missing_cols:
        error_msg = "🚨 Error en los datos - Faltan columnas requeridas:\n"
        for col in missing_cols:
            error_msg += f"- {col} ({required_columns[col]}) Nombres alternativos aceptados: ganancias, perdidas, resultado, profit\n"
        error_msg += f"\n📋 Columnas disponibles en tu archivo: {', '.join(df.columns.tolist())}"
        return False, error_msg

    try:
        df['fecha'] = pd.to_datetime(df['fecha'])
        df['capital_invertido'] = pd.to_numeric(df['capital_invertido'], errors='coerce')
        df['ganancias_perdidas_brutas'] = pd.to_numeric(df['ganancias_perdidas_brutas'], errors='coerce')
        return True, "✅ Datos validados correctamente"
    except Exception as e:
        return False, f"❌ Error en tipos de datos: {str(e)}\n\nTipos actuales:\n{df.dtypes}"

def calculate_kpis(df):
    capital_inicial = df['capital_invertido'].iloc[0]
    capital_actual = df['capital_invertido'].iloc[-1]
    delta_capital = capital_actual - capital_inicial
    ganancias_brutas = df['ganancias_perdidas_brutas'].sum()
    retorno = safe_divide(ganancias_brutas, capital_inicial) * 100
    return {
        'capital_inicial': capital_inicial,
        'capital_actual': capital_actual,
        'delta_capital': delta_capital,
        'ganancias_brutas': ganancias_brutas,
        'retorno': retorno
    }

def show_kpis(kpis):
    st.markdown("### 📌 KPIs Principales")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Capital Inicial", f"${kpis['capital_inicial']:,.2f}")
    col2.metric("Capital Actual", f"${kpis['capital_actual']:,.2f}", delta=f"{kpis['delta_capital']:,.2f}")
    col3.metric("Ganancias Brutas", f"${kpis['ganancias_brutas']:,.2f}")
    col4.metric("ROI", f"{kpis['retorno']:.2f}%")

def show_charts(df):
    st.markdown("### 📈 Visualización")
    fig1 = px.line(df, x='fecha', y='capital_invertido', title='Evolución del Capital Invertido', template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)

    fig2 = px.bar(
        df,
        x='fecha',
        y='ganancias_perdidas_brutas',
        title='Ganancias/Pérdidas Brutas por Periodo',
        color='ganancias_perdidas_brutas',
        color_continuous_scale=px.colors.diverging.RdYlGn,
        template="plotly_dark"
    )
    st.plotly_chart(fig2, use_container_width=True)

# =============================================
# INTERFAZ PRINCIPAL
# =============================================

def main():
    st.title("📊 Dashboard Financiero Fallone Investments")
    uploaded_file = st.file_uploader("📤 Subir archivo Excel", type=['xlsx', 'xls'])

    if uploaded_file is not None:
        try:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            selected_sheet = st.selectbox("📋 Seleccionar hoja", sheet_names)

            @st.cache_data
            def load_data(file, sheet):
                df = pd.read_excel(file, sheet_name=sheet)
                df = normalize_column_names(df)
                return df.loc[:, ~df.columns.duplicated()]

            df = load_data(uploaded_file, selected_sheet)

            is_valid, validation_msg = validate_dataframe(df)
            if not is_valid:
                st.error(validation_msg)
                st.stop()

            st.success("✅ Archivo cargado y validado correctamente.")
            kpis = calculate_kpis(df)
            show_kpis(kpis)
            show_charts(df)

            with st.expander("📋 Ver tabla de datos"):
                st.dataframe(df)

        except Exception as e:
            st.error(f"❌ Error al procesar el archivo: {str(e)}")
    else:
        st.info("👋 Por favor, sube un archivo Excel para comenzar")

if __name__ == "__main__":
    main()

