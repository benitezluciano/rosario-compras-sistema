# Vista: `pedido_view.py`

## Propósito Principal
Clase encargada de construir y gobernar la interfaz visual de la carga de pedidos (CU-001). Actúa como un *Widget* integrado en la arquitectura que carga y renderiza su estructura base a partir del XML diseñado externamente con Qt Designer (`carga_pedido.ui`).

## Dependencias e Interacciones
- **Llama a**: Archivo XML de Qt Designer `carga_pedido.ui` y componentes directos de PyQt6 (`QWidget`, `uic`, `QTableWidgetItem`, `QMessageBox`).
- **Es llamado por**: `PedidoController` y `main.py` (durante la inyección de dependencias general del layout padre).

## Lógica Clave
- **Carga Dinámica de UI**: En su método inicializador o constructor (`__init__`) utiliza el motor nativo `uic.loadUi()` para interpretar y fusionar dinámicamente el esqueleto XML de la pantalla dentro de la instancia de la clase Python actual, permitiendo utilizar objetos como si estuvieran hardcodeados.
- **Poblado de Grilla de Componentes Visuales (`cargar_articulos`)**: Interviene la tabla principal o Grilla iterando sobre los catálogos traídos del modelo. Transforma datos estáticos al formato enriquecido `QTableWidgetItem`, bloqueando su edición como si fueran variables de solo lectura, con la única excepción de la columna clave de "Cantidad". Para permitir un rápido rastreo o trazabilidad posterior por parte de su Controlador, encripta silenciosamente los identificadores numéricos de base de datos de los artículos utilizando el método `setData` en el espacio de metadatos ocultos del backend visual de la primera celda.
- **Comportamiento Reactivo (`calcular_totales`)**: Implementa un ciclo de escucha permanente conectándose a la señal o trigger o nativo `itemChanged` emanada intrínsecamente por la tabla en cada tipeo. Al detectar modificaciones específicas del usuario en cualquier celda de la columna "Cantidad", re-evalúa los montos numéricos cruzándolos automáticamente con el multiplicador constante de su celda de "Precio" para sobreescribir la columna de "Subtotal", imitando de manera fidedigna la responsividad instantánea de una "Hoja de Cálculo" común y retroalimentando en cascada la etiqueta acumuladora inferior.
- **Sistema de Pop-ups Interactivos**: Integra en su catálogo un sub-sistema de envoltorios (Wrappers) estandarizados sobre `QMessageBox` para invocar reportes e interrupciones en la pantalla o reportar logs limpios procedentes del rastro del Controlador.
