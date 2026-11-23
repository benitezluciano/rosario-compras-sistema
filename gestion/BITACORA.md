# Bitácora de sesiones

> Reglas: ver [README.md](README.md#bitácora-de-sesiones). Las entradas nuevas van arriba y las viejas no se editan.

---

## 2026-11-23 — Sesión 3
**Duración aprox.:** (completar) · **Quién:** BenitezLuciano, con asistente (Claude Code)

- **Objetivo de la sesión:** Que el socio pueda ver lo que pidió. El historial mostraba los productos en una sola columna ("Productos Solicitados") que no se leía bien, y no había forma de ver el detalle ni de obtener un archivo.
- **Hecho:**
  - **Historial del socio rediseñado:**
    - Se quitó la columna "Productos Solicitados".
    - La lista tiene filtros por proveedor y por estado, y una columna con el número de remito.
    - Debajo de la lista se ve el detalle del pedido seleccionado, en cualquier estado: estado explicado en lenguaje simple, renglones con unidad, cantidad, precio congelado y subtotal. Si ya se entregó, también lo entregado según el remito.
  - **Nota de Pedido en PDF**, con el mismo estilo que el remito pero con precios: se puede abrir o guardar donde elija el socio.
  - **Botones nuevos:** "Ver remito" (si ya se entregó) y "Modificar pedido" (si está pendiente y la lista sigue habilitada), que lleva a la hoja de ese proveedor en Gestión de Pedidos.
  - Cada socio solo puede ver sus propios pedidos (lo valida el modelo).
  - La prueba integral suma el paso 8b: 12 de 12 pruebas OK. También se revisaron las pantallas con capturas y los dos PDF renderizados.
  - **Traspaso:** `ESTADO.md` quedó con una guía para quien retome y con cada pendiente explicado (por qué existe, qué archivos toca). Los pendientes se pasaron a Eros mediante un Issue.
- **Decidido:** (ver [DECISIONES.md](DECISIONES.md))
  - DEC-024 — Historial del socio con detalle del pedido y Nota de Pedido en PDF
- **Cerrado:**
  - El socio no tenía dónde ver lo que había enviado.
  - La columna "Productos Solicitados" era ilegible.
- **Pendiente / abierto:**
  - Guardar la cantidad original del pedido antes de que el ejecutivo la ajuste (para mostrar "pediste 10, se ajustó a 8").
  - Pantalla para cargar los datos fiscales de los socios.
  - Documentación (README, manual, walkthrough) al flujo nuevo.
  - Borrar `historial_pedidos.ui`, que quedó sin uso (falta confirmar).
  - Lo que sigue abierto de las sesiones anteriores: DEC-011, DEC-014 y observación #7. La lista completa está en [ESTADO.md](ESTADO.md).
- **Problemas o aprendizajes:**
  - La Nota de Pedido no se guarda en el proyecto, a diferencia de los remitos: un pedido pendiente cambia y el archivo quedaría desactualizado. Se genera cada vez desde la base.
  - El nombre del estado `Consolidado` no le dice nada al socio. En pantalla se muestra como "Enviado al proveedor" y `Procesado` como "Entregado".
- **Próximo paso:** Eros retoma desde `ESTADO.md` (sección "Para quien retoma el trabajo"). Los puntos que dependen del grupo (DEC-011, observación #7, DEC-014) van a la próxima reunión.
- **Dudas para retomar:** ¿Se borra `historial_pedidos.ui`? ¿El grupo ratifica DEC-011 y decide el manejo del stock (DEC-014)?

---

## 2026-11-23 — Sesión 2
**Duración aprox.:** (completar) · **Quién:** BenitezLuciano, con asistente (Claude Code)

- **Objetivo de la sesión:** Resolver tres temas urgentes surgidos de las pruebas:
  1. El archivo para enviar al proveedor al consolidar.
  2. El historial del ejecutivo.
  3. El rediseño de los remitos.
- **Hecho:**
  - Se commiteó y pusheó la Sesión 1 en la rama `feature/pedidos-por-proveedor` (antes `feature/limpieza-operativa`).
  - **Orden de compra:**
    - Al consolidar se genera el Excel en `ordenes_compra/`.
    - Se abre una ventana para abrirlo o enviarlo por mail al proveedor.
    - Las órdenes quedan registradas en la tabla `ORDENES_COMPRA`.
    - Se quitó "Órdenes por proveedor" y la planilla pasó a ser un borrador del proveedor seleccionado.
  - **Historial del ejecutivo:** pantalla nueva con pestañas de órdenes de compra (con sus pedidos, ver y reenviar), remitos (abrir o regenerar el PDF) y comprobantes (resultado del control).
  - **Remito estándar** según el modelo aportado:
    - Letra X y número `0001-00000001`.
    - Datos del emisor en `src/config/empresa.py` y del socio en `USERS`, todos simulados.
    - Unidad de cada artículo.
    - Referencias y observaciones automáticas.
    - Original y duplicado.
  - **Otros:**
    - `limpiar_db.py` borra también las órdenes.
    - `ordenes_compra/` está en `.gitignore`.
    - La prueba integral crea su propia base: 11 de 11 pruebas OK.
- **Decidido:** (ver [DECISIONES.md](DECISIONES.md))
  - DEC-018 — Al consolidar se genera automáticamente la orden de compra en Excel
  - DEC-019 — Las órdenes de compra se registran en la base
  - DEC-020 — Se quita "Órdenes por proveedor" y la planilla general pasa a ser un borrador del proveedor seleccionado
  - DEC-021 — La prueba integral crea su propia base con el seed (reemplaza a DEC-016)
  - DEC-022 — Historial del ejecutivo como pantalla propia con tres pestañas
  - DEC-023 — Rediseño del remito según el modelo estándar
- **Cerrado:**
  - El ejecutivo no tenía el archivo de la orden para enviar al proveedor.
  - El ejecutivo no tenía historial.
  - Los remitos no seguían el formato estándar.
  - Los PDF de remitos que faltaban (por ejemplo, los del seed) ya se pueden regenerar.
- **Pendiente / abierto:**
  - Pantalla para editar los datos fiscales de los socios.
  - Reemplazar los datos fiscales simulados por los reales.
  - Lo que sigue abierto de la Sesión 1: DEC-011, DEC-014, observación #7 y documentación.
- **Problemas o aprendizajes:**
  - En modo sin pantalla (`QT_QPA_PLATFORM=offscreen`) no hay fuentes: los PDF salen sin texto. Para verificar los PDF hay que correr con la plataforma normal.
  - Al aplicar cambios con scripts, los `\n` dentro de f-strings pueden convertirse en saltos de línea reales. Hay que compilar (`python -m compileall`) después de cada tanda.
- **Próximo paso:** Continuar con las modificaciones que defina BenitezLuciano.
- **Dudas para retomar:** ¿Cada ejecutivo debería ver solo sus proveedores en el historial (junto con la observación #7)?

---

## 2026-11-21 — Sesión 1
**Duración aprox.:** (completar) · **Quién:** BenitezLuciano, con asistente (Claude Code)

- **Objetivo de la sesión:** Analizar el repositorio, adaptar el portal del socio y corregir los tres errores clasificados como importantes en el análisis inicial.
- **Hecho:**
  - Análisis completo del repositorio. Se detectaron 7 observaciones técnicas: 3 importantes (#1 a #3), 4 medias (#4 a #7) y varias menores.
  - Portal del socio: el historial pasó a ser una pantalla propia en el menú lateral, y las listas se muestran como hojas estilo Excel con contador y subtotal.
  - Base de datos: `id_proveedor` en `PEDIDOS`; `lista_habilitada` y `fecha_habilitacion` en `PROVEEDORES`; `precio_unitario` en `DETALLE_PEDIDOS`; `id_pedido`, `id_proveedor` y `codigo_comercial` en `REMITOS`. `migrar_db` actualizado.
  - Modelos reescritos para trabajar por proveedor: catálogo, pedidos, consolidación, reparto y proveedores.
  - Pantallas actualizadas:
    - Socio: botón por hoja, "Enviar todo" con resumen y anulación de pedidos.
    - Módulo 1: botón Habilitar / Cerrar Lista.
    - Módulo 2: consolidación del proveedor seleccionado.
    - Módulo 3: sin "Todos los proveedores".
  - Seed reescrito (recrea las tablas) y base reseteada.
  - `tests/test_circuit_suite.py` reescrito para el flujo nuevo, sobre una copia temporal de la base: 8 de 8 pruebas OK. También se recorrieron todas las pantallas sin ventana visible, sobre una copia de la base.
- **Decidido:** (ver [DECISIONES.md](DECISIONES.md))
  - DEC-001 — Historial de Pedidos como pantalla propia en el menú lateral
  - DEC-002 — Listas de precios por proveedor como "hojas" estilo Excel
  - DEC-003 — Hoja "Resumen" en el portal del socio *(Propuesta)*
  - DEC-004 — Un pedido corresponde a un socio y a un único proveedor
  - DEC-005 — Cada artículo pertenece al catálogo de un único proveedor
  - DEC-006 — Ciclo de la lista de precios: habilitada / cerrada
  - DEC-007 — Un pedido pendiente por socio y proveedor, editable hasta consolidar
  - DEC-008 — La consolidación se hace por proveedor
  - DEC-009 — Reparto: proveedor obligatorio y un remito por pedido
  - DEC-010 — Precio congelado en cada renglón del pedido
  - DEC-011 — Una lista nueva actualiza el precio de los pedidos pendientes *(provisoria)*
  - DEC-012 — Hoja en 0 con pedido vigente: se anula con confirmación
  - DEC-013 — "Enviar todo" muestra un resumen por proveedor antes de confirmar
  - DEC-014 — Manejo del stock al asentar un comprobante *(Propuesta)*
  - DEC-015 — Resetear la base de datos con el seed
  - DEC-016 — Las pruebas del circuito corren sobre una copia temporal de la base
  - DEC-017 — Forma de trabajo: consultar antes de modificar
- **Cerrado:**
  - Observación #1: un pedido con varios proveedores quedaba incompleto en el reparto.
  - Observación #2: el reparto con "Todos los proveedores" duplicaba remitos y descontaba stock de más.
  - Observación #3: los artículos compartidos entre proveedores duplicaban filas en las consultas.
  - Observación #5: la notificación de ajustes mostraba un código de pedido equivocado.
  - Observación #6: la consolidación era global.
  - Observación #4, en parte: el comprobante ya no se asigna por defecto al proveedor 1.
- **Pendiente / abierto:**
  - Observación #4, resto: sumar o reemplazar el stock (DEC-014, bloqueado por decisión del grupo).
  - Observación #7: notificaciones compartidas entre ejecutivos.
  - Ratificar DEC-011 con el grupo.
  - Actualizar README, manual de usuario y walkthrough al flujo nuevo.
  - `tests/test_proveedores_email.py` escribe sobre la base real.
  - Commit de la rama `feature/limpieza-operativa`.
- **Problemas o aprendizajes:**
  - La causa común de los tres errores importantes era de **modelo de datos**: el pedido no registraba a qué proveedor pertenecía. Entender el proceso real del negocio (una lista negociada, un pedido por proveedor) resolvió los tres de raíz, mejor que parchear cada consulta.
  - SQLite no permite modificar un CHECK ni agregar una columna NOT NULL con clave foránea a una tabla existente. Por eso el seed recrea las tablas.
  - La consola de Windows (cp1252) falla al imprimir emojis: hay que correr los scripts con `PYTHONIOENCODING=utf-8`.
- **Próximo paso:** Prueba manual con `python main.py` y commit.
- **Dudas para retomar:** ¿El negocio opera con depósito y stock acumulado, o con paso directo (DEC-014)? ¿El grupo está de acuerdo con DEC-011?
