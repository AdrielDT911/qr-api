from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import qrcode
from io import BytesIO
import base64
import random

# App FastAPI
app = FastAPI()
cdc_storage = {}  # Almacén temporal para cdc_id

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos
class CDCRequest(BaseModel):
    qr_id: int
    cdc_id: str

# Endpoint para generar el QR (sin parámetros innecesarios)
@app.post("/qr/generador")
def generar_qr():
    try:
        qr_id = random.randint(1, 999999)

        # URL con el qr_id solamente
        qr_data = f"https://adrieldt911.github.io/ScanWeb/?qr_id={qr_id}"

        # Crear el código QR
        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_bytes = buffer.getvalue()

        return {
            "qr": base64.b64encode(qr_bytes).decode(),
            "url": qr_data,
            "qr_id": qr_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando QR: {str(e)}")

# Endpoint para guardar el CDC
@app.post("/qr/guardar-cdc")
def guardar_cdc(request: CDCRequest):
    try:
        cdc_storage[request.qr_id] = request.cdc_id
        return {"status": "ok", "message": f"CDC_ID '{request.cdc_id}' recibido para QR_ID {request.qr_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recibiendo CDC_ID: {str(e)}")

# Endpoint para verificar el CDC
@app.get("/qr/verificar-cdc")
def verificar_cdc(qr_id: int = Query(...)):
    try:
        if qr_id in cdc_storage:
            return {"cdc_id": cdc_storage[qr_id]}
        else:
            return {"cdc_id": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verificando CDC_ID: {str(e)}")
