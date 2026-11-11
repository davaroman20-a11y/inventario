from typing import Optional
from pydantic import BaseModel, Field, model_validator


class ProductoCreate(BaseModel):
    codigo: str = Field(..., min_length=3, max_length=10, description="Código único por producto")
    nombre: str = Field(..., min_length=3, max_length=50)
    categoria: str
    precio: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    compatible_con: Optional[str | list[str]] = None


class OrdenCreate(BaseModel):
    placa: str = Field(..., max_length=6)
    modelo: str = Field(..., min_length=1)
    falla_reportada: str = Field(..., min_length=1)


class OrdenUpdate(BaseModel):
    nuevo_estado: str = Field(..., min_length=1)
    costo_reparacion: float

    @model_validator(mode="after")
    def validar_costo_operacion(self):
        if self.nuevo_estado.lower() == "reparada" and self.costo_reparacion <= 0:
            raise ValueError("No se puede marcar como reparada sin asignar un costo mayor a cero")
        self.nuevo_estado = self.nuevo_estado.capitalize()
        return self


class OrdenPatch(BaseModel):
    nuevo_estado: Optional[str] = None
    costo_reparacion: Optional[float] = Field(None, ge=0)
    falla_reportada: Optional[str] = None


class OrdenResponse(OrdenCreate):
    id: int
    estado: str
    costo_reparacion: float

    model_config = {"from_attributes": True}


class MecanicoCreate(BaseModel):
    documento: str = Field(..., min_length=1, max_length=15)
    nombre_completo: str = Field(..., min_length=1, max_length=100)
    especialidad: str = Field(..., min_length=1, max_length=50)


class MecanicoResponse(MecanicoCreate):
    id: int
    activo: bool

    model_config = {"from_attributes": True}


class RepuestoCreate(BaseModel):
    codigo_sku: str = Field(..., min_length=1, max_length=20)
    nombre: str = Field(..., min_length=1, max_length=100)
    precio_compra: float
    precio_venta: float
    stock_actual: int = Field(default=0, ge=0)


class RepuestoResponse(RepuestoCreate):
    id: int

    model_config = {"from_attributes": True}
