from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import inspect

from core.config import settings
from core import models  # Importa todos los modelos antes de create_all
from core.database import Base, engine
from dependencias import simular_base_datos
from routers.inventario import router as router_inventario
from routers.mecanicos import router as router_mecanicos
from routers.ordenes import router as router_ordenes
from routers.repuestos import router as router_repuestos
from routers.facturas import router as router_facturas

def preparar_base_datos(conn):
    # create_all crea tablas nuevas, pero no agrega columnas a tablas existentes.
    # Esta pequeña migración conserva los datos de la base anterior.
    inspector = inspect(conn)
    if "ordenes" in inspector.get_table_names():
        columnas = [columna["name"] for columna in inspector.get_columns("ordenes")]
        if "mecanico_id" not in columnas:
            conn.exec_driver_sql(
                "ALTER TABLE ordenes ADD COLUMN mecanico_id INTEGER REFERENCES mecanicos(id)"
            )
    Base.metadata.create_all(conn)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("---- Conectando con la base de datos y creando tablas ----")
    async with engine.begin() as conn:
        await conn.run_sync(preparar_base_datos)
    print("Base de datos lista")
    yield
    print("Apagando el servidor")
    await engine.dispose()


app = FastAPI(
    title="API inventarios SENA",
    description="API asíncrona para el inventario y taller mecánico",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router_inventario)
app.include_router(router_ordenes)
app.include_router(router_mecanicos)
app.include_router(router_repuestos)
app.include_router(router_facturas)


@app.get("/prueba-yield")
async def probar_yield(conexion: str = Depends(simular_base_datos)):
    return {"mensaje": "revisar consola", "estado": conexion}


@app.get("/")
async def ping():
    return {
        "mensaje": f"Bienvenido a {settings.PROJECT_NAME}",
        "db_configurada": True,
    }
