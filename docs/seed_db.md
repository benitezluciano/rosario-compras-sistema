# Script Poblador (`seed_db.py`)

## Propósito Principal
Es un script transitorio y de apoyo que sirve para rellenar (poblar) la base de datos `database.db` con datos ficticios controlados o "mocks". Es crítico durante la etapa de desarrollo local, permitiendo simular el comportamiento del sistema sin tener que realizar inserciones manuales exhaustivas a través de la interfaz.

## Dependencias e Interacciones
- **Llama a**: 
  - La librería estándar `sqlite3` de Python para manejar la conexión de base de datos directa.
- **Es llamado por**:
  - El desarrollador u operador técnico al ejecutar `python seed_db.py` por terminal para reiniciar el estado inicial del sistema en fases de validación.

## Lógica Interna Clave
- **Inserciones Estáticas**: Inyecta datos controlados como usuarios con el rol validado `'socio'` y `'ejecutivo'`.
- **Estructuración del Catálogo**: Introduce registros a `PROVEEDORES` y `ARTICULOS` con sus montos lógicos de stock en almacén, y conecta estos datos en la tabla intermedia de `PRECIOS_NEGOCIADOS`.
- Al usar construcciones como `INSERT OR IGNORE`, evita fallos o duplicidades en bases de datos que ya tienen algo de información pre-existente generada en ejecuciones previas.
