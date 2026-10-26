from fastapi import FastAPI, HTTPException
from databse import leer_base_datos, obtener_producto, guardar_base_datos
from schemas import ProductoCreate, OrdenCreate, OrdenUpdate

# Inicializar la aplicación
apiRest = FastAPI(
    title="API inventarios SENA",
    description="Mi primera API asíncrona",
    version="1.0.0"
)

# Nuestro primer endpoint
@apiRest.get("/")
async def ruta_principal():
    return {"mensaje": "¡Bienvenido a mi primera API Rest!"}

@apiRest.get("/estado")
async def estado_servidor():
    return {"status": "En línea", "servicios": "Operativos sin ningún inconveniente"}

@apiRest.get("/suma")
async def sumar():
    numero1 = 5
    numero2 = 4
    resultado = numero1 + numero2
    return  resultado

@apiRest.get("/productos")
async def listar_productos():
    datos = await leer_base_datos()
    return {"cantidad": len(datos), "productos": datos}

@apiRest.get("/productos/{codigo_producto}")
async def buscar_un_producto(codigo_producto: str):
    try:
        producto = await obtener_producto(codigo_producto)
        return producto
    except KeyError:
        raise HTTPException(status_code=404, detail="El producto solicitado no existe en la BD")

@apiRest.get("/categorias")
async def listar_categorias():
    datos = await leer_base_datos()
    categorias = set()

@apiRest.get("/alertas/stock")
async def stock_critico():
    datos = await leer_base_datos()
    productos_criticos = []

@apiRest.get("/productos/buscar/{palabra_clave}")
async def buscar_por_nombre(palabra_clave: str):
    datos = await leer_base_datos()
    productos_encontrados = []

@apiRest.post("/productos", status_code="201")
async def registrar_nuevo_producto(producto: ProductoCreate):
    datos = await leer_base_datos()

    # 1. Validar que el producto no exista
    for dato in datos:
        if dato["codigo"] == producto.codigo:
            raise HTTPException(status_code=400, detail="El codigo de producto ya exixte.")

    # 2. Convertir la clase a un diccionario
    nuevo_producto = producto.model_dump()

    # 3. Guardar
    datos.append(nuevo_producto)
    await guardar_base_datos(datos)

    return {"mensaje": "Producto registrado correctamente", "Producto": nuevo_producto}

# Put, actulizar inventario
@apiRest.put("/productos/{codigo_producto}")
async def actualizar_producto(codigo_producto: str, producto_actualizado: ProductoCreate):
    datos = await leer_base_datos()
    for posicion, dato in enumerate(datos):
        if dato["codigo"] == codigo_producto:
            # Reemplazamos los datos manteniendo el codigo
            datos[posicion] = producto_actualizado.model_dump()
            datos[posicion]["codigo"] = codigo_producto

            await guardar_base_datos(datos)
            return {"mensaje": "Producto actualizado", "producto": datos[posicion]}

        raise HTTPException(status_code=404, detail="Producto no encontrado")

# ==========================================================
# TALLER DE MOTOCICLETAS - ORDENES DE SERVICIO
# Se agrega este codigo sin borrar los endpoints anteriores.
# ==========================================================
import json
import os

ARCHIVO_TALLER = os.path.join(os.path.dirname(__file__), "taller.json")

def leer_ordenes():
    try:
        with open(ARCHIVO_TALLER, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        return []

def guardar_ordenes(ordenes):
    with open(ARCHIVO_TALLER, "w", encoding="utf-8") as archivo:
        json.dump(ordenes, archivo, indent=4, ensure_ascii=False)

# 1. Registrar una orden de ingreso
@apiRest.post("/ordenes", status_code=201)
async def crear_orden(orden: OrdenCreate):
    ordenes = leer_ordenes()

    for dato in ordenes:
        if dato["placa"].upper() == orden.placa.upper() and dato["estado"] != "Entregada":
            raise HTTPException(status_code=400, detail="La moto ya se encuentra en el taller")

    nueva_orden = {
        "placa": orden.placa.upper(),
        "modelo": orden.modelo,
        "falla_reportada": orden.falla_reportada,
        "estado": "En diagnóstico",
        "costo_reparacion": 0
    }

    ordenes.append(nueva_orden)
    guardar_ordenes(ordenes)
    return nueva_orden

# 2. Consultar todas las ordenes
@apiRest.get("/ordenes")
async def consultar_ordenes():
    return leer_ordenes()

# 3. Actualizar el estado y el costo de una orden
@apiRest.put("/ordenes/{placa}")
async def actualizar_orden(placa: str, datos: OrdenUpdate):
    ordenes = leer_ordenes()
    orden_encontrada = None

    for orden in ordenes:
        if orden["placa"].upper() == placa.upper():
            orden_encontrada = orden
            break

    if orden_encontrada is None:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    if datos.nuevo_estado == "Reparada" and datos.costo_reparacion <= 0:
        raise HTTPException(
            status_code=400,
            detail="No se puede marcar como reparada sin asignar un costo de reparación"
        )

    orden_encontrada["estado"] = datos.nuevo_estado
    orden_encontrada["costo_reparacion"] = datos.costo_reparacion
    guardar_ordenes(ordenes)

    return {"mensaje": "Orden actualizada correctamente", "orden": orden_encontrada}
