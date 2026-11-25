# Estado actual

**Última actualización:** 2026-11-24
**Versión / hito actual:** Historial del socio con detalle y Nota de Pedido (rama `feature/pedidos-por-proveedor`)

## Para quien retoma el trabajo
1. Leer este archivo y después [DECISIONES.md](DECISIONES.md) (por qué está hecho así). La historia de cada sesión está en [BITACORA.md](BITACORA.md).
2. Trabajar sobre la rama `feature/pedidos-por-proveedor`. La rama ya está en el remoto.
3. Correr la app con `python main.py`. Usuarios de prueba y contraseñas: los del seed (`seeds/seed_db.py`).
4. **Antes de entregar cualquier cambio:**
   - Correr `python tests/test_circuit_suite.py` (12 de 12 tienen que dar OK). Usa su propia base temporal, no toca `database.db`.
   - Correr `python -m compileall -q main.py src seeds tests`.
5. Forma de trabajo acordada (DEC-017): **proponer y esperar el OK antes de modificar**. Cada decisión nueva se registra en `DECISIONES.md` en el momento.
6. Aviso sobre la base: `seeds/seed_db.py` **borra todos los datos** de `database.db`; `seeds/limpiar_db.py` borra solo los datos operativos. `database.db` está en el control de versiones y aparece modificada cada vez que se usa la app: no incluirla en los commits.
7. Para ver PDF con texto hay que correr con pantalla normal (con `QT_QPA_PLATFORM=offscreen` no hay fuentes y los PDF salen sin texto).

## Objetivo del momento
Completar el circuito operativo del socio y del ejecutivo (pedir, consolidar, enviar, repartir, consultar) y dejar la documentación al día.

## En curso
- [ ] Nada abierto en este momento. Los pendientes de abajo están **asignados a Eros** mediante un Issue de traspaso.

## Pendiente (en orden de prioridad)
Los puntos "Para hacer ya" de las sesiones 1 a 3 quedaron implementados el 2026-11-24. Quedan pendientes únicamente los puntos que requieren definición del grupo:

1. **Ratificar con el grupo que una lista nueva actualiza los precios de los pedidos pendientes.** — DEC-011 (decisión del grupo, no es para programar)
2. **Observación #7: notificaciones compartidas entre ejecutivos**, junto con qué ve cada ejecutivo en su historial. — DEC-022 (decisión del grupo)
3. **Idea nueva (sin decidir):** que al hacer clic en una notificación (por ejemplo "tu remito fue emitido") se abra ese pedido en el historial del socio.
4. **Reemplazo de datos fiscales simulados en producción:** para la entrega académica se mantienen en `True` (`src/config/empresa.py`) por definición del equipo (DEC-029).

## Bloqueado
- Manejo del stock al asentar comprobantes (sumar o reemplazar; depósito o paso directo). Lo destraba una decisión del grupo. — DEC-014

## Presentación del proyecto (en paralelo al desarrollo)
**Fecha de la presentación: 27/11/2026.** Formato y criterio en DEC-025 (propuesta) y DEC-026. Material en [../presentacion/](../presentacion/README.md): página AS-IS y TO-BE, diagramas en SVG y PNG, guion del video, texto de las diapositivas para Gamma (Sergio) y el script que genera los diagramas.
- **Falta:**
  1. Ensayar el recorrido del video con la base reseteada y confirmar el reparto esperado (2 / 4 / 3); decidir quién graba. La portada la completa Sergio.
  2. Con el grupo: aclarar en el video que los datos son de prueba y decidir si se incluye el cuarto criterio de éxito del documento 06.
  3. No hay duraciones ni costos de implementación calculados: las diapositivas no los incluyen (DEC-027). Si el grupo respalda las cifras de plazo del documento 06, se agregan.
- **Diferencias entre el documento 05 (v1) y el sistema actual, para revisar con el grupo:**
  - RF-18 figura como no implementado, pero hoy el socio accede a su remito desde el historial (DEC-024).
  - L-01 parece resuelta por DEC-004 a DEC-009, y L-11 quedó vieja (hay una prueba integral de 12 pasos). L-02 (stock) y L-08 (cantidad original) siguen abiertas.
  - Los datos de prueba tienen 8 socios gastronómicos; el caso real son 12 supermercadistas.
  - El documento 02 repite el encabezado del 04, y el diagrama de contexto del 03 tiene una caja suelta.
  - Los ejecutivos pidieron en la entrevista que los archivos se generen "según necesidad"; el sistema hoy guarda las órdenes de compra en la base (DEC-019). A verificar.
- `presentacion/` se versiona desde el 24/11. `documentacion/` (los PDF de la cátedra) todavía no: decisión pendiente del grupo.

## Cerrado recientemente
- Trazabilidad de cantidad original del pedido (`DETALLE_PEDIDOS.cantidad_original`), pantalla "Mis Datos Fiscales" del socio, hoja `"🧾 Resumen"` (`DEC-003`), filtros por fecha en historiales, descripciones multilínea en PDFs, aislamiento de `test_proveedores_email.py`, limpieza de archivos/.gitignore/`requirements.txt` y documentación al día (DEC-028, DEC-029) — 2026-11-24
- Historial del socio: detalle del pedido en cualquier estado, Nota de Pedido en PDF (abrir o guardar), acceso al remito y a "Modificar pedido" (DEC-024) — 2026-11-23
- Orden de compra en Excel generada al consolidar, con envío por mail y registro en la base (DEC-018 a DEC-020) — 2026-11-23
- La prueba integral crea su propia base con el seed (DEC-021) — 2026-11-23
- Historial del ejecutivo: órdenes, remitos y comprobantes (DEC-022) — 2026-11-23
- Remito con formato estándar: letra X, número 0001-…, original y duplicado (DEC-023) — 2026-11-23

## Próximo paso concreto
Eros toma el punto 1 (cantidad original del pedido) o el 5 (documentación), según prefiera. Los puntos 3 y 4 se llevan a la próxima reunión del grupo.

Presentación (27/11): Sergio arma las diapositivas en Gamma con `presentacion/contenido_diapositivas.md`; quien grabe el video ensaya con `presentacion/guion_video.md`; ensayo cronometrado del grupo el jueves 26.

## Dudas / riesgos abiertos
- DEC-011 y DEC-014 dependen del grupo.
- Los datos fiscales del emisor y de los socios son simulados: no usar los remitos ni las Notas de Pedido fuera de las pruebas.
- Todos los ejecutivos ven todo el historial (DEC-022) hasta que se resuelva la observación #7.

## Enlaces útiles
- Decisiones: [DECISIONES.md](DECISIONES.md) · Bitácora: [BITACORA.md](BITACORA.md)
- Presentación: [../presentacion/README.md](../presentacion/README.md) · Relevamiento: [../documentacion/](../documentacion)
- Prueba integral: `python tests/test_circuit_suite.py`
- Datos de la empresa: [../src/config/empresa.py](../src/config/empresa.py)
- Esquema de base de datos: [../db/rosario_compras.sql](../db/rosario_compras.sql)
