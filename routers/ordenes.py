import json
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from dependencias import verificar_api_key, parametros_paginacion
from core.schemas.schemas import OrdenCreate, OrdenUpdate

router = APIRouter(prefix="/ordenes", tags=["Ordenes de servicio"])
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


@router.post("", status_code=201)
async def crear_orden(
    orden: OrdenCreate,
    api_key: str = Depends(verificar_api_key),
):
    ordenes = leer_ordenes()
    for dato in ordenes:
        if dato["placa"].upper() == orden.placa.upper() and dato["estado"].lower() != "entregada":
            raise HTTPException(status_code=400, detail="La moto ya se encuentra en el taller")

    nueva_orden = {
        "placa": orden.placa.upper(),
        "modelo": orden.modelo,
        "falla_reportada": orden.falla_reportada,
        "estado": "En diagnóstico",
        "costo_reparacion": 0,
    }
    ordenes.append(nueva_orden)
    guardar_ordenes(ordenes)
    return {"mensaje": "Orden creada exitosamente", "orden": nueva_orden, "llave_usada": api_key}


@router.get("")
async def obtener_ordenes(
    estado: Optional[str] = None,
    paginacion: dict = Depends(parametros_paginacion),
):
    ordenes = leer_ordenes()
    if estado:
        ordenes = [o for o in ordenes if o["estado"].lower() == estado.lower()]
    skip, limit = paginacion["skip"], paginacion["limit"]
    return {"total": len(ordenes), "ordenes": ordenes[skip:skip + limit]}


@router.get("/{placa}")
async def obtener_orden_por_placa(placa: str):
    for orden in leer_ordenes():
        if orden["placa"].upper() == placa.upper():
            return orden
    raise HTTPException(status_code=404, detail="Orden no encontrada")


@router.put("/{placa}")
async def actualizar_orden(placa: str, datos: OrdenUpdate):
    ordenes = leer_ordenes()
    for orden in ordenes:
        if orden["placa"].upper() == placa.upper():
            orden["estado"] = datos.nuevo_estado
            orden["costo_reparacion"] = datos.costo_reparacion
            guardar_ordenes(ordenes)
            return {"mensaje": "Orden actualizada correctamente", "orden": orden}
    raise HTTPException(status_code=404, detail="Orden no encontrada")
