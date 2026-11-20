from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import obtener_db
from core.models.factura import Factura
from core.models.orden import Orden
from core.models.orden_repuesto import OrdenRepuesto
from core.schemas.schemas import (
    FacturaDetalladaResponse, OrdenFacturaResponse, MecanicoFacturaResponse,
    RepuestoFacturaDetalle,
)

router = APIRouter(prefix="/facturas", tags=["Facturación"])


@router.get("/{orden_id}", response_model=FacturaDetalladaResponse)
async def obtener_factura(orden_id: int, db: AsyncSession = Depends(obtener_db)):
    resultado = await db.execute(
        select(Factura)
        .options(
            selectinload(Factura.orden).selectinload(Orden.mecanico),
            selectinload(Factura.orden).selectinload(Orden.repuestos_usados).selectinload(OrdenRepuesto.repuesto),
        )
        .where(Factura.orden_id == orden_id)
    )
    factura = resultado.scalar_one_or_none()
    if not factura:
        raise HTTPException(status_code=404, detail="No existe una factura para esta orden")

    orden = factura.orden
    repuestos = [
        RepuestoFacturaDetalle(
            nombre_repuesto=detalle.repuesto.nombre,
            cantidad=detalle.cantidad,
            precio_unitario_historico=detalle.precio_unitario_historico,
            subtotal_linea=detalle.cantidad * detalle.precio_unitario_historico,
        )
        for detalle in orden.repuestos_usados
    ]
    return FacturaDetalladaResponse(
        id=factura.id, fecha_emision=factura.fecha_emision,
        subtotal_repuestos=factura.subtotal_repuestos,
        costo_mano_obra=factura.costo_mano_obra, iva=factura.iva,
        total_pagar=factura.total_pagar,
        orden=OrdenFacturaResponse(
            placa=orden.placa, modelo=orden.modelo,
            mecanico=(MecanicoFacturaResponse(nombre_completo=orden.mecanico.nombre_completo) if orden.mecanico else None),
            repuestos=repuestos,
        ),
    )
