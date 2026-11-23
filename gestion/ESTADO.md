# Estado actual

**Última actualización:** 2026-11-23
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
Los puntos 1, 2 y 5 se pueden hacer ya. Los puntos 3 y 4 necesitan antes una decisión del grupo.

1. **Guardar la cantidad original del pedido antes de que el ejecutivo la ajuste.** — DEC-024
   - Por qué: en el Módulo 2 el ejecutivo puede cambiar cantidades de pedidos pendientes y se pierde lo que pidió el socio. Con el dato, el historial y la Nota de Pedido podrían mostrar "pediste 10, se ajustó a 8".
   - Dónde: `DETALLE_PEDIDOS` (columna nueva, con `migrar_db` en `src/database.py` y el DDL en `db/rosario_compras.sql`), `ConsolidacionModel.guardar_modificaciones_ejecutivo`, `PedidoModel.obtener_detalle_pedido`, `historial_view.py` y `pdf_service.py` (Nota de Pedido).
2. **Pantalla para que el socio cargue sus datos fiscales y su domicilio.** — DEC-023
   - Por qué: CUIT/DNI, condición frente al IVA y domicilio salen en el remito y en la Nota de Pedido, y hoy solo se cargan desde el seed (`USERS.cuit_dni`, `condicion_iva`, `domicilio`).
   - Después, reemplazar los datos simulados del emisor en `src/config/empresa.py` y poner `DATOS_SIMULADOS = False`.
3. **Ratificar con el grupo que una lista nueva actualiza los precios de los pedidos pendientes.** — DEC-011 (decisión del grupo, no es para programar)
4. **Observación #7: notificaciones compartidas entre ejecutivos**, junto con qué ve cada ejecutivo en su historial. — DEC-022 (decisión del grupo)
5. **Actualizar la documentación al flujo nuevo:** `README.md`, `MANUAL_DE_USUARIO.md/.html` y `WALKTHROUGH.md/.html`. No reflejan nada de las sesiones 1 a 3. — sin Issue
6. **`tests/test_proveedores_email.py` escribe sobre la base real.** Que use una base temporal como la suite integral. — DEC-021
7. **Evaluar la hoja "Resumen"** del portal del socio. — DEC-003 (propuesta)
8. **Idea nueva (sin decidir):** que al hacer clic en una notificación (por ejemplo "tu remito fue emitido") se abra ese pedido en el historial del socio.
9. **Menores:**
   - Borrar `src/views/historial_pedidos.ui`: quedó sin uso desde DEC-024 (falta confirmar).
   - Filtro por rango de fechas en los dos historiales.
   - Remito y Nota de Pedido: descripciones largas en más de una línea (hoy se cortan con "…").
   - Dependencias sin uso en `requirements.txt`.
   - Sacar `database.db`, `remitos_pdf/` y `logs/` del control de versiones.
   - Documentos duplicados.

## Bloqueado
- Manejo del stock al asentar comprobantes (sumar o reemplazar; depósito o paso directo). Lo destraba una decisión del grupo. — DEC-014

## Cerrado recientemente
- Historial del socio: detalle del pedido en cualquier estado, Nota de Pedido en PDF (abrir o guardar), acceso al remito y a "Modificar pedido" (DEC-024) — 2026-11-23
- Orden de compra en Excel generada al consolidar, con envío por mail y registro en la base (DEC-018 a DEC-020) — 2026-11-23
- La prueba integral crea su propia base con el seed (DEC-021) — 2026-11-23
- Historial del ejecutivo: órdenes, remitos y comprobantes (DEC-022) — 2026-11-23
- Remito con formato estándar: letra X, número 0001-…, original y duplicado (DEC-023) — 2026-11-23

## Próximo paso concreto
Eros toma el punto 1 (cantidad original del pedido) o el 5 (documentación), según prefiera. Los puntos 3 y 4 se llevan a la próxima reunión del grupo.

## Dudas / riesgos abiertos
- DEC-011 y DEC-014 dependen del grupo.
- Los datos fiscales del emisor y de los socios son simulados: no usar los remitos ni las Notas de Pedido fuera de las pruebas.
- Todos los ejecutivos ven todo el historial (DEC-022) hasta que se resuelva la observación #7.

## Enlaces útiles
- Decisiones: [DECISIONES.md](DECISIONES.md) · Bitácora: [BITACORA.md](BITACORA.md)
- Prueba integral: `python tests/test_circuit_suite.py`
- Datos de la empresa: [../src/config/empresa.py](../src/config/empresa.py)
- Esquema de base de datos: [../db/rosario_compras.sql](../db/rosario_compras.sql)
