# Modelo: `reparto_model.py`

## Propósito Principal
Es el modelo más robusto y complejo del sistema. Encargado de orquestar la sofisticada lógica del Caso de Uso 2 (Reparto Automático). Gestiona las operaciones de extracción de datos, comprobación de integridad y asignación del stock remanente, además del rastro de auditoría transaccional con sus respectivos remitos.

## Dependencias e Interacciones
- **Llama a**: La clase context manager `Database` y a la librería `datetime` nativa de Python.
- **Es llamado por**: `RepartoController`.

## Métodos y Lógica Clave
- `obtener_pedidos_consolidados()`: Trae los pedidos listos para su reparto y utiliza funciones avanzadas de SQLite como `group_concat` para consolidar el detalle de múltiples artículos de un pedido en una sola línea textual y resumida para la vista de control.
- `validar_stock_vs_pedidos()`: Algoritmo heurístico que contrasta el acumulado demandado de artículos frente a la columna transaccional de `cantidad_stock`. En caso de que se detecte una sobredemanda inasumible con el stock físico disponible, aplica un **Algoritmo de Prorrateo Matemático Equitativo**:
  - Aplica un factor base `(disponible/total)` extrayendo la parte entera para asegurar un piso base uniforme de unidades para todos los solicitantes.
  - El residuo o "sobrante numérico de las divisiones con coma" se ordena por su fracción matemáticamente exacta y se reparte en un sistema de asignación *Round-Robin* (asignando +1 unidad entera al grupo con mayores restos hasta liquidar todo el remanente físico exacto). Esto genera el diccionario objeto de `ajustes` para proponer al usuario humano la solución óptima automatizada (Excepción E1).
- `ejecutar_reparto_masivo(ajustes)`: Flujo transaccional maestro que iterativamente descuenta las unidades físicas consolidadas (aplicando los dicts de ajuste equitativo si los hubiera), cambia dinámicamente el estado individual de cada solicitud en la tabla de `PEDIDOS` a la fase de 'Procesado', guarda la corrida general consolidada en la tabla `PROCESOS_REPARTO` y genera de manera distribuida los registros inter-conectados en la tabla `REMITOS` que servirán al cadete.
