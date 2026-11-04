from fastapi import APIRouter, HTTPException
from databse import leer_base_datos, obtener_producto, guardar_base_datos
from schemas import ProductoCreate

router = APIRouter(tags=["Inventario"])

# Nuestro primer endpoint
@router.get("/")
async def ruta_principal():
    return {"mensaje": "¡Bienvenido a mi primera API Rest!"}

@router.get("/estado")
async def estado_servidor():
    return {"status": "En línea", "servicios": "Operativos sin ningún inconveniente"}

@router.get("/suma")
async def sumar():
    numero1 = 5
    numero2 = 4
    resultado = numero1 + numero2
    return resultado

@router.get("/productos")
async def listar_productos():
    datos = await leer_base_datos()
    return {"cantidad": len(datos), "productos": datos}

@router.get("/productos/{codigo_producto}")
async def buscar_un_producto(codigo_producto: str):
    try:
        producto = await obtener_producto(codigo_producto)
        return producto
    except KeyError:
        raise HTTPException(status_code=404, detail="El producto solicitado no existe en la BD")

@router.get("/categorias")
async def listar_categorias():
    datos = await leer_base_datos()
    categorias = []
    for dato in datos:
        if dato["categoria"] not in categorias:
            categorias.append(dato["categoria"])
    return {"categorias": categorias}

@router.get("/alertas/stock")
async def stock_critico():
    datos = await leer_base_datos()
    productos_criticos = []
    for dato in datos:
        if dato["stock"] < 3:
            productos_criticos.append(dato)
    return {"productos_criticos": productos_criticos}

@router.get("/productos/buscar/{palabra_clave}")
async def buscar_por_nombre(palabra_clave: str):
    datos = await leer_base_datos()
    productos_encontrados = []
    for dato in datos:
        if palabra_clave.lower() in dato["nombre"].lower():
            productos_encontrados.append(dato)
    return {"productos": productos_encontrados}

@router.post("/productos", status_code=201)
async def registrar_nuevo_producto(producto: ProductoCreate):
    datos = await leer_base_datos()

    # 1. Validar que el producto no exista
    for dato in datos:
        if dato["codigo"] == producto.codigo:
            raise HTTPException(status_code=400, detail="El codigo de producto ya existe.")

    # 2. Convertir la clase a un diccionario
    nuevo_producto = producto.model_dump()

    # 3. Guardar
    datos.append(nuevo_producto)
    await guardar_base_datos(datos)

    return {"mensaje": "Producto registrado correctamente", "Producto": nuevo_producto}

# Put, actualizar inventario
@router.put("/productos/{codigo_producto}")
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