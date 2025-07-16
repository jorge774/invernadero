import os
import serial
import time
import pandas as pd
from datetime import datetime

# === Configuración del puerto serial ===
port = "/dev/ttyACM0"
baudrate = 9600
ser = serial.Serial(port, baudrate, timeout=1)

# === Columnas del CSV ===
columnas = ["timestamp", "temperatura", "humedad_aire", "humedad_suelo", "presion", "co2", "lumenes"]

# === Carpeta de salida para CSVs ===
CSV_FOLDER = "datos"  # Puedes cambiar esto por la ruta que quieras

# Crear carpeta si no existe
os.makedirs(CSV_FOLDER, exist_ok=True)

# === Función para obtener nombre del archivo CSV en carpeta especificada ===
def obtener_nombre_csv(folder_path):
    fecha_actual = datetime.now().strftime("%Y%m%d")
    return os.path.join(folder_path, f"{fecha_actual}.csv")

# Inicialización
fecha_actual = datetime.now().date()
csv = obtener_nombre_csv(CSV_FOLDER)

# Abrir archivo CSV y escribir encabezado si es nuevo
def abrir_archivo_csv(nombre_archivo):
    existe = os.path.exists(nombre_archivo)
    f = open(nombre_archivo, "a")
    if not existe:
        f.write(",".join(columnas) + "\n")
    return f

f = abrir_archivo_csv(csv)

# === Lectura de datos y guardado continuo ===
print(f"Grabando en {csv}... presiona Ctrl+C para detener.")
try:
    while True:
        linea = ser.readline().decode(errors='ignore').strip()
        datos_i = linea.split(",")

        if len(datos_i) == len(columnas) - 1:
            tstamp = pd.Timestamp(datetime.now()).round(freq='s').isoformat()            
            print(f"{tstamp},{linea}")
            f.write(f"{tstamp},{linea}\n")
            f.flush()

        nueva_fecha = datetime.now().date()
        if nueva_fecha != fecha_actual:
            f.close()
            fecha_actual = nueva_fecha
            csv = obtener_nombre_csv(CSV_FOLDER)
            f = abrir_archivo_csv(csv)
            print(f"\n🕛 Nuevo día detectado. Grabando en nuevo archivo: {csv}")

        time.sleep(300)

except KeyboardInterrupt:
    print("Grabación detenida por el usuario.")
    f.close()
    ser.close()

