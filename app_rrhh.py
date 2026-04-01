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

# Función inteligente para formatear Valores (Horas vs Moneda)
def dar_formato(columna, valor):
    if 'horas' in columna.lower():
        # Formato para horas: respeta 1 decimal y usa 'hrs'
        formateado = f"{valor:.1f}".replace('.', ',')
        if formateado.endswith(',0'):
            formateado = formateado[:-2] # Quitar el ,0 si es entero
        return f"{formateado} hrs"
    else:
        # Formato para moneda: sin decimales, con $ y puntos separadores de miles
        return f"${int(valor):,}".replace(',', '.')

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
        
        if not set(id_cols).issubset(df_anterior.columns) or not set(id_cols).issubset(df_actual
