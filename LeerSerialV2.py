import os
import serial
import time
import pandas as pd
from datetime import datetime

# === Configuración del puerto serial ===
port = "/dev/ttyACM0"
baudrate = 9600
ser = serial.Serial(port, baudrate, timeout=2)

# === Columnas del CSV ===
columnas = ["timestamp", "temperatura", "humedad_aire", "humedad_suelo", "presion", "co2", "lumenes"]

# === Carpeta de salida para CSVs ===
CSV_FOLDER = "datos"
os.makedirs(CSV_FOLDER, exist_ok=True)

# === Función para obtener nombre del archivo CSV en carpeta especificada ===
def obtener_nombre_csv(folder_path):
    fecha_actual = datetime.now().strftime("%Y%m%d")
    return os.path.join(folder_path, f"{fecha_actual}.csv")

# === Función para abrir CSV y escribir encabezado si es nuevo ===
def abrir_archivo_csv(nombre_archivo):
    existe = os.path.exists(nombre_archivo)
    f = open(nombre_archivo, "a")
    if not existe:
        f.write(",".join(columnas) + "\n")
    return f

# === Inicialización ===
ultimo_minuto = None
fecha_actual = datetime.now().date()
csv = obtener_nombre_csv(CSV_FOLDER)
f = abrir_archivo_csv(csv)

print(f"✅ Grabando en {csv}... (Ctrl+C para detener)")

# === Loop de adquisición ===
try:
    while True:
        linea = ser.readline().decode(errors='ignore').strip()
        datos_i = linea.split(",")

        if len(datos_i) == len(columnas) - 1:
            ahora = datetime.now().replace(second=0, microsecond=0)
            if ahora != ultimo_minuto:
                tstamp = ahora.isoformat()
                f.write(f"{tstamp},{linea}\n")
                f.flush()
                print(f"{tstamp},{linea}")
                ultimo_minuto = ahora

        # Nuevo día → cambiar de archivo
        nueva_fecha = datetime.now().date()
        if nueva_fecha != fecha_actual:
            f.close()
            fecha_actual = nueva_fecha
            csv = obtener_nombre_csv(CSV_FOLDER)
            f = abrir_archivo_csv(csv)
            print(f"\n🕛 Nuevo día detectado. Grabando en nuevo archivo: {csv}")

        time.sleep(1)

except KeyboardInterrupt:
    print("\n🛑 Grabación detenida por el usuario.")
finally:
    f.close()
    ser.close()
