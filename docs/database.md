# Base de Datos (`src/database.py`)

## Propósito Principal
Este archivo gestiona la conexión a la base de datos SQLite (`database.db`). Actúa como un *Context Manager* (utilizando los métodos mágicos `__enter__` y `__exit__`), lo que permite que otras partes de la aplicación abran conexiones seguras usando el bloque `with Database() as conn:`.

## Dependencias e Interacciones
- **Llama a**: La librería estándar `sqlite3` de Python.
- **Es llamado por**: Todos los archivos dentro de `src/models/` y el archivo `main.py` (durante la inicialización).

## Métodos y Clases Clave
- **Clase `Database`**: 
  - `__init__`: Define la ruta física al archivo de base de datos.
  - `__enter__`: Abre la conexión y **habilita explícitamente las claves foráneas** ejecutando `PRAGMA foreign_keys = ON;` para que SQLite aplique las restricciones de relaciones de integridad.
  - `__exit__`: Asegura el cierre seguro de la conexión al terminar el bloque, liberando los recursos de memoria y el bloqueo del archivo.
- **Función `inicializar_db()`**: Ejecuta el script SQL fundacional `rosario_compras.sql` (ubicado en `db/`) para asegurar de que la estructura DDL completa esté construida antes de que el usuario opere el sistema.
