from fastapi import FastAPI
from routers.ordenes import router as router_ordenes
from routers.inventario import router as router_inventario

app = FastAPI(
    title="API inventarios SENA",
    description="Mi primera API asíncrona",
    version="1.0.0"
)

app.include_router(router_inventario)
app.include_router(router_ordenes)


