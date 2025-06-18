# -*- coding: utf-8 -*-
# MQTT suscriber

import paho.mqtt.client as mqtt
import pandas as pd
from datetime import datetime
import threading
import time
import os

# === Configuración MQTT ===
BROKER = "test.mosquitto.org"
PORT = 1883
TOPICS = [("sensor/temperatura",0),("sensor/AireH",0),("sensor/SueloH",0),("sensor/Pres",0),("sensor/Co2",0),("sensor/Lu",0)]
INTERVALO = 300  # 5 minutos
columnas = ["timestamp","temperatura", "humedad_aire", "humedad_suelo", "presion", "co2", "lumenes"]
ini_cache=[str(0) for _ in columnas]
claves_esperadas = ["temperatura", "AireH", "SueloH", "Pres", "Co2", "Lu"]
data_buffer = {}
ultimo_guardado=0

def get_csv_filename():
    fecha = datetime.now().strftime("%Y%m%d")
    return f"datos/lidera/{fecha}.csv"

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
    print(f"Received message on topic {topic}: {value}")
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
        if (ahora-nonlocal_vars['ultimo_guardado'])>=INTERVALO:
            csv_file = get_csv_filename()
            # Crear archivo con encabezado si no existe aún
            if not os.path.exists(csv_file):
                with open(csv_file, "w") as f:
                    f.write(",".join(columnas)+"\n")
            with open(csv_file, "a") as f:
                f.write(f"{data_buffer['timestamp']},{data_buffer['temperatura']},{data_buffer['AireH']},{data_buffer['SueloH']},{data_buffer['Pres']},{data_buffer['Co2']},{data_buffer['Lu']}\n")
            nonlocal_vars['ultimo_guardado']=ahora 
        data_buffer.clear()

def start_mqtt_listener():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()
    
# Iniciar MQTT en hilo separado
#if 'mqtt_started' not in st.session_state:
    #threading.Thread(target=start_mqtt_listener, daemon=True).start()
    #st.session_state['mqtt_started'] = True
start_mqtt_listener()
