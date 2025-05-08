from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import qrcode
from io import BytesIO
import base64
import random

app = FastAPI()
cdc_storage = {}  # Estructura: {(qr_id, session_id): cdc_id}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QRRequest(BaseModel):
    session_id: str

class CDCRequest(BaseModel):
    qr_id: int
    cdc_id: str
    session_id: str

@app.post("/qr/generador")
def generar_qr(request: QRRequest):
    try:
        qr_id = random.randint(1, 999999)
        qr_data = f"https://adrieldt911.github.io/ScanWeb/?qr_id={qr_id}&session_id={request.session_id}"

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

@app.post("/qr/guardar-cdc")
def guardar_cdc(request: CDCRequest):
    try:
        key = (request.qr_id, request.session_id)
        cdc_storage[key] = request.cdc_id
        return {"status": "ok", "message": f"CDC_ID '{request.cdc_id}' guardado para QR_ID {request.qr_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recibiendo CDC_ID: {str(e)}")

@app.get("/qr/verificar-cdc")
def verificar_cdc(qr_id: int = Query(...), session_id: str = Query(...)):
    try:
        key = (qr_id, session_id)
        return {"cdc_id": cdc_storage.get(key)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verificando CDC_ID: {str(e)}")
