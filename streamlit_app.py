# -*- coding: utf-8 -*-
# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import paho.mqtt.client as mqtt
import threading
import time
import os

# === Configuración MQTT ===
BROKER = "test.mosquitto.org"
PORT = 1883
TOPICS = [("sensor/temperatura",0),("sensor/AireH",0),("sensor/SueloH",0),("sensor/Pres",0),("sensor/Co2",0),("sensor/Lu",0)]
CSV_FILE = "datosInvernadero.csv"
CACHE_FILE = "cache.csv"
INTERVALO = 300  # 5 minutos
columnas = ["timestamp","temperatura", "humedad_aire", "humedad_suelo", "presion", "co2", "lumenes"]
claves_esperadas = ["temperatura", "AireH", "SueloH", "Pres", "Co2", "Lu"]
data_buffer = {}
ultimo_guardado = 0

# Crear archivo CSV si no existe
try:
    open(CSV_FILE, "r")
except FileNotFoundError:
    with open(CSV_FILE, "w") as f:
        f.write(",".join(columnas) + "\n")

# Crear archivo CSV de cache
try:
    open(CACHE_FILE, "r")
except FileNotFoundError:
    with open(CACHE_FILE, "w") as f:
        f.write(",".join(columnas) + "\n")
    with open(CACHE_FILE, "a") as f:
        f.write(",".join(columnas) + "\n") 


# === Funciones MQTT ===
def on_connect(client, userdata, flags, rc):
    for topic, qos in TOPICS:
        client.subscribe(topic)

def on_message(client, userdata, msg):
    nonlocal_vars = globals()
    nonlocal_vars['ultimo_guardado']  # para evitar warning
    timestamp = datetime.now().isoformat(timespec='seconds')
    data_buffer["timestamp"] = timestamp
    topic = msg.topic
    value = msg.payload.decode("utf-8")

    if topic == "sensor/temperatura":
        data_buffer["temperatura"] = float(value)
    elif topic == "sensor/AireH":
        data_buffer["AireH"] = float(value)
    elif topic == "sensor/SueloH":
        data_buffer["SueloH"] = float(value)
    elif topic == "sensor/Pres":
        data_buffer["Pres"] = float(value)
    elif topic == "sensor/Co2":
        data_buffer["Co2"] = float(value)
    elif topic == "sensor/Lu":
        data_buffer["Lu"] = float(value)

    completo = all(clave in data_buffer and data_buffer[clave] not in [None, "", "null"] for clave in claves_esperadas)
    ahora = time.time()
    if completo:
        if (ahora - nonlocal_vars['ultimo_guardado']) >= INTERVALO:
            with open(CSV_FILE, "a") as f:
                f.write(f"{data_buffer['timestamp']},{data_buffer['temperatura']},{data_buffer['AireH']},{data_buffer['SueloH']},{data_buffer['Pres']},{data_buffer['Co2']},{data_buffer['Lu']}\n")
            nonlocal_vars['ultimo_guardado']=ahora
        with open(CACHE_FILE, "r") as f:content=f.readlines()
        content[-1]=(f"{data_buffer['timestamp']},{data_buffer['temperatura']},{data_buffer['AireH']},{data_buffer['SueloH']},{data_buffer['Pres']},{data_buffer['Co2']},{data_buffer['Lu']}\n")       
        with open(CACHE_FILE, "w") as f:f.writelines(content)
        data_buffer.clear()    

def start_mqtt_listener():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()
    
# Iniciar MQTT en hilo separado
if 'mqtt_started' not in st.session_state:
    threading.Thread(target=start_mqtt_listener, daemon=True).start()
    st.session_state['mqtt_started'] = True

# === INTERFAZ STREAMLIT ===

st.set_page_config(
    page_title="Invernadero Inteligente",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("🌿 Dashboard de Invernadero")
st_autorefresh(interval=500, key="refresh")

try:
    df = pd.read_csv(CACHE_FILE, parse_dates=["timestamp"])
    ultima = df.iloc[-1]
    st.success("📁 Archivo CSV cargado correctamente.")
    print(ultima['temperatura'])
except Exception:
    st.warning("⚠️ Aún no hay datos registrados.")
    st.stop()

a, b = st.columns(2)
c, d = st.columns(2)
e, f = st.columns(2)

a.metric(label="🌡️ Temp (°C)", value=f"{ultima['temperatura']:.1f}",border=True)
b.metric(label="💧 Humedad aire (%)",value= f"{ultima['humedad_aire']:.1f}",border=True)
c.metric(label="🌱 Humedad suelo (%)", value=f"{ultima['humedad_suelo']:.1f}",border=True)
d.metric(label="📈 Presión (kPa)", value=f"{ultima['presion']:.1f}",border=True)
e.metric(label="🟢 CO₂ (ppm)", value=f"{ultima['co2']:.0f}",border=True)
f.metric(label="💡 Lumenes",value= f"{ultima['lumenes']:.0f}",border=True)

