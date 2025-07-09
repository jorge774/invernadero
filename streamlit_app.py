# -*- coding: utf-8 -*-
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

# Diccionario que mapea tópicos MQTT a columnas CSV
TOPIC_MAP = {
    "sensor/temperatura": "temperatura",
    "sensor/AireH": "humedad_aire",
    "sensor/SueloH": "humedad_suelo",
    "sensor/Pres": "presion",
    "sensor/Co2": "co2",
    "sensor/Lu": "lumenes"
}
TOPICS = [(topic, 0) for topic in TOPIC_MAP.keys()]
columnas = ["timestamp"] + list(TOPIC_MAP.values())
claves_esperadas = list(TOPIC_MAP.values())
CACHE_FILE = "cache.csv"
data_buffer = {}
ini_cache = ["0" for _ in columnas]

# === Configuración de endpoint remoto ===
END_POINT = "https://england-amounts-identify-sherman.trycloudflare.com/"

# === Crear archivo CSV si no existe ===
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
    topic = msg.topic
    value = msg.payload.decode("utf-8")

    data_buffer["timestamp"] = timestamp

    if topic in TOPIC_MAP:
        clave = TOPIC_MAP[topic]
        try:
            data_buffer[clave] = float(value)
        except ValueError:
            print(f"⚠️ Error al convertir valor de {topic}: {value}")
            return

    completo = all(clave in data_buffer and data_buffer[clave] not in [None, "", "null"] for clave in claves_esperadas)
    if completo:
        with open(CACHE_FILE, "r") as f:
            content = f.readlines()
        fila = ",".join(str(data_buffer.get(col, "")) for col in columnas) + "\n"
        content[-1] = fila
        with open(CACHE_FILE, "w") as f:
            f.writelines(content)
        data_buffer.clear()

def start_mqtt_listener():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()

# === Lanzar hilo MQTT ===
if 'mqtt_started' not in st.session_state:
    threading.Thread(target=start_mqtt_listener, daemon=True).start()
    st.session_state['mqtt_started'] = True

# === Interfaz ===
st.set_page_config(
    page_title="Invernadero Inteligente",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("🌿 Dashboard de Invernadero")

with st.container():
    st_autorefresh(interval=300000, key="dashboard_refresh", limit=None)
    st.subheader("🌿 Datos en tiempo real (refresca cada 5 minutos)")

    def fila_es_cero(fila):
        return fila.drop(labels=["timestamp"]).eq(0).all()

    try:
        df = pd.read_csv(CACHE_FILE, parse_dates=["timestamp"])
        ultima = df.iloc[-1]
        if fila_es_cero(ultima):
            st.warning("⚠️ La última medición contiene solo ceros. Verifica si los sensores están funcionando.")
            st.stop()
        st.success("📁 Esperando datos para ser procesados.")
    except Exception:
        st.warning("⚠️ Error al leer el archivo CSV de cache.")
        st.stop()

    a, b = st.columns(2)
    c, d = st.columns(2)
    e, f = st.columns(2)
    a.metric(label="🌡️ Temp (°C)", value=f"{ultima['temperatura']:.1f}", border=True)
    b.metric(label="💧 Humedad aire (%)", value=f"{ultima['humedad_aire']:.1f}", border=True)
    c.metric(label="🌱 Humedad suelo (ADC)", value=f"{ultima['humedad_suelo']:.1f}", border=True)
    d.metric(label="📈 Presión (kPa)", value=f"{ultima['presion']:.1f}", border=True)
    e.metric(label="🟢 CO₂ (ppm)", value=f"{ultima['co2']:.0f}", border=True)
    f.metric(label="💡 Lumenes", value=f"{ultima['lumenes']:.0f}", border=True)

# === Descarga de CSV remoto ===
st.markdown("---")
st.subheader("📅 Descargar CSV histórico desde servidor remoto")

fecha_seleccionada = st.date_input("Selecciona la fecha de los datos que quieres descargar")
fecha_str = fecha_seleccionada.strftime("%Y%m%d")
csv_url = f"{END_POINT}{fecha_str}.csv"

try:
    df_remoto = pd.read_csv(csv_url)
    st.success("✅ Archivo cargado correctamente desde el repositorio.")
    st.dataframe(df_remoto, use_container_width=True)
    csv_bytes = df_remoto.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar CSV", data=csv_bytes, file_name=f"datosInvernadero_{fecha_str}.csv", mime="text/csv")
except Exception as e:
    st.warning(f"⚠️ No se pudo cargar el archivo para {fecha_str}. Verifica si el invernadero adquirió datos en esa fecha.")
################################### Visualización interactiva ####################################################
# st.markdown("---")
# st.subheader("📈 Visualización interactiva de variables")

# if 'df_remoto' in locals():
#     opciones = {
#         "🌡️ Temperatura (°C)": "temperatura",
#         "💧 Humedad en aire (%)": "humedad_aire",
#         "🌱 Humedad en suelo (%)": "humedad_suelo",
#         "📈 Presión (kPa)": "presion",
#         "🟢 CO₂ (ppm)": "co2",
#         "💡 Lumenes": "lumenes"
#     }

#     variable = st.selectbox("Selecciona la variable a graficar:", list(opciones.keys()))
#     nombre_columna = opciones[variable]

#     try:
#         # Asegurar que timestamp esté como índice de tiempo
#         df_remoto["timestamp"] = pd.to_datetime(df_remoto["timestamp"])
#         df_remoto = df_remoto.sort_values("timestamp")
#         df_remoto.set_index("timestamp", inplace=True)

#         st.line_chart(df_remoto[[nombre_columna]])

#     except Exception as e:
#         st.warning("⚠️ No se pudo graficar la variable seleccionada.")
#         st.text(f"Error: {e}")
# else:
#     st.info("ℹ️ Primero asegurate de tener el csv con datos historicos.")





