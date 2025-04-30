from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import qrcode
from io import BytesIO
import base64
import random

# App FastAPI
app = FastAPI()
cdc_storage = {}  # Guardamos los cdc_id temporalmente

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos
class QRRequest(BaseModel):
    app_id: int
    app_user: str
    app_page_id: int

class CDCRequest(BaseModel):
    qr_id: int
    cdc_id: str

# Generar QR
@app.post("/qr/generador")
def generar_qr(request: QRRequest):
    try:
        qr_id = random.randint(1, 999999)  # Generamos primero
        qr_data = (
            f"https://adrieldt911.github.io/ScanWeb/"
            f"?app_id={request.app_id}&app_user={request.app_user}"
            f"&app_page_id={request.app_page_id}&qr_id={qr_id}"
        )

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

# Guardar CDC
@app.post("/qr/guardar-cdc")
def guardar_cdc(request: CDCRequest):
    try:
        # Guardamos el cdc_id asociado al qr_id
        cdc_storage[request.qr_id] = request.cdc_id
        return {"status": "ok", "message": f"CDC_ID '{request.cdc_id}' recibido para QR_ID {request.qr_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recibiendo CDC_ID: {str(e)}")

# Verificars CDC
from fastapi import Query
@app.get("/qr/verificar-cdc")
def verificar_cdc(qr_id: int = Query(...)):
    try:
        if qr_id in cdc_storage:
            return {"cdc_id": cdc_storage[qr_id]}
        else:
            return {"cdc_id": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verificando CDC_ID: {str(e)}")
