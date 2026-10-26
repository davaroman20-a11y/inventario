from pydantic import BaseModel, Field
from typing import Optional # Para campos que pueden estar vacíos


class ProductoCreate(BaseModel):
    codigo: str = Field(..., min_length=3, max_length=10, description="Código unico por producto")
    nombre: str = Field(..., min_length=3, max_length=50, description="Nombre del producto")
    categoria: str # = Field(...)
    precio: float = Field(..., gt=0, description="El precio debe ser mayor a 0") # Greater than
    stock: int = Field(default=0, ge=0, description="El stock no puede ser negatico") # Geater or equal
    compatible_con: Optional[str] = None # Campo opcional

# Esquema para crear una orden de servicio
class OrdenCreate(BaseModel):
    placa: str = Field(..., max_length=6, description="Placa de la motocicleta")
    modelo: str = Field(..., min_length=1, description="Modelo de la motocicleta")
    falla_reportada: str = Field(..., min_length=1, description="Falla reportada")

# Esquema para actualizar una orden de servicio
class OrdenUpdate(BaseModel):
    nuevo_estado: str = Field(..., min_length=1, description="Nuevo estado de la orden")
    costo_reparacion: float
