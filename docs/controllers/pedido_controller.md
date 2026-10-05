# Controlador: `pedido_controller.py`

## Propósito Principal
Es el gestor o mediador lógico para el flujo integral de Carga de Pedidos (CU-001). Centraliza las validaciones de las entradas del usuario (evitando que comandos corruptos lleguen a la BD) y traslada la instrucción final aprobada hacia el modelo para su grabación.

## Dependencias e Interacciones
- **Llama a**: `PedidoModel` (para consultas base y envíos DML) y `PedidoView` (para recibir inputs y emitir popups).
- **Es llamado por**: El script central `main.py` durante la fase de inyección o enlazado.

## Lógica Clave
- **Inicializador de Estado (`inicializar`)**: Extrae el listado completo y vigente del catálogo desde el modelo transaccional y le ordena explícitamente a su propia vista que repinte por completo el panel para dejarlo preparado para una nueva interacción humana.
- **Motor Validador Lógico (`guardar_pedido`)**:
  - Captura y responde directamente al evento o *click* del botón primario de guardar.
  - Itera secuencialmente el *backend* de la tabla visual para recolectar e interpretar todas y cada una de las cantidades ingresadas, omitiendo automáticamente y de forma silenciosa las filas vacías (es decir, cantidades idénticas a 0).
  - Efectúa validaciones estrictas de reglas de negocio duras: prohíbe formalmente que un usuario intente crear un pedido estéril (pedido vacío sin volumen neto), y corta o interrumpe instantáneamente el flujo enviando alertas si detecta montos numéricos negativos que pudieran llegar a corromper las transacciones contables del almacén.
  - Habiendo superado toda barrera, instruye finalmente a su modelo a disparar su procedimiento `crear_pedido()`. Si el feedback del motor es positivo, reinicia limpiamente la pantalla (`inicializar()`) devolviendo el control al inicio.
