from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import obtener_db
from core.models.mecanico import Mecanico
from core.schemas.schemas import MecanicoCreate, MecanicoResponse

router = APIRouter(prefix="/mecanicos", tags=["Mecanicos"])


@router.post("", response_model=MecanicoResponse, status_code=201)
async def crear_mecanico(
    mecanico: MecanicoCreate,
    db: AsyncSession = Depends(obtener_db),
):
    nuevo_mecanico = Mecanico(**mecanico.model_dump())
    db.add(nuevo_mecanico)
    try:
        await db.commit()
        await db.refresh(nuevo_mecanico)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe un mecánico con ese documento")
    return nuevo_mecanico


@router.get("", response_model=list[MecanicoResponse])
async def listar_mecanicos(db: AsyncSession = Depends(obtener_db)):
    sentencia = select(Mecanico)
    resultado = await db.execute(sentencia)
    return resultado.scalars().all()
