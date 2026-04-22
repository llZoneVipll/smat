from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

# IMPORTACIONES RELATIVAS PROFESIONALES
# El punto '.' indica que los archivos están en la misma carpeta /app
from . import models, schemas
from .database import engine, get_db

# Inicialización de la base de datos (Paso 1 de la guía)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SMAT - Sistema de Monitoreo de Alerta Temprana",
    description="""
API RESTful para la gestión y monitoreo de desastres naturales (FISI - UNMSM).
Arquitectura limpia aplicada: Modelos, Esquemas y Controladores separados.
    """,
    version="1.0.0"
)

# CONFIGURACIÓN DE SEGURIDAD (Middleware CORS - Paso 2 de la guía)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# ENDPOINTS (CONTROLADORES)
# ==========================================================

@app.post("/estaciones/", status_code=201, tags=["Gestión de Infraestructura"])
def crear_estacion(estacion: schemas.EstacionCreate, db: Session = Depends(get_db)):
    nueva_estacion = models.EstacionDB(id=estacion.id, nombre=estacion.nombre, ubicacion=estacion.ubicacion)
    db.add(nueva_estacion)
    db.commit()
    db.refresh(nueva_estacion)
    return {"msj": "Estación guardada en DB", "data": nueva_estacion}

@app.post("/lecturas/", status_code=201, tags=["Telemetría de Sensores"])
def registrar_lectura(lectura: schemas.LecturaCreate, db: Session = Depends(get_db)):
    estacion = db.query(models.EstacionDB).filter(models.EstacionDB.id == lectura.estacion_id).first()
    if not estacion:
        raise HTTPException(status_code=404, detail="Estación no existe")
    
    nueva_lectura = models.LecturaDB(valor=lectura.valor, estacion_id=lectura.estacion_id)
    db.add(nueva_lectura)
    db.commit()
    return {"status": "Lectura guardada en DB"}

@app.get("/estaciones/{id}/riesgo", tags=["Análisis de Riesgo"])
def evaluar_riesgo(id: int, db: Session = Depends(get_db)):
    ultima_lectura = db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).order_by(models.LecturaDB.id.desc()).first()
    
    if not ultima_lectura:
        raise HTTPException(status_code=404, detail="No hay lecturas registradas")
    
    # Lógica de criticidad
    estado = "NORMAL"
    if ultima_lectura.valor > 50: estado = "PELIGRO"
    elif ultima_lectura.valor > 30: estado = "ALERTA"
        
    return {"estacion_id": id, "ultimo_valor": ultima_lectura.valor, "nivel_riesgo": estado}

@app.get("/estaciones/{id}/historial", tags=["Reportes Analíticos"])
def obtener_historial(id: int, db: Session = Depends(get_db)):
    historial = db.query(models.LecturaDB).filter(models.LecturaDB.estacion_id == id).all()
    if not historial:
        raise HTTPException(status_code=404, detail="Estación sin historial")
    return {"estacion_id": id, "historial": historial}

# RETO FINAL: DASHBOARD DE AUDITORÍA
@app.get("/estaciones/dashboard", tags=["Auditoría"])
def obtener_dashboard(db: Session = Depends(get_db)):
    total_estaciones = db.query(models.EstacionDB).count()
    total_lecturas = db.query(models.LecturaDB).count()
    
    lectura_max = db.query(models.LecturaDB).order_by(models.LecturaDB.valor.desc()).first()
    punto_critico = None
    if lectura_max:
        estacion = db.query(models.EstacionDB).filter(models.EstacionDB.id == lectura_max.estacion_id).first()
        punto_critico = {
            "estacion_id": lectura_max.estacion_id,
            "nombre_estacion": estacion.nombre if estacion else "Desconocida",
            "valor_maximo": lectura_max.valor
        }
        
    return {
        "total_estaciones_monitoreadas": total_estaciones,
        "total_lecturas_procesadas": total_lecturas,
        "punto_critico_maximo": punto_critico
    }