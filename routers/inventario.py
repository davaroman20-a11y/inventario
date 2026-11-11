from fastapi import APIRouter, HTTPException

from databse import guardar_base_datos, leer_base_datos, obtener_producto
from core.schemas.schemas import ProductoCreate

router = APIRouter(prefix="", tags=["Inventario"])


@router.get("/estado")
async def estado_servidor():
    return {"status": "En línea", "servicios": "Operativos sin ningún inconveniente"}


@router.get("/suma")
async def sumar():
    numero1 = 5
    numero2 = 4
    return {"resultado": numero1 + numero2}


@router.get("/productos")
async def listar_productos():
    datos = await leer_base_datos()
    return {"cantidad": len(datos), "productos": datos}


@router.get("/productos/{codigo_producto}")
async def buscar_un_producto(codigo_producto: str):
    try:
        return await obtener_producto(codigo_producto)
    except KeyError:
        raise HTTPException(status_code=404, detail="El producto solicitado no existe en la BD")


@router.get("/categorias")
async def listar_categorias():
    datos = await leer_base_datos()
    categorias = []
    for dato in datos:
        if dato.get("categoria") and dato["categoria"] not in categorias:
            categorias.append(dato["categoria"])
    return {"categorias": categorias}


@router.get("/alertas/stock")
async def stock_critico():
    datos = await leer_base_datos()
    productos_criticos = []
    for dato in datos:
        if dato.get("stock", 0) < 3:
            productos_criticos.append(dato)
    return {"productos_criticos": productos_criticos}


@router.get("/productos/buscar/{palabra_clave}")
async def buscar_por_nombre(palabra_clave: str):
    datos = await leer_base_datos()
    productos_encontrados = []
    for dato in datos:
        nombre = str(dato.get("nombre", "")).lower()
        if palabra_clave.lower() in nombre:
            productos_encontrados.append(dato)
    return {"productos": productos_encontrados}


@router.post("/productos", status_code=201)
async def registrar_nuevo_producto(producto: ProductoCreate):
    datos = await leer_base_datos()

    for dato in datos:
        if dato.get("codigo") == producto.codigo:
            raise HTTPException(status_code=400, detail="El código de producto ya existe.")

    nuevo_producto = producto.model_dump()
    datos.append(nuevo_producto)
    await guardar_base_datos(datos)

    return {"mensaje": "Producto registrado correctamente", "producto": nuevo_producto}


@router.put("/productos/{codigo_producto}")
async def actualizar_producto(codigo_producto: str, producto_actualizado: ProductoCreate):
    datos = await leer_base_datos()
    for posicion, dato in enumerate(datos):
        if dato.get("codigo") == codigo_producto:
            datos[posicion] = producto_actualizado.model_dump()
            datos[posicion]["codigo"] = codigo_producto
            await guardar_base_datos(datos)
            return {"mensaje": "Producto actualizado", "producto": datos[posicion]}

    raise HTTPException(status_code=404, detail="Producto no encontrado")