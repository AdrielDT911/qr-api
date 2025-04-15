from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import oracledb
import qrcode
from io import BytesIO
import base64
import random
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

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

# Conexión Oracle
dsn = oracledb.makedsn(
    os.getenv("DB_HOST"),
    os.getenv("DB_PORT"),
    service_name=os.getenv("DB_SERVICE_NAME")
)

connection = oracledb.connect(
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    dsn=dsn
)
print("✅ Conectado a Oracle")

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
        qr_data = f"https://adrieldt911.github.io/Web-Scan/index.html?app_id={request.app_id}&app_user={request.app_user}&app_page_id={request.app_page_id}"
        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_bytes = buffer.getvalue()
        qr_id = random.randint(1, 999999)

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO QR_SCANS (QR_ID, APP_ID, APP_USER, APP_PAGE_ID, URL_GEN, QR_IMAGE)
                VALUES (:1, :2, :3, :4, :5, :6)
            """, [qr_id, request.app_id, request.app_user, request.app_page_id, qr_data, qr_bytes])
            connection.commit()

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
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE QR_SCANS
                SET CDC_ID = :1
                WHERE QR_ID = :2
            """, [request.cdc_id, request.qr_id])
            connection.commit()

        return {"status": "ok", "message": f"CDC_ID guardado para QR_ID {request.qr_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando CDC_ID: {str(e)}")



# cd C:\Users\SCV\Documents\QR_API
# uvicorn main:app --host 0.0.0.0 --port 8000
