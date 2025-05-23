# -*- coding: utf-8 -*-
import paho.mqtt.client as mqtt
import pandas as pd
from datetime import datetime
import time
# === Configuración ===
BROKER = "test.mosquitto.org"  # Puedes usar el tuyo
PORT = 1883
TOPICS = [("sensor/temperatura",0),("sensor/AireH",0),("sensor/SueloH",0),("sensor/Pres",0),("sensor/Co2",0),("sensor/Lu",0)]
CSV_FILE = "datosInvernadero.csv"
ultimo_guardado = 0  # en segundos desde epoch
INTERVALO = 300  # 5 minutos = 300 segundos
# Lista de nombres de columnas
columnas=["timestamp","temperatura", "humedad_aire", "humedad_suelo", "presion", "co2", "lumenes"]
claves_esperadas = ["temperatura", "AireH", "SueloH", "Pres", "Co2", "Lu"]
# === Archivo CSV ===
with open(CSV_FILE,"w") as f:f.write(",".join(columnas)+"\n")
# === Buffer en memoria ===
data_buffer={}
# === Callback cuando se conecta al broker ===
def on_connect(client,userdata,flags,rc):
    print(f"Conectado con código {rc}")
    for topic, qos in TOPICS:
        client.subscribe(topic)
        print(f"Suscrito a: {topic}")

# === Callback cuando llega un mensaje ===
def on_message(client, userdata, msg):
    global ultimo_guardado
    timestamp = datetime.now().isoformat(timespec='seconds')
    data_buffer["timestamp"]=timestamp
    topic = msg.topic
    payload = msg.payload.decode("utf-8")

    #print(f"[{timestamp}] {topic}: {payload}")

    # Guardar en buffer en memoria
    #data_buffer.append({"timestamp": timestamp, "topic": topic, "value": payload})

    topic = msg.topic
    value = msg.payload.decode("utf-8")

    #print(str(timestamp)+"#"+str(topic)+"#"+str(value))
    if topic == "sensor/temperatura":
        temperatura = float(value)
        data_buffer["temperatura"]=temperatura
    if topic == "sensor/AireH":
        AireH = float(value)
        data_buffer["AireH"]=AireH
    if topic == "sensor/SueloH":
        SueloH = float(value)
        data_buffer["SueloH"]=SueloH
    if topic == "sensor/Pres":
        Pres = float(value)
        data_buffer["Pres"]=Pres
    if topic == "sensor/Co2":
        Co2 = float(value)
        data_buffer["Co2"]=Co2
    if topic == "sensor/Lu":
        Lu = float(value)
        data_buffer["Lu"]=Lu
    # Verificamos si todas existen y no están vacías
    completo = all(
        clave in data_buffer and data_buffer[clave] not in [None, "", "null"]
        for clave in claves_esperadas
    )
    # Guardar en archivo CSV
    ahora = time.time()
    if completo and (ahora-ultimo_guardado) >= INTERVALO:
        with open(CSV_FILE, "a") as f:
            #f.write(f"{timestamp},{temperatura},{AireH},{SueloH},{Pres},{Co2},{Lu}\n")
            f.write(f"{data_buffer['timestamp']},{data_buffer['temperatura']},{data_buffer['AireH']},{data_buffer['SueloH']},{data_buffer['Pres']},{data_buffer['Co2']},{data_buffer['Lu']}\n")
        ultimo_guardado = ahora
        data_buffer.clear()
# === Cliente MQTT ===
def start_mqtt_listener():
    client=mqtt.Client()
    client.on_connect=on_connect
    client.on_message=on_message
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()
start_mqtt_listener()
