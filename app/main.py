from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import uvicorn
import logging
from sqlalchemy.exc import SQLAlchemyError

from config.db import engine, Base
from routes import auth, products, reports
from models import user, product

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)
logger = logging.getLogger(__name__)

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Inicializar la aplicación FastAPI
app = FastAPI(
    title="Sistema de Inventario",
    description="API del Sistema de Inventario para pequeños negocios",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar carpeta de archivos estáticos
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Configurar plantillas
templates = Jinja2Templates(directory="templates")

# Incluir rutas
app.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
app.include_router(products.router, prefix="/products", tags=["Productos"])
app.include_router(reports.router, prefix="/reports", tags=["Informes"])

# Ruta de inicio
@app.get("/", tags=["General"])
async def root():
    return {
        "message": "API del Sistema de Inventario",
        "docs": "/docs",
        "version": "1.0.0"
    }

# Manejador de errores
@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Error de base de datos: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno de base de datos"}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error general: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor"}
    )

# Middleware para logging de solicitudes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Solicitud entrante: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Respuesta: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error en la solicitud: {str(e)}")
        raise

# Punto de entrada para ejecución directa
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)