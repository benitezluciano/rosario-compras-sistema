import hashlib
import uuid

def generar_codigo_pedido(id_pedido: int, fecha: str = "") -> str:
    """
    Genera un identificador comercial ofuscado para pedidos tipo 'RC-ORD-8F2A1C'.
    Protege el secreto del volumen comercial impidiendo inferir la correlatividad.
    """
    semilla = f"PEDIDO-{id_pedido}-{fecha}-ROSARIO-COMPRAS-SECRET"
    hash_hex = hashlib.sha256(semilla.encode('utf-8')).hexdigest()[:6].upper()
    return f"RC-ORD-{hash_hex}"

def generar_codigo_comprobante(id_proveedor: int = 0) -> str:
    """
    Genera un número de comprobante interno automático único tipo 'CMP-2026-F89B21'.
    """
    token = uuid.uuid4().hex[:6].upper()
    return f"CMP-REC-{token}"

def generar_codigo_remito(id_remito: int, id_socio: int = 0) -> str:
    """
    Genera un identificador comercial ofuscado para remitos tipo 'RC-REM-B7C410'.
    """
    semilla = f"REMITO-{id_remito}-{id_socio}-ROSARIO-COMPRAS"
    hash_hex = hashlib.sha256(semilla.encode('utf-8')).hexdigest()[:6].upper()
    return f"RC-REM-{hash_hex}"
