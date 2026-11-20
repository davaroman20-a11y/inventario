from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class OrdenRepuesto(Base):
    __tablename__ = "orden_repuestos"

    orden_id = Column(Integer, ForeignKey("ordenes.id"), primary_key=True)
    repuesto_id = Column(Integer, ForeignKey("repuestos.id"), primary_key=True)

    cantidad = Column(Integer, nullable=False, default=1)
    precio_unitario_historico = Column(Float, nullable=False)

    orden = relationship("Orden", back_populates="repuestos_usados")
    repuesto = relationship("Repuesto", back_populates="ordenes_asociadas")
    