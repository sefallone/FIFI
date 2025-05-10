import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# ... (Configuración inicial y carga de archivo se mantiene igual)

if uploaded_file is not None:
    try:
        # ... (Sección de KPIs y metadatos se mantiene igual)

        # =================================================================
        # --- 🆕 SECCIÓN ACTUALIZADA: PROYECCIÓN ACUMULATIVA ---
        # =================================================================
        st.markdown("---")
        st.subheader("🚀 Proyección Acumulativa de Capital")

        # Widgets para configuración
        col4, col5, col6 = st.columns(3)
        
        with col4:
            annual_rate = st.slider(
                "Tasa de crecimiento anual (%)", 
                min_value=0.0, 
                max_value=50.0, 
                value=10.0, 
                step=0.5
            )
        
        with col5:
            initial_capital = st.number_input(
                "Capital inicial ($)", 
                min_value=0.0, 
                value=float(df["Capital Invertido"].iloc[-1]) if "Capital Invertido" in df.columns else 10000.0, 
                step=1000.0
            )
        
        with col6:
            additional_capital = st.number_input(
                "Aumento Capital adicional anual ($)", 
                min_value=0.0, 
                value=5000.0, 
                step=1000.0
            )

        # Función de proyección acumulativa (¡Nueva lógica!)
        def calculate_accumulative_projection(initial, rate, periods, extra_capital=0):
            rate_monthly = rate / 100 / 12  # Tasa mensual
            dates = []
            capital = []
            ganancias_netas = []
            aumento_capital = []
            
            current_capital = initial
            for month in range(periods + 1):
                dates.append(datetime.now() + timedelta(days=30*month))
                
                # Añadir capital adicional al inicio de cada año
                if month % 12 == 0 and month != 0:
                    current_aumento = extra_capital
                else:
                    current_aumento = 0
                
                # Calcular ganancias netas (interés compuesto)
                current_ganancias = current_capital * rate_monthly
                
                # Actualizar capital (Capital anterior + Aumento + Ganancias)
                current_capital += current_aumento + current_ganancias
                
                # Guardar valores
                capital.append(current_capital)
                ganancias_netas.append(current_ganancias)
                aumento_capital.append(current_aumento)
            
            return pd.DataFrame({
                'Fecha': dates,
                'Capital Invertido': capital,
                'Ganancias Netas': ganancias_netas,
                'Aumento Capital': aumento_capital,
                'Escenario': 'Base' if extra_capital == 0 else f'Con +${extra_capital:,.0f}/año'
            })

        # Calcular ambos escenarios
        projection_base = calculate_accumulative_projection(initial_capital, annual_rate, 36)  # 3 años
        projection_extra = calculate_accumulative_projection(initial_capital, annual_rate, 36, additional_capital)

        # Combinar resultados
        df_projection = pd.concat([projection_base, projection_extra])

        # ---- Resultados ----
        tab1, tab2 = st.tabs(["📈 Gráfico", "📊 Detalle Mensual"])

        with tab1:
            # Gráfico evolutivo
            fig = px.line(
                df_projection, 
                x='Fecha', 
                y='Capital Invertido', 
                color='Escenario',
                title='Evolución del Capital Invertido',
                labels={'Capital Invertido': 'Valor ($)'},
                hover_data=['Ganancias Netas', 'Aumento Capital']
            )
            st.plotly_chart(fig, use_container_width=True)

            # Resumen comparativo
            st.subheader("🔍 Resumen al final del período")
            final_values = df_projection.groupby('Escenario').last().reset_index()
            final_values['Diferencia'] = final_values['Capital Invertido'] - final_values['Capital Invertido'].shift(1)
            
            col7, col8 = st.columns(2)
            with col7:
                st.metric(
                    "Capital Base (3 años)",
                    f"${final_values.iloc[0]['Capital Invertido']:,.2f}",
                    delta=f"Ganancias: ${final_values.iloc[0]['Ganancias Netas']:,.2f}/mes"
                )
            
            with col8:
                st.metric(
                    "Con Aumento Capital",
                    f"${final_values.iloc[1]['Capital Invertido']:,.2f}",
                    delta=f"+${final_values.iloc[1]['Diferencia']:,.2f} vs base"
                )

        with tab2:
            # Tabla detallada
            st.dataframe(
                df_projection.style.format({
                    'Fecha': lambda x: x.strftime('%Y-%m-%d'),
                    'Capital Invertido': '${:,.2f}',
                    'Ganancias Netas': '${:,.2f}',
                    'Aumento Capital': '${:,.2f}'
                }),
                height=500
            )

        # ... (El resto del dashboard se mantiene igual)

    except Exception as e:
        st.error(f"Error: {str(e)}")
else:
    st.info("👋 Sube un archivo Excel para comenzar")













