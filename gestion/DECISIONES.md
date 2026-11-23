# Registro de decisiones

> Reglas del registro: ver [README.md](README.md#registro-de-decisiones). Las decisiones nunca se borran; si cambian, se marcan como `Reemplazada`.

---

### DEC-001 — Historial de Pedidos como pantalla propia en el menú lateral

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** En el portal del socio, "Gestión de Pedidos" y "Historial de Pedidos" eran dos pestañas de la misma pantalla. Se busca que "Gestión de Pedidos" se ocupe solo de ver las listas habilitadas y cargar pedidos.
- **Decisión:** El historial pasa a ser una pantalla independiente, accesible desde un segundo ítem del menú lateral del socio ("📜 Historial de Pedidos"), debajo de "🛍️ Gestión de Pedidos".
- **Alternativas consideradas:**
  - Pestaña dentro de la misma pantalla: era la situación anterior, justamente la que se quería cambiar.
  - Ventana emergente: tapa o bloquea la ventana principal, queda fuera de la navegación y rompe la consistencia con los módulos del ejecutivo, que se navegan desde el menú lateral.
- **Consecuencias:** Archivos nuevos `historial_view.py`, `historial_pedidos.ui` y `historial_controller.py`. `main.py` diferencia las dos pantallas del socio. A futuro, el historial puede mostrar el detalle de los renglones al seleccionar un pedido.
- **Relacionado con:** DEC-002.

---

### DEC-002 — Listas de precios por proveedor como "hojas" estilo Excel

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** Las listas de todos los proveedores se mostraban como recuadros apilados con scroll vertical, lo que dificultaba ubicarse cuando hay varias listas.
- **Decisión:** Cada lista se muestra en una hoja propia, con **pestañas en la parte inferior** (como Excel). Cada pestaña muestra un **contador** de productos cargados, por ejemplo "Lácteos del Litoral (2)", y cada hoja tiene su **subtotal** al pie. El total general queda fuera de las hojas.
- **Alternativas consideradas:**
  - Recuadros apilados (situación anterior): poco práctico con muchas listas.
  - Pestañas arriba: funcionalmente igual, pero se prefirió la analogía directa con las hojas de Excel.
- **Consecuencias:** Estilo `QTabBar::tab:bottom` agregado en `theme.py`. Al volver a la pantalla se conserva la hoja activa. Con DEC-004, cada hoja pasa a ser un pedido independiente.
- **Relacionado con:** DEC-003, DEC-004.

---

### DEC-003 — Hoja "Resumen" en el portal del socio

- **Fecha:** 2026-11-21
- **Estado:** Propuesta
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** Con varias hojas, al socio le puede costar revisar todo lo cargado antes de enviar.
- **Decisión:** (En evaluación) Agregar una primera hoja "🧾 Resumen" que muestre solo lo cargado en todas las hojas, agrupado por proveedor. Se evaluará más adelante.
- **Alternativas consideradas:**
  - No agregarla y confiar en el contador por pestaña (DEC-002) y en el resumen previo de "Enviar todo" (DEC-013): es la situación actual.
- **Consecuencias:** Sin cambios en código por ahora.
- **Relacionado con:** DEC-002, DEC-013.

---

### DEC-004 — Un pedido corresponde a un socio y a un único proveedor

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** El sistema permitía un único pedido con artículos de varios proveedores, pero ni el detalle del pedido ni el remito registraban a qué proveedor pertenecía cada renglón. Eso causaba tres errores graves:
  1. Al repartir un proveedor, el pedido entero pasaba a "Procesado" y los artículos de los otros proveedores nunca se repartían.
  2. Con "Todos los proveedores" se generaban remitos duplicados con el mismo número y el stock se descontaba varias veces.
  3. Los artículos con precio en dos proveedores duplicaban filas en las consultas.

  El proceso real es: el ejecutivo negocia con un proveedor, importa su lista final y la habilita, y cada socio pide sobre esa lista.
- **Decisión:** Cada pedido es de **un socio para un proveedor** (`PEDIDOS.id_proveedor`). Si hay varias listas habilitadas, el socio puede enviar hoja por hoja o usar **"Enviar todo"**, que es solo una comodidad: el sistema igual genera **un pedido separado por proveedor**.
- **Alternativas consideradas:**
  - Mantener el pedido multi-proveedor y agregar `id_proveedor` a `DETALLE_PEDIDOS`: obligaba a revisar casi todas las consultas y no reflejaba el proceso real.
  - Dividir el pedido por proveedor al consolidar: agregaba complejidad y estados intermedios ("entrega parcial") innecesarios.
- **Consecuencias:**
  - Las observaciones #1, #2 y #3 quedan resueltas de raíz. Todas las consultas filtran por el proveedor del pedido.
  - No se puede eliminar un proveedor que tenga pedidos.
  - El portal del socio tiene un botón por hoja más el botón "Enviar todo".
- **Relacionado con:** DEC-005 a DEC-013.

---

### DEC-005 — Cada artículo pertenece al catálogo de un único proveedor

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** Al importar una lista, el sistema buscaba el artículo **por nombre en todo el catálogo**. Si coincidía con el de otro proveedor, lo reutilizaba. En la base de pruebas llegó a haber 16 artículos compartidos entre proveedores.
- **Decisión:** La importación busca los artículos **solo dentro del catálogo del proveedor**, primero por código del proveedor y, si no hay coincidencia, por nombre. Si dos proveedores venden el mismo producto, son dos artículos distintos.
- **Alternativas consideradas:**
  - Artículo compartido con un precio por proveedor: permitiría comparar precios, pero genera ambigüedad sobre a qué proveedor se le pide y no corresponde al proceso, donde cada lista es propia del proveedor.
- **Consecuencias:** Una lista ya no "pisa" artículos de otro proveedor. El campo `id_articulo_proveedor` se usa como código del proveedor.
- **Relacionado con:** DEC-004.

---

### DEC-006 — Ciclo de la lista de precios: habilitada / cerrada

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** Había que definir cuándo puede pedir el socio de una lista y cuándo deja de poder.
- **Decisión:** La lista funciona **por ciclos**:
  - Se **habilita** al importar una lista nueva, o manualmente con el botón "Habilitar / Cerrar Lista" del Módulo 1.
  - Se **cierra automáticamente** al consolidar los pedidos de ese proveedor.
  - El socio **solo ve las listas habilitadas**.
- **Alternativas consideradas:**
  - Lista siempre abierta desde que se importa: no refleja que cada lista nace de una negociación para un ciclo de pedidos.
  - Tabla nueva `LISTAS_PRECIOS` con estados y vínculo de cada pedido a su lista: más trazable, pero más compleja. La trazabilidad de precios ya queda cubierta con DEC-010. Además, esa tabla había sido eliminada en la migración 0002.
- **Consecuencias:** Columnas `lista_habilitada` y `fecha_habilitacion` en `PROVEEDORES`. Al habilitar se notifica a los socios. Si se cierra una lista con pedidos pendientes, estos se conservan y pueden consolidarse, pero el socio no puede modificarlos.
- **Relacionado con:** DEC-004, DEC-008, DEC-010.

---

### DEC-007 — Un pedido pendiente por socio y proveedor, editable hasta consolidar

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** Había que definir si un socio puede tener varios pedidos abiertos a la vez.
- **Decisión:** Un socio puede tener **un pedido "Pendiente" por cada proveedor**, todos a la vez. Cada uno se puede modificar mientras no se consolide.
- **Alternativas consideradas:**
  - Un único pedido pendiente por socio: incompatible con DEC-004.
  - Varios pedidos pendientes para el mismo proveedor: complica la consolidación y no aporta valor.
- **Consecuencias:** Si se vuelve a enviar una hoja que ya tiene pedido vigente, se actualiza ese mismo pedido.
- **Relacionado con:** DEC-004, DEC-012.

---

### DEC-008 — La consolidación se hace por proveedor

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** "Confirmar consolidación" pasaba a "Consolidado" **todos** los pedidos pendientes, aunque la pantalla trabajaba por proveedor (observación #6).
- **Decisión:** Consolidar actúa **solo sobre el proveedor seleccionado** y cierra su lista (DEC-006). Los pedidos de otros proveedores no se modifican.
- **Alternativas consideradas:**
  - Consolidación global (situación anterior): obligaba a cerrar todos los proveedores a la vez, aunque cada uno tenga su propio ciclo.
- **Consecuencias:**
  - El selector muestra cuántos pedidos pendientes tiene cada proveedor.
  - No se puede consolidar con ajustes sin guardar en la matriz.
  - Se corrigió también el código de pedido equivocado en la notificación de ajustes (observación #5).
- **Relacionado con:** DEC-006.

---

### DEC-009 — Reparto: proveedor obligatorio y un remito por pedido

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** La opción "Todos los proveedores" del Módulo 3 duplicaba remitos y, al asentar un comprobante, lo asignaba por defecto al proveedor 1. Además, el número de remito se derivaba de (pedido, socio) y se repetía entre proveedores.
- **Decisión:** Se quita "Todos los proveedores" y es obligatorio elegir el proveedor, porque cada entrega llega de un proveedor con su comprobante. Cada pedido genera **un remito**, vinculado a pedido y proveedor, con un **número único** derivado de su `id_remito`.
- **Alternativas consideradas:**
  - Mantener "Todos" generando un remito por cada (pedido, proveedor): técnicamente posible, pero no refleja la realidad de una entrega por proveedor.
- **Consecuencias:** Columnas `id_pedido`, `id_proveedor` y `codigo_comercial` en `REMITOS`. La parte de "proveedor 1 por defecto" de la observación #4 quedó resuelta.
- **Relacionado con:** DEC-004, DEC-014.

---

### DEC-010 — Precio congelado en cada renglón del pedido

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** Los totales del historial se recalculaban con el precio actual de la lista. Si el ejecutivo importaba una lista nueva, cambiaban los montos de pedidos viejos.
- **Decisión:** Se guarda el precio en `DETALLE_PEDIDOS.precio_unitario` al registrar el pedido. Al consolidar, ese precio queda fijo.
- **Alternativas consideradas:**
  - Seguir calculando con el precio vigente: los pedidos históricos dejan de ser confiables.
  - Vincular cada pedido a una versión de la lista (tabla `LISTAS_PRECIOS`): más complejo, descartado en DEC-006.
- **Consecuencias:** El historial, la consolidación, las órdenes de compra y el control de recepción usan el precio del renglón.
- **Relacionado con:** DEC-006, DEC-011.

---

### DEC-011 — Una lista nueva actualiza el precio de los pedidos pendientes

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** Si el ejecutivo importa una lista nueva de un proveedor mientras hay pedidos "Pendiente" de ese proveedor, hay que definir con qué precio quedan.
- **Decisión:** Los pedidos **pendientes** toman los precios nuevos, porque todavía no se enviaron. Los **consolidados** conservan su precio congelado. **Aplicada en forma provisoria:** falta ratificarla con el grupo.
- **Alternativas consideradas:**
  - Mantener el precio original del pedido pendiente: el socio pediría a un precio que ya no es el negociado.
  - Anular los pendientes y pedir que se carguen de nuevo: costoso para los socios.
- **Consecuencias:** La importación recalcula `precio_unitario` de los renglones pendientes del proveedor. Si el grupo decide otra cosa, se registra una decisión nueva que reemplace a esta.
- **Relacionado con:** DEC-010.

---

### DEC-012 — Hoja en 0 con pedido vigente: se anula con confirmación

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** Había que definir qué pasa si el socio deja en 0 todas las cantidades de una hoja que ya tenía pedido vigente y guarda.
- **Decisión:** El pedido **se anula** (se elimina), previa confirmación del socio. Se notifica al ejecutivo.
- **Alternativas consideradas:**
  - Mostrar un error e impedirlo: el socio no tendría forma de retirar un pedido que ya no quiere.
- **Consecuencias:** Solo es posible mientras el pedido está "Pendiente". El tipo de notificación nuevo `pedido_anulado` tiene su ícono en el centro de notificaciones.
- **Relacionado con:** DEC-007.

---

### DEC-013 — "Enviar todo" muestra un resumen por proveedor antes de confirmar

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** "Enviar todo" puede crear, modificar y anular varios pedidos de una vez.
- **Decisión:** Antes de procesar se muestra una confirmación con el resumen por proveedor (acción, cantidad de productos y monto) y el total. Solo se procesan las hojas que cambiaron.
- **Alternativas consideradas:**
  - Enviar sin confirmación: riesgo de enviar pedidos por error.
- **Consecuencias:** Los pedidos nuevos y modificados se guardan juntos en una sola operación: si uno falla, no se guarda ninguno.
- **Relacionado con:** DEC-004, DEC-003.

---

### DEC-014 — Manejo del stock al asentar un comprobante

- **Fecha:** 2026-11-21
- **Estado:** Propuesta
- **Participantes:** BenitezLuciano, asistente (Claude Code) — pendiente de discutir con el grupo
- **Contexto:** Al asentar un comprobante, el stock del artículo se **reemplaza** por la cantidad recibida, en lugar de sumarse (observación #4). Ejemplo: había 10 kg en depósito, llegan 20 kg y los socios piden 25. El sistema considera 20 disponibles y prorratea, cuando en realidad hay 30.
- **Decisión:** (Pendiente) Elegir entre:
  - **A) Depósito con stock acumulado:** lo que sobra se usa en el próximo ciclo. Hay que **sumar** y evitar que un comprobante se asiente dos veces.
  - **B) Paso directo (cross-docking):** la mercadería llega y se reparte enseguida. El reparto usa **solo lo recibido en ese comprobante**, y lo que sobra se registra como excedente para que el ejecutivo decida.
- **Alternativas consideradas:** las dos de arriba. El asistente ve el proceso descripto más cerca de B, pero `circuito.md` menciona "asentar el stock real en depósito", lo que sugiere A.
- **Consecuencias:** Mientras no se decida, el código mantiene el comportamiento actual (reemplazar).
- **Relacionado con:** DEC-009.

---

### DEC-015 — Resetear la base de datos con el seed

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** La base tenía datos inconsistentes generados durante las pruebas: artículos compartidos y pedidos procesados a medias.
- **Decisión:** Se descartan esos datos y se resetea la base con `seeds/seed_db.py`. El seed ahora **borra y recrea las tablas**, para que el esquema quede con todas las columnas, claves foráneas y restricciones actualizadas.
- **Alternativas consideradas:**
  - Escribir una migración que corrija los datos existentes: no se justificaba porque eran datos de prueba.
- **Consecuencias:** El seed carga 16 pedidos de un solo proveedor cada uno:
  - 10 "Pendiente" en 4 listas habilitadas.
  - 4 "Consolidado" en 2 listas cerradas.
  - 2 "Procesado" con remito.

  Ejecutar el seed **borra todos los datos** de `database.db`. `migrar_db` sigue completando columnas faltantes en bases viejas.
- **Relacionado con:** DEC-004.

---

### DEC-016 — Las pruebas del circuito corren sobre una copia temporal de la base

- **Fecha:** 2026-11-21
- **Estado:** Reemplazada por DEC-021
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** `tests/test_circuit_suite.py` escribía sobre la `database.db` real: creaba pedidos, importaba listas y generaba PDFs.
- **Decisión:** La suite copia la base y usa una carpeta de PDFs temporales, y borra todo al terminar.
- **Alternativas consideradas:**
  - Pasar a pytest con fixtures: mejor a largo plazo, pero excedía el alcance de esta sesión.
- **Consecuencias:** Se puede correr la suite sin perder los datos de prueba. `tests/test_proveedores_email.py` **todavía** escribe sobre la base real (queda pendiente).
- **Relacionado con:** DEC-015.

---

### DEC-017 — Forma de trabajo: consultar antes de modificar

- **Fecha:** 2026-11-21
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** Las correcciones se hacen paso a paso y las decisiones de negocio son del equipo.
- **Decisión:** Antes de modificar cualquier archivo, el asistente presenta la propuesta (qué cambia, alternativas y preguntas) y espera la aprobación explícita.
- **Alternativas consideradas:**
  - Que el asistente aplique cambios directamente: rápido, pero quita control sobre decisiones de negocio.
- **Consecuencias:** Cada cambio pasa por una ronda de preguntas. Las decisiones quedan registradas en este archivo.
- **Relacionado con:** —

---

### DEC-018 — Al consolidar se genera automáticamente la orden de compra en Excel

- **Fecha:** 2026-11-23
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** Al consolidar, el sistema solo cambiaba estados, cerraba la lista y mostraba mensajes. No generaba ningún archivo. Los botones de exportar (planilla general y órdenes por proveedor) tomaban todos los proveedores y solo pedidos "Pendiente", así que después de consolidar ya no había forma de obtener la orden para enviarla al proveedor.
- **Decisión:**
  - Al consolidar un proveedor se genera su **orden de compra en Excel (.xlsx)**, el mismo formato con el que el proveedor envía su lista.
  - Tiene un encabezado formal (Rosario Compras, proveedor, N° de orden `RC-OC-XXXXXX`, fecha, ejecutivo) y los **totales por artículo** (código del proveedor, detalle, cantidad, precio, subtotal y total), **sin desglose por socio**.
  - Se guarda en la carpeta fija `ordenes_compra/`.
  - Al terminar se abre una ventana con la orden y los botones **Abrir archivo**, **Abrir carpeta** y **Enviar al proveedor**. Este último usa la ventana de mail que ya existía, con la orden adjunta y el email del proveedor completado.
  - Primero se genera el archivo y después se consolida, en una sola operación: si el archivo falla, no se consolida nada.
- **Alternativas consideradas:**
  - PDF o Excel y PDF: el PDF es más formal, pero el proveedor trabaja con Excel.
  - Incluir el desglose por socio: no hace falta porque el proveedor entrega todo a Rosario Compras y el reparto lo hace el sistema.
  - Preguntar dónde guardar el archivo cada vez: agrega un paso y el archivo queda disperso.
- **Consecuencias:**
  - Servicio nuevo `orden_compra_service.py` y ventana nueva `orden_compra_dialog.py`.
  - Plantilla de mail `generar_plantilla_orden_compra`.
  - La notificación al socio indica el N° de orden.
  - Sin SMTP configurado, el envío queda registrado en modo simulación (como el resto de los mails) y la orden figura como enviada.
- **Relacionado con:** DEC-008, DEC-019, DEC-020.

---

### DEC-019 — Las órdenes de compra se registran en la base

- **Fecha:** 2026-11-23
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** Si la orden queda solo como archivo en una carpeta, no se puede recuperar ni reenviar desde el programa, y el historial del ejecutivo no tendría de dónde salir.
- **Decisión:**
  - Tabla nueva `ORDENES_COMPRA`: proveedor, ejecutivo, código, fecha, cantidad de pedidos, total, nombre del archivo y último envío por mail (fecha y destinatario).
  - Cada pedido consolidado guarda su orden en `PEDIDOS.id_orden_compra`.
  - Los artículos de la orden se obtienen de los pedidos vinculados, con el precio congelado (DEC-010).
  - Si el archivo no está (se borró la carpeta o la orden viene del seed), **se regenera** desde la base al abrirlo o enviarlo.
- **Alternativas consideradas:**
  - Solo el archivo en la carpeta: más simple, pero no se puede recuperar ni reenviar.
  - Guardar también una copia de los renglones en la orden: duplica datos que ya están congelados en los pedidos.
- **Consecuencias:**
  - `migrar_db` agrega la columna a bases existentes y la tabla se crea sola al iniciar.
  - El seed carga 4 órdenes para los pedidos consolidados y procesados.
  - Es la base para el historial del ejecutivo (punto 2, pendiente).
- **Relacionado con:** DEC-018, DEC-010.

---

### DEC-020 — Se quita "Órdenes por proveedor" y la planilla general pasa a ser un borrador del proveedor seleccionado

- **Fecha:** 2026-11-23
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** Con DEC-018, "Órdenes por proveedor" quedaba redundante. La "Planilla consolidada general" exportaba todos los proveedores, aunque la pantalla trabaja con uno.
- **Decisión:**
  - Se elimina el botón "Órdenes por proveedor (.xlsx)".
  - La planilla pasa a llamarse **"Planilla Borrador del Proveedor"**. Exporta el resumen y el detalle por socio **solo del proveedor seleccionado**, como archivo de trabajo interno antes de consolidar.
- **Alternativas consideradas:**
  - Dejar los dos botones como estaban: generan confusión con la orden oficial.
- **Consecuencias:** Se eliminó `exportar_ordenes_por_proveedor` del modelo.
- **Relacionado con:** DEC-018.

---

### DEC-021 — La prueba integral crea su propia base con el seed

- **Fecha:** 2026-11-23
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** `tests/test_circuit_suite.py` copiaba `database.db` y dependía de que tuviera los datos del seed. Después de ejecutar `limpiar_db.py`, la base real no tiene pedidos y la suite fallaría.
- **Decisión:** La suite ejecuta `seeds/seed_db.py` sobre una base en la carpeta temporal y ya no lee `database.db`. Confirmada por BenitezLuciano el 2026-11-23.
- **Alternativas consideradas:**
  - Seguir copiando la base real: la prueba depende del estado en que cada uno deje su base.
- **Consecuencias:** La suite da el mismo resultado sin importar el estado de `database.db`. Reemplaza a DEC-016.
  - En la misma fecha, `seeds/limpiar_db.py` pasó a borrar también `ORDENES_COMPRA` y los `.xlsx` de `ordenes_compra/`, y `ordenes_compra/` se agregó a `.gitignore`.
- **Relacionado con:** DEC-016.

---

### DEC-022 — Historial del ejecutivo como pantalla propia con tres pestañas

- **Fecha:** 2026-11-23
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** El ejecutivo no tenía dónde consultar lo ya realizado. Una orden emitida no se podía volver a abrir ni reenviar, y no había un registro visible de remitos ni de comprobantes recibidos.
- **Decisión:**
  - Cuarto ítem en el menú del ejecutivo, **"📜 Historial"**, como pantalla propia (igual que DEC-001).
  - Tiene tres pestañas:
    1. **Órdenes de Compra**: estado de entrega (pendiente o repartida) y de envío (enviada o sin enviar). Al seleccionar una orden se ven sus pedidos, y con **"Ver Orden"** se abre la misma ventana de la consolidación (abrir archivo, abrir carpeta, reenviar).
    2. **Remitos Emitidos**: con acceso al PDF. Si el archivo no está, se indica "PDF no disponible".
    3. **Comprobantes de Proveedores**: resultado del doble control (faltantes, excedentes, diferencias de precio) y detalle por artículo.
  - Filtros: proveedor en todas las pestañas, más estado (órdenes), socio (remitos) y resultado del control (comprobantes). El rango de fechas queda para más adelante.
  - **Todos los ejecutivos ven todo.** Se revisará junto con la observación #7 (notificaciones compartidas).
  - No se agrega una pestaña "Pedidos de socios": los pendientes están en el Módulo 2 y los demás aparecen dentro de cada orden.
- **Alternativas consideradas:**
  - Pestaña dentro de otro módulo: mezcla consulta con operación.
  - Filtrar por los proveedores asignados a cada ejecutivo: queda para cuando se resuelva la observación #7.
  - Regenerar ahora los PDF de remitos que faltan: se hará en el rediseño de remitos (punto 3), para no programarlo dos veces.
- **Consecuencias:**
  - Archivos nuevos: `historial_ejecutivo_model.py`, `historial_ejecutivo_view.py` y `historial_ejecutivo_controller.py`.
  - Las acciones sobre la orden pasaron a `orden_compra_acciones.py`, que comparten la consolidación y el historial.
- **Relacionado con:** DEC-001, DEC-018, DEC-019.

---

### DEC-023 — Rediseño del remito según el modelo estándar

- **Fecha:** 2026-11-23
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** El remito generado no seguía la estructura estándar de un remito argentino. BenitezLuciano aportó un modelo en PDF y la lista de datos que debe contener.
- **Decisión:**
  - **Diseño fiel al modelo**, dibujado directamente sobre el PDF:
    - Cabecera con el emisor y el recuadro central de la letra **"X"** con "DOCUMENTO NO VÁLIDO COMO FACTURA".
    - Datos del remito: N.º, fecha y lugar (Rosario).
    - Bloques Señor(es) y Domicilio, con I.V.A. y C.U.I.T./D.N.I.
    - Franja de **referencias** (pedido, orden de compra, proveedor y comprobante) en lugar de "Condición de venta".
    - Tabla Cantidad · Unidad · Código · Descripción, **sin precios**.
    - Pie de transporte y recepción.
  - **Letra X**: el sistema no está autorizado por AFIP para emitir remitos "R".
  - **Número formal `0001-00000001`** (punto de venta + correlativo, columna `REMITOS.numero_remito`). El código ofuscado `RC-REM-…` queda como **referencia interna**.
  - **Datos del emisor** en `src/config/empresa.py`. **Datos del socio** en `USERS` (`cuit_dni`, `condicion_iva`, `domicilio`). **Unidad** en `ARTICULOS.unidad`, que la importación de listas lee de una columna "Unidad" opcional.
  - **Observaciones automáticas**: pedido de origen y faltantes por prorrateo. Transportista, chofer y dominio quedan para completar a mano.
  - **ORIGINAL y DUPLICADO** en el mismo PDF. Si hay más de 17 renglones, se agregan hojas ("Hoja n de m").
  - Desde el historial, el PDF **se regenera** si falta (incluye los del formato anterior), a partir de los datos de la base.
  - **Datos fiscales simulados**: los CUIT figuran como `XX-XXXXXXXX-X`, el domicilio y la condición frente al IVA del emisor como "Completar", y los domicilios de los socios son ficticios. El pie del remito lo aclara mientras `DATOS_SIMULADOS = True`.
- **Alternativas consideradas:**
  - Letra R: requiere autorización de AFIP.
  - Reemplazar el código `RC-REM` por el correlativo: se pierde la referencia que ya usan el historial y las notificaciones.
  - Mantener solo el código ofuscado: no respeta la numeración estándar del remito.
  - Seguir generando el PDF desde HTML: no permite reproducir con precisión la grilla del modelo.
- **Consecuencias:**
  - `pdf_service.py` reescrito y modelo nuevo `remito_model.py`.
  - El reparto genera el PDF desde la base, igual que la regeneración.
  - Hoy no hay pantalla para editar los datos fiscales de los socios (pendiente).
- **Relacionado con:** DEC-009, DEC-022.

---

### DEC-024 — Historial del socio con detalle del pedido y Nota de Pedido en PDF

- **Fecha:** 2026-11-23
- **Estado:** Cerrada
- **Participantes:** BenitezLuciano, asistente (Claude Code)
- **Contexto:** El socio enviaba pedidos pero no tenía dónde ver lo que había enviado. El historial mostraba lo pedido en una columna "Productos Solicitados" con todos los artículos concatenados, que no se leía bien y no servía en la práctica.
- **Decisión:**
  - **Se quita la columna "Productos Solicitados".** La lista queda con N° de Pedido · Fecha · Proveedor · Estado · Productos (cantidad) · Unidades · Total · Remito, más filtros por proveedor y por estado.
  - **Detalle debajo de la lista** (igual que el historial del ejecutivo). Al seleccionar un pedido, en cualquier estado, se ve:
    - El estado en lenguaje simple: "Pendiente" (se puede modificar hasta que se consolide), "Enviado al proveedor" o "Entregado" (con el número de remito).
    - Los renglones: código, artículo, unidad, cantidad, precio unitario congelado y subtotal, con el total.
    - Si ya se entregó, una columna "Entregado" según el remito, resaltada cuando es menor que lo pedido.
  - **Nota de Pedido en PDF**, disponible en cualquier estado:
    - Mismo estilo que el remito, pero con precios, una sola copia y la leyenda "no válido como factura ni como remito".
    - Se puede **abrir** (se genera en una carpeta temporal) o **guardar como…** en la carpeta que elija el socio. No se guarda una copia en el proyecto: se genera siempre con los datos actuales de la base.
  - **"🚚 Ver remito"** cuando el pedido ya se entregó (regenera el PDF si falta, como en DEC-023).
  - **"✏️ Modificar pedido"** para los pedidos pendientes: abre Gestión de Pedidos en la hoja de ese proveedor. Solo se habilita si la lista sigue habilitada, y se vuelve a verificar al hacer clic.
  - Cada socio solo puede ver sus propios pedidos: el modelo valida que el pedido le pertenezca.
- **Alternativas consideradas:**
  - Ventana emergente con el detalle: agrega un paso más que el panel debajo de la lista.
  - Guardar la Nota de Pedido en una carpeta del proyecto, como los remitos: un pedido pendiente cambia y el archivo quedaría desactualizado.
  - Exportar a Excel: el PDF es más simple de leer, imprimir y reenviar para el socio.
  - Mostrar "pediste 10, se ajustó a 8" cuando el ejecutivo ajusta cantidades antes de consolidar: hoy no se guarda la cantidad original. Queda pendiente.
- **Consecuencias:**
  - `historial_view.py` se arma en código; `historial_pedidos.ui` queda sin uso.
  - `PedidoModel` suma `obtener_detalle_pedido` y la generación de la Nota de Pedido; `pdf_service.py` suma `generar_nota_pedido_pdf`.
  - `PedidoView.seleccionar_hoja` y `main.py` (`ir_a_modificar_pedido`) permiten ir del historial a la hoja del proveedor.
  - La prueba integral suma el paso 8b: 12 de 12 pruebas OK.
- **Relacionado con:** DEC-001, DEC-007, DEC-010, DEC-022, DEC-023.
