"""
Datos de la empresa emisora de los documentos (remitos).

IMPORTANTE: los datos fiscales son SIMULADOS. Antes de usar el sistema en producción
hay que reemplazarlos por los reales y poner DATOS_SIMULADOS = False (eso quita la
leyenda de "datos simulados" del pie de los remitos).
"""

EMPRESA = {
    "razon_social": "Rosario Compras S.A.",
    "cuit": "XX-XXXXXXXX-X",
    "condicion_iva": "Completar",
    "domicilio": "Completar (domicilio de origen), Rosario, Santa Fe",
    "localidad": "Rosario",
    "email": "contacto@rosariocompras.com",
}

# Remito no fiscal: letra "X" (documento no válido como factura).
# La letra "R" corresponde a remitos autorizados por AFIP (con CAI/CAE).
LETRA_REMITO = "X"

# Punto de venta de los remitos: el número se arma como 0001-00000001.
PUNTO_VENTA_REMITOS = 1

# Muestra en el pie de los remitos que los datos fiscales son de prueba.
DATOS_SIMULADOS = True
