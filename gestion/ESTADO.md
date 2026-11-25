# Estado actual

**Última actualización:** 2026-11-25
**Versión / hito actual:** Historial del socio con detalle y Nota de Pedido (rama `feature/pedidos-por-proveedor`)

## Para quien retoma el trabajo
1. Leer este archivo y después [DECISIONES.md](DECISIONES.md) (por qué está hecho así). La historia de cada sesión está en [BITACORA.md](BITACORA.md).
2. Trabajar sobre la rama `feature/pedidos-por-proveedor`. La rama ya está en el remoto.
3. Correr la app con `python main.py`. Usuarios de prueba y contraseñas: los del seed (`seeds/seed_db.py`).
4. **Antes de entregar cualquier cambio:**
   - Correr `python tests/test_circuit_suite.py` (13 de 13 tienen que dar OK). Usa su propia base temporal, no toca `database.db`.
   - Correr `python -m compileall -q main.py src seeds tests`.
5. Forma de trabajo acordada (DEC-017): **proponer y esperar el OK antes de modificar**. Cada decisión nueva se registra en `DECISIONES.md` en el momento.
6. Aviso sobre la base: `seeds/seed_db.py` **borra todos los datos** de `database.db`; `seeds/limpiar_db.py` borra solo los datos operativos. `database.db` está en el control de versiones y aparece modificada cada vez que se usa la app: no incluirla en los commits.
7. Para ver PDF con texto hay que correr con pantalla normal (con `QT_QPA_PLATFORM=offscreen` no hay fuentes y los PDF salen sin texto).

## Objetivo del momento
Completar el circuito operativo del socio y del ejecutivo (pedir, consolidar, enviar, repartir, consultar) y dejar la documentación al día.

## En curso
- [ ] Nada abierto en este momento. Los pendientes de abajo están **asignados a Eros** mediante un Issue de traspaso.

## Pendiente (en orden de prioridad)
Los puntos "Para hacer ya" de las sesiones 1 a 3 quedaron implementados el 2026-11-24 y las decisiones del grupo se cerraron el 2026-11-25 (DEC-030 a DEC-032). No queda nada abierto para programar antes de la presentación.

1. **Reemplazo de datos fiscales simulados en producción:** para la entrega académica se mantienen en `True` (`src/config/empresa.py`) por definición del equipo (DEC-029).

## Mejoras futuras (sin fecha ni prioridad)
- Notificaciones compartidas entre ejecutivos y historial filtrado por los proveedores asignados a cada uno. Hoy hay un solo ejecutivo y todos ven todo. — DEC-032 (observación #7, DEC-022)
- Que al hacer clic en una notificación (por ejemplo "tu remito fue emitido") se abra ese pedido en el historial del socio.
- Registrar el excedente de recepción (lo recibido que sobra tras el reparto) para que el ejecutivo decida. A verificar qué hace hoy el sistema. — DEC-030
- Usuario propio para Logística (limitación L-04 del documento 05).

## Bloqueado
- Nada.

## Presentación del proyecto (en paralelo al desarrollo)
**Fecha de la presentación: 27/11/2026.** Formato y criterio en DEC-025 (propuesta) y DEC-026. Material en [../presentacion/](../presentacion/README.md): página AS-IS y TO-BE, diagramas en SVG y PNG, guion del video, texto de las diapositivas para Gamma (Sergio) y el script que genera los diagramas.
- **Falta:**
  1. Ensayar el recorrido del video (ahora 7 escenas, empieza en la carga de la lista de precios) con la base reseteada, confirmar el reparto esperado (2 / 4 / 3) y medir la duración; decidir quién graba. La portada la completa Sergio.
  2. Con el grupo: aclarar en el video que los datos son de prueba y decidir si se incluye el cuarto criterio de éxito del documento 06.
  3. No hay duraciones ni costos de implementación calculados: las diapositivas no los incluyen (DEC-027). Si el grupo respalda las cifras de plazo del documento 06, se agregan.
- **Diferencias entre el documento 05 (v1) y el sistema actual, para revisar con el grupo:**
  - RF-18 figura como no implementado, pero hoy el socio accede a su remito desde el historial (DEC-024).
  - L-01 parece resuelta por DEC-004 a DEC-009, y L-11 quedó vieja (hay una prueba integral de 13 pruebas). L-08 (cantidad original) quedó resuelta el 24/11 (`DETALLE_PEDIDOS.cantidad_original`) y L-02 (stock) dejó de ser una brecha: Rosario Compras no maneja stock (DEC-030). El riesgo de stock se sacó de la diapositiva 9.
  - Los datos de prueba tienen 8 socios gastronómicos; el caso real son 12 supermercadistas.
  - El documento 02 repite el encabezado del 04, y el diagrama de contexto del 03 tiene una caja suelta.
  - Los ejecutivos pidieron en la entrevista que los archivos se generen "según necesidad"; el sistema hoy guarda las órdenes de compra en la base (DEC-019). A verificar.
- `presentacion/` se versiona desde el 24/11. `documentacion/` (los PDF de la cátedra) no se versiona: está en `.gitignore` desde el 25/11.

## Cerrado recientemente
- Decisiones del grupo: sin stock, lo que llega se reparte (DEC-030, cierra DEC-014); lista nueva actualiza precios de pendientes, ratificada (DEC-031); observación #7 queda como está (DEC-032) — 2026-11-25
- Trazabilidad de cantidad original del pedido (`DETALLE_PEDIDOS.cantidad_original`), pantalla "Mis Datos Fiscales" del socio, hoja `"🧾 Resumen"` (`DEC-003`), filtros por fecha en historiales, descripciones multilínea en PDFs, aislamiento de `test_proveedores_email.py`, limpieza de archivos/.gitignore/`requirements.txt` y documentación al día (DEC-028, DEC-029) — 2026-11-24
- Historial del socio: detalle del pedido en cualquier estado, Nota de Pedido en PDF (abrir o guardar), acceso al remito y a "Modificar pedido" (DEC-024) — 2026-11-23
- Orden de compra en Excel generada al consolidar, con envío por mail y registro en la base (DEC-018 a DEC-020) — 2026-11-23
- La prueba integral crea su propia base con el seed (DEC-021) — 2026-11-23
- Historial del ejecutivo: órdenes, remitos y comprobantes (DEC-022) — 2026-11-23
- Remito con formato estándar: letra X, número 0001-…, original y duplicado (DEC-023) — 2026-11-23

## Próximo paso concreto
Del lado del código no queda nada para programar antes de la presentación. Lo que sigue es la presentación (abajo).

Presentación (27/11): Sergio arma las diapositivas en Gamma con `presentacion/contenido_diapositivas.md`; quien grabe el video ensaya con `presentacion/guion_video.md`; ensayo cronometrado del grupo el jueves 26.

## Dudas / riesgos abiertos
- Los datos fiscales del emisor y de los socios son simulados: no usar los remitos ni las Notas de Pedido fuera de las pruebas.
- Todos los ejecutivos ven todo el historial (DEC-022). Se deja así a propósito mientras haya un solo ejecutivo (DEC-032).

## Enlaces útiles
- Decisiones: [DECISIONES.md](DECISIONES.md) · Bitácora: [BITACORA.md](BITACORA.md)
- Presentación: [../presentacion/README.md](../presentacion/README.md) · Relevamiento: [../documentacion/](../documentacion)
- Prueba integral: `python tests/test_circuit_suite.py`
- Datos de la empresa: [../src/config/empresa.py](../src/config/empresa.py)
- Esquema de base de datos: [../db/rosario_compras.sql](../db/rosario_compras.sql)
