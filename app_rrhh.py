import streamlit as st
import pandas as pd
import numpy as np
import io

# 1. Configuración de la página y Estilos Corporativos
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
        font-family: 'Times New Roman', Times, serif;
    }
    .stButton>button:hover {
        background-color: #006400; /* Verde oscuro */
    }
    </style>
"""
st.markdown(estilo_corporativo, unsafe_allow_html=True)

# Encabezado de la App
st.markdown('<div class="titulo-principal">Control de Remuneraciones</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitulo">CONSTRUYENDO FUTURO</div>', unsafe_allow_html=True)

st.write("Sube los archivos Excel (.xlsx) de liquidaciones descargados de Talana para detectar variaciones mayores al 5%, ítems nuevos o faltantes.")

# 2. Carga de Archivos
col1, col2 = st.columns(2)
with col1:
    archivo_mes_anterior = st.file_uploader("Sube el archivo del Mes Anterior (Excel)", type=['xlsx'])
with col2:
    archivo_mes_actual = st.file_uploader("Sube el archivo del Mes Actual (Excel)", type=['xlsx'])

# 3. Lógica de Procesamiento
if archivo_mes_anterior is not None and archivo_mes_actual is not None:
    try:
        # Lectura directa de archivos Excel
        df_anterior = pd.read_excel(archivo_mes_anterior)
        df_actual = pd.read_excel(archivo_mes_actual)

        # Identificar columnas comunes
        common_cols = set(df_anterior.columns).intersection(set(df_actual.columns))
        id_cols = ['Rut', 'Trabajador', 'Código de Contrato']
        
        # Validación de columnas corregida (con 'not')
        if not set(id_cols).issubset(df_anterior.columns) or not set(id_cols).issubset(df_actual.columns):
            st.error("Error: Los archivos no contienen las columnas necesarias ('Rut', 'Trabajador', 'Código de Contrato'). Revisa el formato exportado por Talana.")
        else:
            value_cols = [col for col in common_cols if col not in id_cols]

            # Unir ambos dataframes
            df_merged = pd.merge(df_anterior, df_actual, on=id_cols, suffixes=('_Ant', '_Act'), how='inner')

            # Convertir a numérico
            for col in value_cols:
                df_merged[f'{col}_Ant'] = pd.to_numeric(df_merged[f'{col}_Ant'], errors='coerce').fillna(0).astype(int)
                df_merged[f'{col}_Act'] = pd.to_numeric(df_merged[f'{col}_Act'], errors='coerce').fillna(0).astype(int)

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
            
            # Ordenar columnas para el reporte final
            output_cols = id_cols + ['Observaciones']
            for col in sorted(value_cols):
                output_cols.extend([f'{col}_Ant', f'{col}_Act'])
                
            df_result = df_merged[output_cols]

            st.success("Cruce de datos desde Talana realizado con éxito.")

            # 4. Visualización y Filtros
            st.subheader("Resultados del Análisis")
            
            # Filtro rápido para ver solo los que tienen variaciones
            ver_solo_desviaciones = st.checkbox("Mostrar solo trabajadores con variaciones (Ocultar 'Sin variación > 5%')")
            
            if ver_solo_desviaciones:
                df_mostrar = df_result[df_result['Observaciones'] != "Sin variación > 5%"]
            else:
                df_mostrar = df_result

            st.dataframe(df_mostrar, use_container_width=True)

            # 5. Descarga del archivo final
            # Convertir dataframe a excel en memoria
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
        st.error(f"Ocurrió un error al procesar los archivos de Excel: {e}")
