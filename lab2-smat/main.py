from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import models
from database import engine, get_db

# ==========================================================
# CRITICAL: CREACIÓN DE LA BASE DE DATOS Y TABLAS
# Esta línea busca el archivo 'smat.db' y crea las tablas
# definidas en models.py si es que aún no existen.
# ==========================================================
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SMAT - Sistema de Monitoreo de Alerta Temprana",
    description="""
API RESTful para la gestión y monitoreo de desastres naturales.
Permite la telemetría de sensores en tiempo real y el cálculo de niveles de riesgo.

**Módulos principales:**
* **Estaciones**: Gestión de recursos físicos.
* **Lecturas**: Datos capturados por sensores.
* **Riesgos**: Análisis de criticidad basado en umbrales.
    """,
    version="1.0.0",
    terms_of_service="http://unmsm.edu.pe/terms/",
    contact={
        "name": "Soporte Técnico SMAT - FISI",
        "url": "http://fisi.unmsm.edu.pe",
        "email": "desarrollo.smat@unmsm.edu.pe",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }
)

# Esquemas de validación (Pydantic)
class EstacionCreate(BaseModel):
    id: int
    nombre: str
    ubicacion: str

class LecturaCreate(BaseModel):
    estacion_id: int
    valor: float

# ==========================================================
# ENDPOINTS REFACTORIZADOS Y DOCUMENTADOS
# ==========================================================

@app.post(
    "/estaciones/",
    status_code=201,
    tags=["Gestión de Infraestructura"],
    summary="Registrar una nueva estación de monitoreo",
    description="Registra una estación física (IoT) en la base de datos relacional."
)
def crear_estacion(estacion: EstacionCreate, db: Session = Depends(get_db)):
    # Convertimos el esquema de Pydantic a Modelo de SQLAlchemy
    nueva_estacion = models.EstacionDB(id=estacion.id, nombre=estacion.nombre, ubicacion=estacion.ubicacion)
    db.add(nueva_estacion)
    db.commit()
    db.refresh(nueva_estacion)
    return {"msj": "Estación guardada en DB", "data": nueva_estacion}

@app.post(
    "/lecturas/",
    status_code=201,
    tags=["Telemetría de Sensores"],
    summary="Recibe datos de telemetría",
    description="Recibe eventos capturados por un sensor y los vincula a una estación existente mediante su ID."
)
def registrar_lectura(lectura: LecturaCreate, db: Session = Depends(get_db)):
    # Validar si la estación existe en la DB
    estacion = db.query(models.EstacionDB).filter(models.EstacionDB.id == lectura.estacion_id).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no existe")
    
    nueva_lectura = models.LecturaDB(valor=lectura.valor, estacion_id=lectura.estacion_id)
    db.add(nueva_lectura)
    db.commit()
    return {"status": "Lectura guardada en DB"}

# ----------------------------------------------------------
# Endpoint 3: Cálculo de Riesgo (Guía Paso 3.C)
# ----------------------------------------------------------
@app.get(
    "/estaciones/{id}/riesgo",
    tags=["Análisis de Riesgo"],
    summary="Evaluar nivel de peligro actual",
    description="Procesa la última lectura recibida de una estación y determina si el estado es NORMAL, ALERTA o PELIGRO."
)
def evaluar_riesgo(id: int, db: Session = Depends(get_db)):
    # Buscamos la última lectura de esta estación
    ultima_lectura = db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).order_by(models.LecturaDB.id.desc()).first()
    
    if not ultima_lectura:
        raise HTTPException(status_code=404, detail="No hay lecturas registradas para esta estación")
    
    # Lógica básica de evaluación de riesgo
    estado = "NORMAL"
    if ultima_lectura.valor > 50: 
        estado = "PELIGRO"
    elif ultima_lectura.valor > 30:
        estado = "ALERTA"
        
    return {"estacion_id": id, "ultimo_valor_registrado": ultima_lectura.valor, "nivel_riesgo": estado}

# ----------------------------------------------------------
# Endpoint 4: Historial (RETO)
# ----------------------------------------------------------
@app.get(
    "/estaciones/{id}/historial",
    tags=["Reportes Analíticos"],
    summary="Consultar historial de estación",
    description="Muestra los datos históricos reportados por un sensor y se vincula a una estación existente mediante su ID.",
    responses={
        404: {"description": "Estación no encontrada en el sistema."}
    }
)
def obtener_historial(id: int, db: Session = Depends(get_db)):
    historial = db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).all()
    
    if not historial:
        raise HTTPException(status_code=404, detail="Estación no encontrada o sin historial")
        
    return {"estacion_id": id, "historial": historial}