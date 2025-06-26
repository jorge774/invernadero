# -*- coding: utf-8 -*-
# MQTT subscriber parametrizado

import paho.mqtt.client as mqtt
import pandas as pd
from datetime import datetime
import threading
import time
import os

# === Configuración MQTT ===
BROKER = "test.mosquitto.org"
PORT = 1883
INTERVALO = 300  # 5 minutos

# === Configuracion almacenamiento datos=====
BASE_PATH="datos/lidera"

# Mapeo de tópicos a claves en el buffer
TOPIC_MAP = {
    "sensor/temperatura": "temperatura",
    "sensor/AireH": "AireH",
    "sensor/SueloH": "SueloH",
    "sensor/Pres": "Pres",
    "sensor/Co2": "Co2",
    "sensor/Lu": "Lu"
}
TOPICS = [(topic, 0) for topic in TOPIC_MAP]  # Suscripciones

columnas = ["timestamp", "temperatura", "humedad_aire", "humedad_suelo", "presion", "co2", "lumenes"]
claves_esperadas = list(TOPIC_MAP.values())
data_buffer = {}
ultimo_guardado = 0

def get_csv_filename(BASE_PATH):
    fecha = datetime.now().strftime("%Y%m%d")
    return f"{BASE_PATH}/{fecha}.csv"

# === Funciones MQTT ===
def on_connect(client, userdata, flags, rc):
    for topic, qos in TOPICS:
        client.subscribe(topic)

def on_message(client, userdata, msg):
    nonlocal_vars = globals()
    nonlocal_vars['ultimo_guardado']

    timestamp = datetime.now().isoformat(timespec='seconds')
    topic = msg.topic
    value = msg.payload.decode("utf-8")

    print(f"Received message on topic {topic}: {value}")

    # Guardar timestamp y valor si el tópico es esperado
    if topic in TOPIC_MAP:
        data_buffer["timestamp"] = timestamp
        try:
            data_buffer[TOPIC_MAP[topic]] = float(value)
        except ValueError:
            print(f"⚠️ Error de conversión en el tópico {topic} con valor '{value}'")
            return

    completo = all(clave in data_buffer and data_buffer[clave] not in [None, "", "null"] for clave in claves_esperadas)
    ahora = time.time()

    if completo:
        if (ahora - nonlocal_vars['ultimo_guardado']) >= INTERVALO:
            csv_file = get_csv_filename(BASE_PATH)
            os.makedirs(os.path.dirname(csv_file), exist_ok=True)
            if not os.path.exists(csv_file):
                with open(csv_file, "w") as f:
                    f.write(",".join(columnas) + "\n")
            with open(csv_file, "a") as f:
                fila = f"{data_buffer['timestamp']}," \
                       f"{data_buffer['temperatura']}," \
                       f"{data_buffer['AireH']}," \
                       f"{data_buffer['SueloH']}," \
                       f"{data_buffer['Pres']}," \
                       f"{data_buffer['Co2']}," \
                       f"{data_buffer['Lu']}\n"
                f.write(fila)
            nonlocal_vars['ultimo_guardado'] = ahora
        data_buffer.clear()

def start_mqtt_listener():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()

start_mqtt_listener()

