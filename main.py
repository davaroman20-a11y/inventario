from fastapi import Depends, FastAPI
from .dependencias import simular_base_datos
from .routers.ordenes import router as router_ordenes
from .routers.inventario import router as router_inventario
from .routers.mecanicos import router as router_mecanicos

app = FastAPI(
    title="API inventarios SENA",
    description="Mi primera API asíncrona",
    version="1.0.0"
)

app.include_router(router_inventario)
app.include_router(router_ordenes)
app.include_router(router_mecanicos)


@app.get("/prueba-yield")
async def probar_yield(conexion: str = Depends(simular_base_datos)):
    print("2. [RUTA] Ejecutando la ruta. Estado:", conexion)
    return {"mensaje": "revisar consola"}


