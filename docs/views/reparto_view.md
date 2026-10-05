# Vista: `reparto_view.py`

## Propósito Principal
Es el componente táctico de la Capa de Visualización para el panel de asignación masiva de entregas (CU-002). Su función primaria consiste en cargar una consola logística visual para el monitoreo panorámico de los pedidos consolidados pendientes e intervenir dinámicamente para solicitar permisos, decisiones y confirmaciones tácticas al humano operador. 

## Dependencias e Interacciones
- **Llama a**: Archivo XML nativo del diseño `reparto_automatico.ui`, y dependencias robustas del paquete de PyQt6 (`QWidget`, `QMessageBox`, `uic`, y enums estructurales de `Qt`).
- **Es llamado por**: `RepartoController` (quien inyecta mutaciones sobre su estado) y por `main.py` durante el bootstrapping del menú base general.

## Lógica Clave
- **Carga de Archivo Físico**: Lee dinámicamente e incorpora los objetos alojados en el layout pre-compilado en `reparto_automatico.ui`.
- **Rellenado y Estilización de Grilla de Consolidación (`cargar_tabla`)**: Instala el resumen tabular de pedidos, dotando al usuario final de una visión limpia ("Snapshot" general) de su carga o compromiso operativo actual. Se acopla de manera reactiva para auto-ajustar las anchuras en la visualización de la pantalla al invocar la función estándar de adaptabilidad de `resizeColumnToContents`.
- **Feedback Constante (`actualizar_estado_interfaz`)**: Agrupa y abstrae toda lógica de mutaciones destinadas a controlar los hilos visuales informativos en su etiqueta dinámica, mostrando en tiempo real un rastro textual (por ejemplo, los marcadores: "Procesando..." de carga base, o "Asignación Cancelada" en interrupción).
- **Control Lógico-Gráfico Interactivo de Alerta (Excepción E1)**: Posee el complejo método interactivo de `mostrar_alerta_ajuste(discrepancias)`. Tras recibir el análisis de un evento de quiebre algorítmico sobre el stock físico desde su Controlador maestro, esta vista transiciona abriendo un cuadro de diálogo del tipo `Question`. En lugar de poseer una limitante opción binaria estática ("Sí/No"), este sistema concatena un cuerpo dinámico tipo lista anidada analizando exhaustivamente y de forma pormenorizada (con métricas exactas solicitadas versus métricas exactas físicas) para plantear la propuesta matemática elaborada por el Modelo, inyectándole directamente botones nativos personalizados (`"Aceptar Ajuste"`, `"Cancelar"`) con retorno booleano directo al núcleo de asignación de SQLite.
