# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
st.subheader("📌 Última medición")
# Cargar los datos
CSV_FILE = "datosInvernadero.csv"
try:
    df = pd.read_csv(CSV_FILE, parse_dates=["timestamp"])
    st.success("📁 Archivo CSV cargado correctamente.")
    # Tomar la última fila
    ultima = df.iloc[-1]
except FileNotFoundError:
    st.warning("⚠️ Aún no hay datos registrados.")
    st.stop()
# Crear columnas para mostrar datos como tarjetas
a, b = st.columns(2)
c, d = st.columns(2)
e, f= st.columns(2)

a.metric(label="🌡️ Temp (°C)",value=f"{ultima['temperatura']:.1f}",border=True)
b.metric(label="💧 Humedad en aire (%)",value=f"{ultima['humedad_aire']:.1f}",border=True)
c.metric(label="🌱 Humedad en suelo (%)", value=f"{ultima['humedad_suelo']:.1f}",border=True)
d.metric(label="📈 Presión (kPa)",value=f"{ultima['presion']:.1f}",border=True)
e.metric(label="🟢 CO₂ (ppm)",value=f"{ultima['co2']:.0f}",border=True)
f.metric(label="💡 Luminosidad (Lumenes)",value=f"{ultima['lumenes']:.0f}",border=True)
