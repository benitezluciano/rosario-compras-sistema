# Estado actual

**Última actualización:** 2026-11-21
**Versión / hito actual:** Circuito de pedidos por proveedor (rama `feature/limpieza-operativa`, sin commitear)

## Objetivo del momento
Estabilizar el circuito de compras con pedidos por proveedor y cerrar las observaciones técnicas pendientes.

## En curso
- [ ] Prueba manual de la app con `python main.py`, como socio (`socio1`) y como ejecutivo (BenitezLuciano) — sin Issue

## Pendiente (en orden de prioridad)
1. Commitear los cambios de la rama `feature/limpieza-operativa` después de la prueba manual — sin Issue
2. Ratificar con el grupo que una lista nueva actualiza los pedidos pendientes — DEC-011
3. Actualizar la documentación al flujo nuevo: `README.md`, `MANUAL_DE_USUARIO.md/.html`, `WALKTHROUGH.md/.html` y documentos del circuito — sin Issue
4. Observación #7: las notificaciones de ejecutivos son compartidas (si uno las marca como leídas, quedan leídas para todos) — sin Issue
5. `tests/test_proveedores_email.py` escribe sobre la base real — DEC-016
6. Evaluar la hoja "Resumen" del portal del socio — DEC-003
7. Menores: dependencias sin uso en `requirements.txt`, agregar `database.db`, `remitos_pdf/` y `logs/` a `.gitignore`, documentos duplicados (`walkthrough*.md`), migraciones SQL históricas

## Bloqueado
- Manejo del stock al asentar comprobantes (sumar o reemplazar; depósito o paso directo) — lo destraba una decisión del grupo — DEC-014

## Cerrado recientemente
- Historial como pantalla propia (DEC-001) y listas como hojas estilo Excel (DEC-002) — 2026-11-21
- Pedidos por proveedor: resueltas las observaciones #1, #2, #3, #5 y #6 (DEC-004 a DEC-013) — 2026-11-21
- Reset de la base con el seed (DEC-015) y pruebas sobre copia temporal (DEC-016) — 2026-11-21

## Próximo paso concreto
Correr `python main.py` y recorrer el circuito completo: socio, Módulo 1, Módulo 2 y Módulo 3. Si funciona, hacer commit.

## Dudas / riesgos abiertos
- DEC-011 y DEC-014 dependen del grupo; si cambian, hay que ajustar `catalogo_model.py` o `reparto_model.py`.
- Correr `seeds/seed_db.py` **borra todos los datos** de `database.db`.
- `database.db` y `remitos_pdf/` están versionados en git, así que los cambios de datos aparecen en cada commit.

## Enlaces útiles
- Decisiones: [DECISIONES.md](DECISIONES.md) · Bitácora: [BITACORA.md](BITACORA.md)
- Prueba integral: `python tests/test_circuit_suite.py`
- Esquema de base de datos: [../db/rosario_compras.sql](../db/rosario_compras.sql)
