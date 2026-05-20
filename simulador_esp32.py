import asyncio
import random
import requests
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Simulador ESP32")
API_PRINCIPAL = "http://127.0.0.1:8000/api/lecturas"

estado_hardware = {
    "luces": "OFF",
    "extractor": "OFF",
    "riego": "OFF"
}

class Comando(BaseModel):
    actuador: str
    orden: str

# 1. Separamos el envío de datos en su propia función para poder llamarla cuando queramos
def forzar_actualizacion_bd():
    datos = {
        "luz_valor": round(random.uniform(40.0, 95.0), 1),
        "luz_estado": "Encendido" if estado_hardware["luces"] == "ON" else "Apagado",
        "temp_aire": round(random.uniform(22.0, 30.0), 1),
        "hum_aire": round(random.uniform(50.0, 70.0), 1),
        "extractor_estado": "Activo" if estado_hardware["extractor"] == "ON" else "Inactivo",
        "hum_suelo": round(random.uniform(20.0, 60.0), 1),
        "riego_estado": "Activo" if estado_hardware["riego"] == "ON" else "Inactivo"
    }
    try:
        requests.post(API_PRINCIPAL, json=datos)
    except requests.exceptions.RequestException:
        pass

# 2. Cuando Android manda una orden, actualizamos la memoria Y la Base de Datos INMEDIATAMENTE
@app.post("/control")
def recibir_orden(comando: Comando):
    print(f"\n📡 [NUEVA ORDEN] -> {comando.actuador} cambiar a: {comando.orden}")
    if comando.actuador in estado_hardware:
        estado_hardware[comando.actuador] = comando.orden
        
        # ¡LA MAGIA!: Le avisamos a la BD en ese exacto milisegundo, sin esperar.
        forzar_actualizacion_bd()
        print("⚡ Estado actualizado en la Base de Datos al instante.")
        
    return {"status": "ok"}

# 3. El ciclo normal sigue corriendo por si los sensores cambian por el clima
async def enviar_datos_sensores():
    while True:
        await asyncio.sleep(5)
        forzar_actualizacion_bd()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(enviar_datos_sensores())

if __name__ == "__main__":
    print("🚀 ESP32 Simulado Iniciado en puerto 8080...")
    uvicorn.run(app, host="0.0.0.0", port=8080)
