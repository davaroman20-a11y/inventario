from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/ordenes", tags=["Ordenes de servicio"])


@router.get("")
async def obtener_ordenes_demo():
    return {"mensaje": "Módulo de órdenes listo para uso"}


@router.get("/health")
async def ordenes_health():
    return {"status": "ok"}