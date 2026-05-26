-- ============================================================
--  BASE DE DATOS: Rosario Compras
--  Motor: SQLite
--  Descripción: Script de creación completo con todas las tablas
-- ============================================================

-- Esta línea activa el control de claves foráneas en SQLite.
-- SQLite NO lo activa por defecto, así que siempre hay que ponerlo al principio.
PRAGMA foreign_keys = ON;


-- ============================================================
-- TABLA 1: EJECUTIVOS
-- ============================================================
-- Los ejecutivos son los empleados que gestionan proveedores.
-- Es la primera tabla porque nadie depende de ella (no tiene FK).

CREATE TABLE IF NOT EXISTS EJECUTIVOS (
    id_ejecutivo  INTEGER PRIMARY KEY AUTOINCREMENT,
    -- INTEGER PRIMARY KEY AUTOINCREMENT → SQLite asigna el número solo (1, 2, 3...).
    -- Nunca tenés que insertar este valor manualmente.

    nombre        TEXT    NOT NULL,
    -- TEXT = cualquier texto. NOT NULL = campo obligatorio.

    email         TEXT    NOT NULL UNIQUE
    -- UNIQUE = no puede haber dos ejecutivos con el mismo email.
);


-- ============================================================
-- TABLA 2: PROVEEDORES
-- ============================================================
-- Cada proveedor es gestionado por exactamente un ejecutivo.
-- La FK id_ejecutivo "apunta" a la tabla EJECUTIVOS.

CREATE TABLE IF NOT EXISTS PROVEEDORES (
    id_proveedor  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_ejecutivo  INTEGER NOT NULL,
    nombre        TEXT    NOT NULL,
    direccion     TEXT,
    -- direccion no tiene NOT NULL → puede quedar vacío (NULL es válido).

    FOREIGN KEY (id_ejecutivo) REFERENCES EJECUTIVOS(id_ejecutivo)
    -- Esto le dice a SQLite: "el valor de id_ejecutivo debe existir en EJECUTIVOS".
    -- Si intentás insertar un proveedor con un id_ejecutivo que no existe → error.
);


-- ============================================================
-- TABLA 3: LISTAS_PRECIOS
-- ============================================================
-- Cada lista pertenece a un proveedor. Un proveedor puede tener
-- varias listas a lo largo del tiempo.

CREATE TABLE IF NOT EXISTS LISTAS_PRECIOS (
    id_lista              INTEGER PRIMARY KEY AUTOINCREMENT,
    id_proveedor          INTEGER NOT NULL,
    fecha_carga           TEXT    NOT NULL,
    -- Las fechas en SQLite se guardan como TEXT en formato 'YYYY-MM-DD'.
    -- Ejemplo: '2024-03-15'

    nombre_archivo_source TEXT,
    -- Nombre del archivo Excel/CSV original del que vino la lista.

    FOREIGN KEY (id_proveedor) REFERENCES PROVEEDORES(id_proveedor)
);


-- ============================================================
-- TABLA 4: ARTICULOS
-- ============================================================
-- Cada artículo pertenece a una lista de precios.
-- Tiene precio y stock. El id_articulo_proveedor es el código
-- interno que usa el proveedor (puede ser texto como "ABC-123").

CREATE TABLE IF NOT EXISTS ARTICULOS (
    id_articulo           INTEGER PRIMARY KEY AUTOINCREMENT,
    id_lista              INTEGER NOT NULL,
    id_articulo_proveedor TEXT,
    -- Código del proveedor para este artículo. Puede ser alfanumérico.

    detalle               TEXT    NOT NULL,
    rubro                 TEXT,
    precio_final          REAL    NOT NULL DEFAULT 0.0,
    -- REAL = número con decimales (ideal para precios).
    -- DEFAULT 0.0 = si no se especifica un precio, se pone 0.

    cantidad_stock        INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (id_lista) REFERENCES LISTAS_PRECIOS(id_lista)
);


-- ============================================================
-- TABLA 5: SOCIOS
-- ============================================================
-- Los socios son quienes realizan pedidos y reciben remitos.
-- Esta tabla no depende de ninguna otra (no tiene FK).

CREATE TABLE IF NOT EXISTS SOCIOS (
    id_socio  INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT    NOT NULL,
    email     TEXT    NOT NULL UNIQUE
);


-- ============================================================
-- TABLA 6: PEDIDOS
-- ============================================================
-- Un pedido es realizado por un socio. Tiene fecha y estado.
-- Los estados posibles serían: 'pendiente', 'confirmado', 'cancelado'.

