# Modelo: `pedido_model.py`

## Propósito Principal
Es la capa de acceso a datos para el Caso de Uso 1 (Carga Digital de Pedido). Contiene la lógica responsable de leer el catálogo de precios actual de la base de datos y de persistir la solicitud del socio a nivel físico.

## Dependencias e Interacciones
- **Llama a**: La clase context manager `Database` de `src.database`.
- **Es llamado por**: `PedidoController` (quien le pasa los datos limpiados desde la Vista).

## Métodos Clave
- `obtener_articulos()`: Realiza un `JOIN` entre `ARTICULOS` y `PRECIOS_NEGOCIADOS` extrayendo el precio final unitario, devolviendo diccionarios iterables para popular la tabla visual.
- `crear_pedido(id_socio, estado, detalles)`: Función transaccional (`try/except`) que efectúa múltiples `INSERT`: 
  1. Graba el encabezado del pedido en la tabla `PEDIDOS`.
  2. Itera sobre el array de `detalles` e inserta los renglones correspondientes dentro de `DETALLE_PEDIDOS`. 
  Efectúa un `conn.rollback()` en caso de fallas de integridad en cualquiera de los inserts, protegiendo así la coherencia de datos y evitando inserciones parciales de pedidos huérfanos.
