from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import obtener_db
from core.models.mecanico import Mecanico
from core.models.orden import Orden
from core.models.orden_repuesto import OrdenRepuesto
from core.models.repuesto import Repuesto
from core.models.factura import Factura
from core.schemas.schemas import (
    OrdenCreate, OrdenPatch, OrdenUpdate, AgregarRepuestoOrden,
    RepuestoEnOrdenResponse,
)

router = APIRouter(prefix="/ordenes", tags=["Ordenes de servicio"])


@router.post("", status_code=201)
async def crear_orden(orden: OrdenCreate, db: AsyncSession = Depends(obtener_db)):
    mecanico = await db.get(Mecanico, orden.mecanico_id)
    if not mecanico:
        raise HTTPException(status_code=404, detail="El mecánico no existe")

    sentencia = select(Orden).where(
        Orden.placa == orden.placa.upper(), Orden.estado != "Entregada"
    )
    resultado = await db.execute(sentencia)
    if resultado.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="La moto ya se encuentra en el taller")

    nueva_orden = Orden(
        placa=orden.placa.upper(), modelo=orden.modelo,
        falla_reportada=orden.falla_reportada, mecanico_id=orden.mecanico_id,
        estado="En diagnóstico", costo_reparacion=0,
    )
    db.add(nueva_orden)
    await db.commit()
    await db.refresh(nueva_orden)
    return nueva_orden


@router.get("")
async def obtener_ordenes(estado: Optional[str] = None, db: AsyncSession = Depends(obtener_db)):
    sentencia = select(Orden)
    if estado:
        sentencia = sentencia.where(Orden.estado.ilike(estado))
    resultado = await db.execute(sentencia)
    ordenes = resultado.scalars().all()
    return {"total": len(ordenes), "ordenes": ordenes}


@router.get("/{placa}")
async def obtener_orden_por_placa(placa: str, db: AsyncSession = Depends(obtener_db)):
    resultado = await db.execute(select(Orden).where(Orden.placa == placa.upper()))
    orden = resultado.scalar_one_or_none()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return orden


@router.put("/{placa}")
async def actualizar_orden(placa: str, datos: OrdenUpdate, db: AsyncSession = Depends(obtener_db)):
    resultado = await db.execute(select(Orden).where(Orden.placa == placa.upper()))
    orden = resultado.scalar_one_or_none()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    factura_resultado = await db.execute(select(Factura).where(Factura.orden_id == orden.id))
    if orden.estado == "Reparada" or factura_resultado.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="No se puede modificar una orden ya cerrada/facturada")
    if datos.nuevo_estado.lower() == "reparada":
        raise HTTPException(status_code=400, detail="Para generar la factura automáticamente, cambia el estado usando PATCH /ordenes/{orden_id}")
    orden.estado = datos.nuevo_estado
    orden.costo_reparacion = datos.costo_reparacion
    await db.commit()
    await db.refresh(orden)
    return {"mensaje": "Orden actualizada correctamente", "orden": orden}


@router.delete("/{placa}", status_code=204)
async def eliminar_orden(placa: str, db: AsyncSession = Depends(obtener_db)):
    resultado = await db.execute(select(Orden).where(Orden.placa == placa.upper()))
    orden = resultado.scalar_one_or_none()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    factura_resultado = await db.execute(select(Factura).where(Factura.orden_id == orden.id))
    if factura_resultado.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="No se puede eliminar una orden facturada")
    await db.delete(orden)
    await db.commit()


