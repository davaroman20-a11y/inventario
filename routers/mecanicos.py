from fastapi import APIRouter, Depends, HTTPException
import json
import os

from ..dependencias import verificar_gerente, verificar_auditor, parametros_paginacion
from ..schemas import MecanicoCreate

router = APIRouter(prefix="/mecanicos", tags=["Mecanicos"])

# Ruta del archivo JSON, ubicada en la carpeta principal del proyecto
ARCHIVO_MECANICOS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mecanicos.json")


def leer_mecanicos():
    try:
        with open(ARCHIVO_MECANICOS, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        return []


def guardar_mecanicos(mecanicos):
    with open(ARCHIVO_MECANICOS, "w", encoding="utf-8") as archivo:
        json.dump(mecanicos, archivo, indent=4, ensure_ascii=False)



@router.get("")
async def listar_mecanicos(
    paginacion: dict = Depends(parametros_paginacion),
    rol: str = Depends(verificar_auditor)
):
    mecanicos = leer_mecanicos()
    skip = paginacion["skip"]
    limit = paginacion["limit"]
    mecanicos_paginados = mecanicos[skip:skip + limit]

    return {
        "total": len(mecanicos),
        "cantidad": len(mecanicos_paginados),
        "mecanicos": mecanicos_paginados
    }


@router.post("", status_code=201)
async def crear_mecanico(
    mecanico: MecanicoCreate,
    rol: str = Depends(verificar_gerente)
):
    mecanicos = leer_mecanicos()

    nuevo_id = max((dato["id"] for dato in mecanicos), default=0) + 1
    nuevo_mecanico = {
        "id": nuevo_id,
        **mecanico.model_dump()
    }

    mecanicos.append(nuevo_mecanico)
    guardar_mecanicos(mecanicos)

    return {
        "mensaje": "Mecanico creado exitosamente",
        "mecanico": nuevo_mecanico
    }



@router.delete("/{id}")
async def eliminar_mecanico(
    id: int,
    rol: str = Depends(verificar_gerente)
):
    mecanicos = leer_mecanicos()
    mecanicos_actualizados = [dato for dato in mecanicos if dato["id"] != id]

    if len(mecanicos) == len(mecanicos_actualizados):
        raise HTTPException(status_code=404, detail="Mecanico no encontrado")

    guardar_mecanicos(mecanicos_actualizados)
    return {"mensaje": "Mecanico eliminado correctamente", "id": id}
