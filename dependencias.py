from fastapi import Header, HTTPException, Query

async def verificar_api_key(x_api_key: str= Header(..., description="API Key secreta del taller")):
    if x_api_key != "Sena2026":
        raise HTTPException(status_code=401, detail="API Key inválida")
    return x_api_key

def parametros_paginacion(
        skip: int = Query(0, description="cuántos registros saltar"),
        limit: int = Query(10, description="límite de registros a devolver")
):
        return {"skip": skip, "limit": limit}

async def simular_base_datos():
    print("1. [DEPENDENCIA] abriendo la conexion con el json")
    yield "conexión simulada"
    print("3. [DEPENDENCIA] Cerrando archivo json y liberando memoria...")



async def verificar_gerente(x_role: str = Header(..., alias="X-Role", description="Rol del usuario: Gerente o Auditor")):
    if x_role != "Gerente":
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere el rol Gerente")
    return x_role



async def verificar_auditor(x_role: str = Header(..., alias="X-Role", description="Rol del usuario: Gerente o Auditor")):
    if x_role not in ("Gerente", "Auditor"):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere el rol Gerente o Auditor")
    return x_role
