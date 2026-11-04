from fastapi import APIRouter, HTTPException
from fastapi import APIRouter, HTTPException
import json
import os
from schemas import OrdenCreate, OrdenUpdate

router = APIRouter(prefix="/ordenes", tags=["ordenes de servicio"])

ARCHIVO_TALLER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "taller.json")

def leer_ordenes():
    try:
        with open(ARCHIVO_TALLER, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        return []

def guardar_ordenes(ordenes):
    with open(ARCHIVO_TALLER, "w", encoding="utf-8") as archivo:
        json.dump(ordenes, archivo, indent=4, ensure_ascii=False)

# 1 registrar
@router.post("", status_code=201)
async def crear_orden(orden: OrdenCreate):
    ordenes = leer_ordenes()

    for dato in ordenes:
        if dato["placa"].upper() == orden.placa.upper() and dato["estado"].lower() != "entregada":
            raise HTTPException(
                status_code=400,
                detail="La moto ya se encuentra en el taller"
            )

    nueva_orden = {
        "placa": orden.placa.upper(),
        "modelo": orden.modelo,
        "falla_reportada": orden.falla_reportada,
        "estado": "En diagnóstico",
        "costo_reparacion": 0
    }

    ordenes.append(nueva_orden)
    guardar_ordenes(ordenes)

    return nueva_orden

# 2consultar
@router.get("")
async def consultar_ordenes(
    estado: str = None,
    modelo: str = None,
    costo_minimo: float = None
):
    ordenes = leer_ordenes()

    if estado:
        ordenes = [
            orden for orden in ordenes
            if orden["estado"].lower() == estado.lower()
        ]

    if modelo:
        ordenes = [
            orden for orden in ordenes
            if modelo.lower() in orden["modelo"].lower()
        ]

    if costo_minimo is not None:
        ordenes = [
            orden for orden in ordenes
            if orden["costo_reparacion"] >= costo_minimo
        ]

    return {
        "total_ordenes": len(ordenes),
        "ordenes": ordenes
    }

# 3. actualizar
@router.put("/{placa}")
async def actualizar_orden(placa: str, datos: OrdenUpdate):
    ordenes = leer_ordenes()
    orden_encontrada = None

    for orden in ordenes:
        if orden["placa"].upper() == placa.upper():
            orden_encontrada = orden
            break

    # Validar que la placa exista
    if orden_encontrada is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    # Validar el costo cuando la moto queda reparada
    if datos.nuevo_estado.lower() == "reparada" and datos.costo_reparacion <= 0:
        raise HTTPException(
            status_code=400,
            detail="No se puede marcar como reparada sin asignar un costo de reparación"
        )

    orden_encontrada["estado"] = datos.nuevo_estado
    orden_encontrada["costo_reparacion"] = datos.costo_reparacion

    guardar_ordenes(ordenes)

    return {"mensaje": "Orden actualizada correctamente", "orden": orden_encontrada}