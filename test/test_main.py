from fastapi.testclient import TestClient
# OJO: Como moviste main.py a la carpeta app, la importación debe ser desde app
from app.main import app 

client = TestClient(app)

def test_crear_estacion():
    response = client.post("/estaciones/", json={
        "id": 1,
        "nombre": "Estación Rímac",
        "ubicacion": "Chosica"
    })
    assert response.status_code == 201
    assert response.json()["data"]["nombre"] == "Estación Rímac"

def test_registrar_lectura():
    # Simulamos lectura de sensor para la estación ID 1
    response = client.post("/lecturas/", json={
        "estacion_id": 1,
        "valor": 12.5
    })
    assert response.status_code == 201
    assert response.json()["status"] == "Lectura recibida"

def test_riesgo_peligro():
    # 1. Registro de estación y lectura crítica (> 20.0)
    client.post("/estaciones/", json={"id": 10, "nombre": "Misti", "ubicacion": "Arequipa"})
    client.post("/lecturas/", json={"estacion_id": 10, "valor": 25.5})

    # 2. Prueba de endpoint de riesgo
    response = client.get("/estaciones/10/riesgo")
    assert response.status_code == 200
    assert response.json()["nivel"] == "PELIGRO"

def test_estacion_no_encontrada():
    # Probar un ID que no existe (ejemplo: 999)
    response = client.get("/estaciones/999/riesgo")
    assert response.status_code == 404
    assert response.json()["detail"] == "Estación no encontrada"

def test_obtener_dashboard():
    # 1. Ejecutamos la petición GET al nuevo endpoint
    response = client.get("/estaciones/dashboard")
    
    # 2. Validamos que la respuesta sea exitosa (HTTP 200 OK)
    assert response.status_code == 200
    
    # 3. Extraemos el JSON de la respuesta
    data = response.json()
    
    # 4. Validamos que los cálculos aritméticos y las llaves existan en el reporte
    assert "total_estaciones_monitoreadas" in data
    assert "total_lecturas_procesadas" in data
    assert "punto_critico_maximo" in data
    
    # Verificamos que los totales sean números enteros (aritméticamente correctos)
    assert isinstance(data["total_estaciones_monitoreadas"], int)
    assert isinstance(data["total_lecturas_procesadas"], int)