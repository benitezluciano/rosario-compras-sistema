# Estado actual

**Última actualización:** 2026-11-23
**Versión / hito actual:** Órdenes de compra, historial del ejecutivo y remito estándar (rama `feature/pedidos-por-proveedor`)

## Objetivo del momento
Completar el circuito operativo del ejecutivo (consolidar, enviar, repartir, consultar) y seguir con las modificaciones que surjan de las pruebas.

## En curso
- [ ] Nuevas modificaciones a definir con BenitezLuciano — sin Issue

## Pendiente (en orden de prioridad)
1. Ratificar con el grupo que una lista nueva actualiza los pedidos pendientes — DEC-011
2. Pantalla para editar los datos fiscales y el domicilio de los socios (hoy solo se cargan desde el seed) — DEC-023
3. Reemplazar los datos fiscales simulados por los reales en `src/config/empresa.py` y `DATOS_SIMULADOS = False` — DEC-023
4. Observación #7: notificaciones de ejecutivos compartidas; revisar junto con la visibilidad del historial por ejecutivo — DEC-022
5. Actualizar la documentación al flujo nuevo: `README.md`, `MANUAL_DE_USUARIO.md/.html`, `WALKTHROUGH.md/.html` — sin Issue
6. `tests/test_proveedores_email.py` escribe sobre la base real — DEC-021
7. Evaluar la hoja "Resumen" del portal del socio — DEC-003
8. Menores:
   - Historial: filtro por rango de fechas.
   - Remito: descripciones largas en más de una línea.
   - Dependencias sin uso en `requirements.txt`.
   - Sacar `database.db`, `remitos_pdf/` y `logs/` del control de versiones.
   - Documentos duplicados.

## Bloqueado
- Manejo del stock al asentar comprobantes (sumar o reemplazar; depósito o paso directo) — lo destraba una decisión del grupo — DEC-014

## Cerrado recientemente
- Orden de compra en Excel generada al consolidar, con envío por mail y registro en la base (DEC-018 a DEC-020) — 2026-11-23
- La prueba integral crea su propia base con el seed (DEC-021) — 2026-11-23
- Historial del ejecutivo: órdenes, remitos y comprobantes (DEC-022) — 2026-11-23
- Remito con formato estándar: letra X, número 0001-…, original y duplicado (DEC-023) — 2026-11-23

## Próximo paso concreto
Definir con BenitezLuciano la próxima tanda de modificaciones.

## Dudas / riesgos abiertos
- DEC-011 y DEC-014 dependen del grupo.
- Los datos fiscales del emisor y de los socios son simulados: no usar los remitos fuera de las pruebas.
- Correr `seeds/seed_db.py` **borra todos los datos** de `database.db`; `seeds/limpiar_db.py` borra solo los datos operativos.

## Enlaces útiles
- Decisiones: [DECISIONES.md](DECISIONES.md) · Bitácora: [BITACORA.md](BITACORA.md)
- Prueba integral: `python tests/test_circuit_suite.py`
- Datos de la empresa: [../src/config/empresa.py](../src/config/empresa.py)
- Esquema de base de datos: [../db/rosario_compras.sql](../db/rosario_compras.sql)
