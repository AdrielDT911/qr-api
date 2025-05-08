from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import qrcode
from io import BytesIO
import base64
import uuid

app = FastAPI()
cdc_storage = {}  # Estructura: { session_id: { qr_id: cdc_id } }

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QRRequest(BaseModel):
    app_session: str

class CDCRequest(BaseModel):
    qr_id: str
    cdc_id: str
    app_session: str

@app.post("/qr/generador")
def generar_qr(request: QRRequest):
    try:
        qr_id = uuid.uuid4().hex
        qr_data = f"https://adrieldt911.github.io/ScanWeb/?qr_id={qr_id}&app_session={request.app_session}"

        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_bytes = buffer.getvalue()

        # Inicializar espacio para esa sesión
        if request.app_session not in cdc_storage:
            cdc_storage[request.app_session] = {}

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
        if request.app_session not in cdc_storage:
            cdc_storage[request.app_session] = {}

        cdc_storage[request.app_session][request.qr_id] = request.cdc_id
        return {"status": "ok", "message": f"CDC_ID '{request.cdc_id}' guardado para sesión {request.app_session} y QR_ID {request.qr_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando CDC_ID: {str(e)}")

@app.get("/qr/verificar-cdc")
def verificar_cdc(qr_id: str = Query(...), app_session: str = Query(...)):
    try:
        cdc_id = cdc_storage.get(app_session, {}).get(qr_id)
        return {"cdc_id": cdc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verificando CDC_ID: {str(e)}")
