# -*- coding: utf-8 -*-
import streamlit as st

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
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("🌡️ Temp (°C)", f"{ultima['temperatura']:.1f}")
col2.metric("💧 Humedad en aire (%)", f"{ultima['humedad_aire']:.1f}")
col3.metric("🌱 Humedad en suelo (%)", f"{ultima['humedad_suelo']:.1f}")
col4.metric("📈 Presión (kPa)", f"{ultima['presion']:.1f}")
col5.metric("🟢 CO₂ (ppm)", f"{ultima['co2']:.0f}")
col6.metric("💡 Luminosidad (Lumenes)", f"{ultima['lumenes']:.0f}")
