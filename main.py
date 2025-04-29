from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import qrcode
from io import BytesIO
import base64
import random
qr_cdc_storage = {}  # Mapea qr_id -> cdc_id (cuando ya se escaneó)

# App FastAPI
app = FastAPI()

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
            f"app_id={request.app_id}&app_user={request.app_user}"
            f"&app_page_id={request.app_page_id}&qr_id={qr_id}"  # <-- lo agregamos aquí
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
        # Guardamos el cdc_id para ese qr_id
        qr_cdc_storage[request.qr_id] = request.cdc_id
        return {"status": "ok", "message": f"CDC_ID '{request.cdc_id}' guardado para QR_ID {request.qr_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recibiendo CDC_ID: {str(e)}")

# Verificars CDC
@app.get("/qr/verificar-cdc")
def verificar_cdc(qr_id: int):
    try:
        cdc = qr_cdc_storage.get(qr_id)
        if cdc:
            return {"qr_id": qr_id, "cdc_id": cdc}
        else:
            return {"qr_id": qr_id, "cdc_id": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar CDC_ID: {str(e)}")


