import streamlit as st
import pandas as pd
import numpy as np
import io
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuración de la página y Estilos
st.set_page_config(page_title="Control de Remuneraciones", layout="wide")

estilo_corporativo = """
    <style>
    html, body, [class*="css"] {
        font-family: 'Times New Roman', Times, serif;
    }
    .titulo-principal {
        color: #800020; /* Burdeo */
        text-align: center;
        font-size: 3em;
        font-weight: bold;
    }
    .subtitulo {
        color: #808080; /* Gris */
        text-align: center;
        font-size: 1.5em;
        font-style: italic;
        margin-bottom: 30px;
    }
    .stButton>button {
        background-color: #008000; /* Verde */
        color: white;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #006400; /* Verde oscuro */
    }
    </style>
"""
st.markdown(estilo_corporativo, unsafe_allow_html=True)

st.markdown('<div class="titulo-principal">Control de Remuneraciones y KPIs</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">CONSTRUYENDO FUTURO</div>', unsafe_allow_html=True)

st.write("Sube los archivos Excel (.xlsx) de Talana para analizar variaciones, ver KPIs globales y descargar el detalle.")

# 2. Carga de Archivos
col1, col2 = st.columns(2)
with col1:
    archivo_mes_anterior = st.file_uploader("Sube el archivo del Mes Anterior (Excel)", type=['xlsx'])
with col2:
    archivo_mes_actual = st.file_uploader("Sube el archivo del Mes Actual (Excel)", type=['xlsx'])

