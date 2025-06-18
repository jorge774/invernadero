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
CACHE_FILE = "cache.csv"
columnas = ["timestamp","temperatura", "humedad_aire", "humedad_suelo", "presion", "co2", "lumenes"]
ini_cache=[str(0) for _ in columnas]
claves_esperadas = ["temperatura", "AireH", "SueloH", "Pres", "Co2", "Lu"]
data_buffer = {}


# Crear archivo CSV de cache
try:
    open(CACHE_FILE, "r")
except FileNotFoundError:
    with open(CACHE_FILE, "w") as f:
        f.write(",".join(columnas) + "\n")
    with open(CACHE_FILE, "a") as f:
        f.write(",".join(ini_cache) + "\n")


# === Funciones MQTT ===
def on_connect(client, userdata, flags, rc):
    for topic, qos in TOPICS:
        client.subscribe(topic)

def on_message(client, userdata, msg):
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
    if completo:
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
def fila_es_cero(fila):
    return fila.drop(labels=["timestamp"]).eq(0).all()

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
    if fila_es_cero(ultima):
        st.warning("⚠️ La última medición contiene solo ceros. Verifica si los sensores están funcionando.")
        st.stop()
    st.success("📁 Esperando datos para ser procesados.")
except Exception:
    st.warning("⚠️ Ha ocurrido un error al tratar almacenar datos entrantes.")
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

####################################Descargar datos########################################################################
st.markdown("---")
st.subheader("📅 Descargar CSV histórico desde servidor remoto")

# Selección de fecha
fecha_seleccionada = st.date_input("Selecciona la fecha de los datos que quieres descargar")

# Construir URL al archivo remoto
fecha_str = fecha_seleccionada.strftime("%Y%m%d")
csv_url = f"https://med-bag-undertaken-cyber.trycloudflare.com/{fecha_str}.csv"

# Descargar el CSV remoto
try:
    df_remoto = pd.read_csv(csv_url)
    st.success(f"✅ Archivo cargado correctamente desde el repositorio.")

    st.dataframe(df_remoto, use_container_width=True)

    # Preparar archivo para descarga
    csv_bytes = df_remoto.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar CSV", data=csv_bytes, file_name=f"datosInvernadero_{fecha_str}.csv", mime="text/csv")

except Exception as e:
    st.warning(f"⚠️ No se pudo cargar el archivo para {fecha_str}. Verifica si el invernadero adquirió datos en esa fecha.")
    #st.text(f"Detalles técnicos: {e}")


################################### Visualización interactiva ####################################################
st.markdown("---")
st.subheader("📈 Visualización interactiva de variables")

if 'df_remoto' in locals():
    opciones = {
        "🌡️ Temperatura (°C)": "temperatura",
        "💧 Humedad en aire (%)": "humedad_aire",
        "🌱 Humedad en suelo (%)": "humedad_suelo",
        "📈 Presión (kPa)": "presion",
        "🟢 CO₂ (ppm)": "co2",
        "💡 Lumenes": "lumenes"
    }

    variable = st.selectbox("Selecciona la variable a graficar:", list(opciones.keys()))
    nombre_columna = opciones[variable]

    try:
        # Asegurar que timestamp esté como índice de tiempo
        df_remoto["timestamp"] = pd.to_datetime(df_remoto["timestamp"])
        df_remoto = df_remoto.sort_values("timestamp")
        df_remoto.set_index("timestamp", inplace=True)

        st.line_chart(df_remoto[[nombre_columna]])

    except Exception as e:
        st.warning("⚠️ No se pudo graficar la variable seleccionada.")
        #st.text(f"Error: {e}")
else:
    st.info("ℹ️ No se puede acceder al repositorio con los datos historicos.")



