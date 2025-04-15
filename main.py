import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import cx_Oracle
import qrcode
from io import BytesIO
import base64
import random
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Inicialización de la aplicación FastAPI
app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite solicitudes desde cualquier origen
    allow_credentials=True,
    allow_methods=["*"],  # Permite cualquier método HTTP
    allow_headers=["*"],  # Permite cualquier encabezado
)

# Conectar a la base de datos usando las variables del .env
dsn = cx_Oracle.makedsn(
    os.getenv("DB_HOST"), 
    os.getenv("DB_PORT"), 
    service_name=os.getenv("DB_SERVICE_NAME")
)

connection = cx_Oracle.connect(
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    dsn=dsn
)
print("✅ Conexión exitosa a Oracle")

# MODELO: Para generación de QR
class QRRequest(BaseModel):
    app_id: int
    app_user: str
    app_page_id: int

# MODELO: Para guardar CDC_ID
class CDCRequest(BaseModel):
    qr_id: int
    cdc_id: str

# Ruta para generar el QR
@app.post("/qr/generador")
def generador_qr(request: QRRequest):
    """
    Genera un código QR con los datos proporcionados y lo devuelve como una imagen en base64.
    """
    try:
        # Generación de la URL para el QR
        qr_data = f"https://adrieldt911.github.io/Web-Scan/index.html?app_id={request.app_id}&app_user={request.app_user}&app_page_id={request.app_page_id}"

        # Generación del QR
        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_bytes = buffer.getvalue()

        # Generación del ID único (número aleatorio entre 1 y 999999)
        qr_id = random.randint(1, 999999)
        
        # Insertar el QR generado en la base de datos
        cursor = connection.cursor()
        query = """
            INSERT INTO QR_SCANS (QR_ID, APP_ID, APP_USER, APP_PAGE_ID, URL_GEN, QR_IMAGE)
            VALUES (:1, :2, :3, :4, :5, :6)
        """
        
        # Convertir los bytes de la imagen a un tipo adecuado para Oracle (BLOB)
        cursor.execute(query, [qr_id, request.app_id, request.app_user, request.app_page_id, qr_data, qr_bytes])
        connection.commit()
        cursor.close()
        
        # Convertir la imagen a base64 para la respuesta
        qr_base64 = base64.b64encode(qr_bytes).decode()
        print("Base64 generado:", qr_base64[:50])  # Muestra los primeros 50 chars

        return {"qr": qr_base64, "url": qr_data, "qr_id": qr_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando QR: {str(e)}")


# 📌 ENDPOINT 2: Guardar el cdc_id en la misma fila usando qr_id
@app.post("/qr/guardar-cdc")
def guardar_cdc(request: CDCRequest):
    try:
        cursor = connection.cursor()

        # Actualizamos la fila con el CDC_ID
        update_query = """
            UPDATE QR_SCANS
            SET CDC_ID = :1
            WHERE QR_ID = :2
        """
        cursor.execute(update_query, [request.cdc_id, request.qr_id])
        connection.commit()
        cursor.close()

        return {"status": "ok", "message": f"CDC_ID guardado para QR_ID {request.qr_id}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando CDC_ID: {str(e)}")

# cd C:\Users\SCV\Documents\QR_API
# uvicorn main:app --host 0.0.0.0 --port 8000