CREATE TABLE IF NOT EXISTS PEDIDOS (
    id_pedido  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_socio   INTEGER NOT NULL,
    fecha      TEXT    NOT NULL,
    estado     TEXT    NOT NULL DEFAULT 'pendiente',
    -- DEFAULT 'pendiente' → si no se especifica estado, queda en 'pendiente'.

    FOREIGN KEY (id_socio) REFERENCES SOCIOS(id_socio)
);


-- ============================================================
-- TABLA 7: DETALLE_PEDIDOS  (tabla intermedia Pedidos ↔ Artículos)
-- ============================================================
-- Esta tabla resuelve la relación N:M entre PEDIDOS y ARTICULOS.
-- Un pedido puede tener muchos artículos, y un artículo puede
-- estar en muchos pedidos.
--
-- La CLAVE PRIMARIA es COMPUESTA: (id_pedido + id_articulo).
-- Eso significa que la combinación de ambos debe ser única,
-- pero cada uno por separado puede repetirse.

CREATE TABLE IF NOT EXISTS DETALLE_PEDIDOS (
    id_pedido       INTEGER NOT NULL,
    id_articulo     INTEGER NOT NULL,
    cantidad_pedida INTEGER NOT NULL DEFAULT 1,

    PRIMARY KEY (id_pedido, id_articulo),
    -- PK compuesta: no puede haber dos líneas con el mismo pedido Y artículo.

    FOREIGN KEY (id_pedido)   REFERENCES PEDIDOS(id_pedido),
    FOREIGN KEY (id_articulo) REFERENCES ARTICULOS(id_articulo)
);


-- ============================================================
-- TABLA 8: PROCESOS_REPARTO
-- ============================================================
-- Un proceso de reparto agrupa varios remitos que se generan
-- juntos (ej: el reparto del martes de la semana 12).

CREATE TABLE IF NOT EXISTS PROCESOS_REPARTO (
    id_proceso           INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_proceso        TEXT    NOT NULL,
    -- Formato datetime: 'YYYY-MM-DD HH:MM:SS' → Ejemplo: '2024-03-15 09:30:00'

    archivo_consolidado  TEXT,
    -- Ruta o nombre del archivo que consolidó los pedidos para este reparto.

    estado_reparto       TEXT    NOT NULL DEFAULT 'en_proceso'
    -- Posibles valores: 'en_proceso', 'completado', 'cancelado'
);


-- ============================================================
-- TABLA 9: REMITOS
-- ============================================================
-- Un remito es el documento de entrega a un socio.
-- Pertenece a un proceso de reparto y va dirigido a un socio.

CREATE TABLE IF NOT EXISTS REMITOS (
    id_remito        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_socio         INTEGER NOT NULL,
    id_proceso       INTEGER NOT NULL,
    fecha_emision    TEXT    NOT NULL,
    detalle_entrega  TEXT,

    FOREIGN KEY (id_socio)   REFERENCES SOCIOS(id_socio),
    FOREIGN KEY (id_proceso) REFERENCES PROCESOS_REPARTO(id_proceso)
);


-- ============================================================
-- TABLA 10: DETALLE_REMITOS  (tabla intermedia Remitos ↔ Artículos)
-- ============================================================
-- Similar a DETALLE_PEDIDOS, resuelve la relación N:M entre
-- REMITOS y ARTICULOS. Registra cuánto se entregó efectivamente.
-- También conecta con DETALLE_PEDIDOS para trazabilidad completa.

CREATE TABLE IF NOT EXISTS DETALLE_REMITOS (
    id_remito           INTEGER NOT NULL,
    id_articulo         INTEGER NOT NULL,
    cantidad_entregada  INTEGER NOT NULL DEFAULT 0,

    PRIMARY KEY (id_remito, id_articulo),
    -- PK compuesta igual que DETALLE_PEDIDOS.

    FOREIGN KEY (id_remito)   REFERENCES REMITOS(id_remito),
    FOREIGN KEY (id_articulo) REFERENCES ARTICULOS(id_articulo)
);


-- ============================================================
-- FIN DEL SCRIPT
-- ============================================================
-- Para ejecutarlo en Python:
--   import sqlite3
--   conn = sqlite3.connect('rosario_compras.db')
--   with open('rosario_compras.sql', 'r') as f:
--       conn.executescript(f.read())
--   conn.close()
--
-- Para ejecutarlo desde la terminal:
--   sqlite3 rosario_compras.db < rosario_compras.sql
-- ============================================================