from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import obtener_db
from core.models.repuesto import Repuesto
from core.schemas.schemas import RepuestoCreate, RepuestoResponse

router = APIRouter(prefix="/repuestos", tags=["Repuestos"])


@router.post("", response_model=RepuestoResponse, status_code=201)
async def crear_repuesto(
    repuesto: RepuestoCreate,
    db: AsyncSession = Depends(obtener_db),
):
    nuevo_repuesto = Repuesto(**repuesto.model_dump())
    db.add(nuevo_repuesto)
    try:
        await db.commit()
        await db.refresh(nuevo_repuesto)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un repuesto con ese código SKU")
    return nuevo_repuesto


@router.get("", response_model=list[RepuestoResponse])
async def listar_repuestos(db: AsyncSession = Depends(obtener_db)):
    sentencia = select(Repuesto)
    resultado = await db.execute(sentencia)
    return resultado.scalars().all()