if archivo_mes_anterior is not None and archivo_mes_actual is not None:
    try:
        df_anterior = pd.read_excel(archivo_mes_anterior)
        df_actual = pd.read_excel(archivo_mes_actual)

        common_cols = set(df_anterior.columns).intersection(set(df_actual.columns))
        id_cols = ['Rut', 'Trabajador', 'Código de Contrato']
        
        if not set(id_cols).issubset(df_anterior.columns) or not set(id_cols).issubset(df_actual.columns):
            st.error("Error: Los archivos no contienen las columnas necesarias ('Rut', 'Trabajador', 'Código de Contrato').")
        else:
            value_cols = [col for col in common_cols if col not in id_cols]

            df_merged = pd.merge(df_anterior, df_actual, on=id_cols, suffixes=('_Ant', '_Act'), how='inner')

            # Convertir a numérico
            for col in value_cols:
                df_merged[f'{col}_Ant'] = pd.to_numeric(df_merged[f'{col}_Ant'], errors='coerce').fillna(0).astype(int)
                df_merged[f'{col}_Act'] = pd.to_numeric(df_merged[f'{col}_Act'], errors='coerce').fillna(0).astype(int)

            # --- SECCIÓN DE KPIS Y GRÁFICOS (NUEVO) ---
            st.markdown("---")
            st.subheader("📊 Dashboard de Control y Alertas Globales")
            
            # Calcular totales por ítem para ambos meses
            totales_ant = {col: df_merged[f'{col}_Ant'].sum() for col in value_cols}
            totales_act = {col: df_merged[f'{col}_Act'].sum() for col in value_cols}
            
            df_totales = pd.DataFrame({
                'Ítem': value_cols,
                'Mes Anterior': [totales_ant[col] for col in value_cols],
                'Mes Actual': [totales_act[col] for col in value_cols]
            })
            
            # Filtrar ítems que están en cero en ambos meses
            df_totales = df_totales[(df_totales['Mes Anterior'] > 0) | (df_totales['Mes Actual'] > 0)].copy()
            
            # Calcular variación porcentual global
            df_totales['Diferencia $'] = df_totales['Mes Actual'] - df_totales['Mes Anterior']
            df_totales['Variación %'] = np.where(df_totales['Mes Anterior'] == 0, 100, 
                                                (df_totales['Diferencia $'] / df_totales['Mes Anterior']) * 100)
            
            # 1. Mostrar KPIs principales (Ej: Horas Extras, Anticipos y Tratos si existen)
            kpi_cols = st.columns(4)
            items_clave = ['Horas Extra Trabajadas', 'Anticipo Manual', 'Tratos Obra', 'Bono Producción']
            
            idx_kpi = 0
            for item in items_clave:
                if item in df_totales['Ítem'].values:
                    row = df_totales[df_totales['Ítem'] == item].iloc[0]
                    with kpi_cols[idx_kpi % 4]:
                        st.metric(label=f"Total {item}", 
                                  value=f"${row['Mes Actual']:,.0f}".replace(',', '.'), 
                                  delta=f"{row['Variación %']:.1f}% (${row['Diferencia $']:,.0f})".replace(',', '.'))
                    idx_kpi += 1

            # 2. Alertas Críticas (Aumentos globales mayores al 15%)
            st.markdown("### 🚨 Alertas Críticas (Aumento Empresa > 15%)")
            alertas = df_totales[(df_totales['Variación %'] > 15) & (df_totales['Mes Anterior'] > 0)]
            if not alertas.empty:
                for _, alerta in alertas.iterrows():
                    st.warning(f"**{alerta['Ítem']}**: Aumentó un **{alerta['Variación %']:.1f}%** a nivel compañía. Pasó de ${alerta['Mes Anterior']:,.0f} a ${alerta['Mes Actual']:,.0f}.".replace(',', '.'))
            else:
                st.success("No se detectaron aumentos críticos mayores al 15% a nivel empresa este mes.")

            # 3. Gráfico Comparativo
            st.markdown("### 📈 Comparativa de Pagos por Ítem")
            # Preparar datos para el gráfico
            df_melt = df_totales.melt(id_vars=['Ítem'], value_vars=['Mes Anterior', 'Mes Actual'], 
                                      var_name='Mes', value_name='Monto ($)')
            
            fig = px.bar(df_melt, x='Ítem', y='Monto ($)', color='Mes', barmode='group',
                         color_discrete_map={'Mes Anterior': '#808080', 'Mes Actual': '#800020'},
                         title="Comparación de Gastos Totales (Excluye Sueldo Base)")
            fig.update_layout(xaxis_tickangle=-45, font=dict(family="Times New Roman"))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            # --- FIN SECCIÓN KPIS ---

            # --- SECCIÓN DETALLE POR TRABAJADOR ---
            st.subheader("📋 Detalle de Variaciones por Trabajador (> 5%)")
            
            observations = []
            for index, row in df_merged.iterrows():
                obs_list = []
                for col in sorted(value_cols):
                    val_ant = row[f'{col}_Ant']
                    val_act = row[f'{col}_Act']
                    
                    if val_ant == 0 and val_act == 0:
                        continue
                        
                    if val_ant == 0 and val_act != 0:
                        obs_list.append(f"{col} (Nuevo: ${val_act:,})".replace(',', '.'))
                    elif val_ant != 0 and val_act == 0:
                        obs_list.append(f"{col} (Falta, era ${val_ant:,})".replace(',', '.'))
                    else:
                        diff = abs(val_act - val_ant) / abs(val_ant)
                        if diff > 0.05:
                            direction = "Aumentó" if val_act > val_ant else "Disminuyó"
                            obs_list.append(f"{col} ({direction} {(diff*100):.1f}%)")

                observations.append("; ".join(obs_list) if obs_list else "Sin variación > 5%")

            df_merged['Observaciones'] = observations
            
            output_cols = id_cols + ['Observaciones']
            for col in sorted(value_cols):
                output_cols.extend([f'{col}_Ant', f'{col}_Act'])
                
            df_result = df_merged[output_cols]

            ver_solo_desviaciones = st.checkbox("Mostrar solo trabajadores con variaciones")
            if ver_solo_desviaciones:
                df_mostrar = df_result[df_result['Observaciones'] != "Sin variación > 5%"]
            else:
                df_mostrar = df_result

            st.dataframe(df_mostrar, use_container_width=True)

            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_result.to_excel(writer, index=False, sheet_name='Control Variaciones')
            
            st.download_button(
                label="📥 Descargar Reporte en Excel",
                data=buffer.getvalue(),
                file_name="Reporte_Desviaciones_RRHH.xlsx",
                mime="application/vnd.ms-excel"
            )

    except Exception as e:
        st.error(f"Ocurrió un error al procesar los archivos: {e}")