@router.patch("/{orden_id}")
async def actualizacion_parcial(
    orden_id: int, orden_patch: OrdenPatch, db: AsyncSession = Depends(obtener_db)
):
    resultado = await db.execute(
        select(Orden).options(selectinload(Orden.repuestos_usados)).where(Orden.id == orden_id)
    )
    orden = resultado.scalar_one_or_none()
    if not orden:
        raise HTTPException(status_code=404, detail="La orden no existe")

    factura_resultado = await db.execute(select(Factura).where(Factura.orden_id == orden_id))
    factura_existente = factura_resultado.scalar_one_or_none()
    datos = orden_patch.model_dump(exclude_unset=True)
    nuevo_estado = datos.pop("nuevo_estado", None)
    mano_obra = datos.pop("mano_obra", None)

    if orden.estado == "Reparada" or factura_existente:
        if nuevo_estado and nuevo_estado.lower() != "reparada":
            raise HTTPException(status_code=400, detail="La orden ya está cerrada/facturada")
        # Repetir PATCH Reparada es permitido, pero nunca crea otra factura.
        if factura_existente:
            return {"mensaje": "La orden ya tiene factura; no se creó otra", "orden": orden}

    for campo, valor in datos.items():
        setattr(orden, campo, valor)

    if nuevo_estado:
        orden.estado = nuevo_estado.strip().capitalize()

    if orden.estado == "Reparada":
        if mano_obra is not None:
            orden.costo_reparacion = (orden.costo_reparacion or 0) + mano_obra

        if not orden.costo_reparacion or orden.costo_reparacion <= 0:
            await db.rollback()
            raise HTTPException(status_code=400, detail="No se puede reparar ni facturar una orden con costo igual a cero")

        subtotal_repuestos = sum(
            detalle.cantidad * detalle.precio_unitario_historico
            for detalle in orden.repuestos_usados
        )
        costo_mano_obra = orden.costo_reparacion - subtotal_repuestos
        if costo_mano_obra < 0:
            await db.rollback()
            raise HTTPException(status_code=400, detail="El costo total no puede ser menor que el subtotal de repuestos")

        total_neto = subtotal_repuestos + costo_mano_obra
        iva = round(total_neto * 0.19, 2)
        total_pagar = round(total_neto + iva, 2)
        nueva_factura = Factura(
            orden_id=orden.id, subtotal_repuestos=subtotal_repuestos,
            costo_mano_obra=costo_mano_obra, iva=iva, total_pagar=total_pagar,
        )
        db.add(nueva_factura)

    try:
        await db.commit()
        await db.refresh(orden)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="No fue posible actualizar la orden y generar la factura")
    return {"mensaje": "La orden ha sido actualizada con éxito", "orden": orden}


@router.post("/{orden_id}/repuesto", status_code=201, response_model=RepuestoEnOrdenResponse)
@router.post("/{orden_id}/repuestos", status_code=201, response_model=RepuestoEnOrdenResponse)
async def agregar_repuesto_a_orden(
    orden_id: int, datos: AgregarRepuestoOrden, db: AsyncSession = Depends(obtener_db)
):
    resultado_orden = await db.execute(select(Orden).where(Orden.id == orden_id))
    orden_db = resultado_orden.scalar_one_or_none()
    if not orden_db:
        raise HTTPException(status_code=404, detail="La orden de servicio no existe")

    factura_resultado = await db.execute(select(Factura).where(Factura.orden_id == orden_id))
    if orden_db.estado == "Reparada" or factura_resultado.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="No se pueden modificar repuestos de una orden ya cerrada/facturada")

    resultado_repuesto = await db.execute(select(Repuesto).where(Repuesto.id == datos.repuesto_id))
    repuesto_db = resultado_repuesto.scalar_one_or_none()
    if not repuesto_db:
        raise HTTPException(status_code=404, detail="El repuesto no existe")
    if repuesto_db.stock_actual < datos.cantidad:
        raise HTTPException(status_code=400, detail=f"Stock insuficiente. En almacén hay: {repuesto_db.stock_actual} y se solicitaron: {datos.cantidad}")

    existente_resultado = await db.execute(
        select(OrdenRepuesto).where(
            OrdenRepuesto.orden_id == orden_id, OrdenRepuesto.repuesto_id == repuesto_db.id
        )
    )
    detalle = existente_resultado.scalar_one_or_none()
    repuesto_db.stock_actual -= datos.cantidad
    if detalle:
        detalle.cantidad += datos.cantidad
    else:
        detalle = OrdenRepuesto(
            orden_id=orden_db.id, repuesto_id=repuesto_db.id, cantidad=datos.cantidad,
            precio_unitario_historico=repuesto_db.precio_venta,
        )
        db.add(detalle)
    orden_db.costo_reparacion = (orden_db.costo_reparacion or 0) + repuesto_db.precio_venta * datos.cantidad

    try:
        await db.commit()
        await db.refresh(detalle)
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error aplicando el repuesto a la orden")
    return detalle
