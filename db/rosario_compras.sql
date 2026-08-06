-- ============================================================
--  BASE DE DATOS: Rosario Compras
--  Motor: SQLite
--  Descripción: Script de creación completo con todas las tablas
--  v2 - Entidad USERS centraliza autenticación y permisos
-- ============================================================

-- Esta línea activa el control de claves foráneas en SQLite.
-- SQLite NO lo activa por defecto, así que siempre hay que ponerlo al principio.
PRAGMA foreign_keys = ON;


-- ============================================================
-- TABLA 1: USERS
-- ============================================================
-- Entidad central de autenticación y permisos.
-- Reemplaza a EJECUTIVOS y SOCIOS del diseño original.
-- Los roles posibles son:
--   'ejecutivo' → ex ejecutivos de cuentas, gestionan proveedores
--   'socio'     → ex socios, realizan pedidos y reciben remitos

CREATE TABLE IF NOT EXISTS USERS (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    -- UNIQUE = no puede haber dos usuarios con el mismo email.

    password_hash TEXT    NOT NULL,
    -- Nunca se guarda la contraseña en texto plano.
    -- Se guarda el hash (resultado de aplicar bcrypt o sha256 a la contraseña).
    -- Ejemplo: '$2b$12$KIXxyz...' en lugar de 'micontraseña123'

    role          TEXT    NOT NULL CHECK(role IN ('ejecutivo', 'socio'))
    -- CHECK garantiza que solo se puedan insertar esos dos valores.
    -- Si intentás insertar role = 'admin' → error.
);


-- ============================================================
-- TABLA 2: PROVEEDORES
-- ============================================================
-- Cada proveedor es gestionado por un usuario con role = 'procurement'.
-- La FK id_user apunta a USERS.

CREATE TABLE IF NOT EXISTS PROVEEDORES (
    id_proveedor  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user       INTEGER NOT NULL,
    -- Reemplaza a id_ejecutivo. Apunta al usuario ejecutivo responsable.

    nombre        TEXT    NOT NULL,
    direccion     TEXT,

    FOREIGN KEY (id_user) REFERENCES USERS(id)
);


-- ============================================================
-- TABLA 3: ARTICULOS
-- ============================================================
-- Representa los artículos/productos generales en el sistema.

CREATE TABLE IF NOT EXISTS ARTICULOS (
    id_articulo           INTEGER PRIMARY KEY AUTOINCREMENT,
    id_articulo_proveedor TEXT,
    -- Código de referencia original del proveedor.

    detalle               TEXT    NOT NULL,
    rubro                 TEXT,
    cantidad_stock        INTEGER NOT NULL DEFAULT 0
);


-- ============================================================
-- TABLA 4: PRECIOS_NEGOCIADOS
-- ============================================================
-- Tabla intermedia/relacional que vincula el ID del Proveedor y el ID del Artículo.
-- Contiene el precio final acordado y/o el descuento pactado.

CREATE TABLE IF NOT EXISTS PRECIOS_NEGOCIADOS (
    id_proveedor  INTEGER NOT NULL,
    id_articulo   INTEGER NOT NULL,
    precio_final  REAL    NOT NULL DEFAULT 0.0, -- Precio final acordado
    descuento     REAL    NOT NULL DEFAULT 0.0, -- Descuento acordado (ej. porcentaje 0.10 o valor directo)

    PRIMARY KEY (id_proveedor, id_articulo),
    FOREIGN KEY (id_proveedor) REFERENCES PROVEEDORES(id_proveedor),
    FOREIGN KEY (id_articulo)  REFERENCES ARTICULOS(id_articulo)
);


-- ============================================================
-- TABLA 5: PEDIDOS
-- ============================================================
-- Un pedido es realizado por un usuario con role = 'socio'.

CREATE TABLE IF NOT EXISTS PEDIDOS (
    id_pedido  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user    INTEGER NOT NULL,
    -- Reemplaza a id_socio. Apunta al usuario socio que hace el pedido.

    fecha      TEXT    NOT NULL,
    estado     TEXT    NOT NULL DEFAULT 'Pendiente' CHECK(estado IN ('Pendiente', 'Consolidado', 'Procesado', 'Repartido')),

    FOREIGN KEY (id_user) REFERENCES USERS(id)
);


-- ============================================================
-- TABLA 6: DETALLE_PEDIDOS  (tabla intermedia Pedidos ↔ Artículos)
-- ============================================================
-- Resuelve la relación N:M entre PEDIDOS y ARTICULOS.
-- PK compuesta: la combinación de id_pedido + id_articulo debe ser única.

CREATE TABLE IF NOT EXISTS DETALLE_PEDIDOS (
    id_pedido       INTEGER NOT NULL,
    id_articulo     INTEGER NOT NULL,
    cantidad_pedida INTEGER NOT NULL DEFAULT 1,

    PRIMARY KEY (id_pedido, id_articulo),

    FOREIGN KEY (id_pedido)   REFERENCES PEDIDOS(id_pedido),
    FOREIGN KEY (id_articulo) REFERENCES ARTICULOS(id_articulo)
);


-- ============================================================
-- TABLA 7: PROCESOS_REPARTO
-- ============================================================
-- Agrupa los remitos generados en un mismo reparto.

CREATE TABLE IF NOT EXISTS PROCESOS_REPARTO (
    id_proceso           INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha_proceso        TEXT    NOT NULL,
    -- Formato datetime: 'YYYY-MM-DD HH:MM:SS'

    archivo_consolidado  TEXT,
    estado_reparto       TEXT    NOT NULL DEFAULT 'en_proceso'
    -- Valores posibles: 'en_proceso', 'completado', 'cancelado'
);


-- ============================================================
-- TABLA 8: REMITOS
-- ============================================================
-- Documento de entrega dirigido a un usuario con role = 'socio'.

CREATE TABLE IF NOT EXISTS REMITOS (
    id_remito        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user          INTEGER NOT NULL,
    -- Reemplaza a id_socio. Apunta al usuario socio que recibe el remito.

    id_proceso       INTEGER NOT NULL,
    fecha_emision    TEXT    NOT NULL,
    detalle_entrega  TEXT,

    FOREIGN KEY (id_user)    REFERENCES USERS(id),
    FOREIGN KEY (id_proceso) REFERENCES PROCESOS_REPARTO(id_proceso)
);


-- ============================================================
-- TABLA 9: DETALLE_REMITOS  (tabla intermedia Remitos ↔ Artículos)
-- ============================================================
-- Resuelve la relación N:M entre REMITOS y ARTICULOS.
-- Registra cuánto se entregó efectivamente.

CREATE TABLE IF NOT EXISTS DETALLE_REMITOS (
    id_remito           INTEGER NOT NULL,
    id_articulo         INTEGER NOT NULL,
    cantidad_entregada  INTEGER NOT NULL DEFAULT 0,

    PRIMARY KEY (id_remito, id_articulo),

    FOREIGN KEY (id_remito)   REFERENCES REMITOS(id_remito),
    FOREIGN KEY (id_articulo) REFERENCES ARTICULOS(id_articulo)
);


-- ============================================================
-- FIN DEL SCRIPT
-- ============================================================