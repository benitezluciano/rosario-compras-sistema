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

    role          TEXT    NOT NULL CHECK(role IN ('ejecutivo', 'socio', 'admin'))
    -- CHECK garantiza que solo se puedan insertar esos valores ('ejecutivo', 'socio', 'admin').
);


-- ============================================================
-- TABLA 2: PROVEEDORES
-- ============================================================
-- Cada proveedor es gestionado por un usuario con role = 'ejecutivo' (o 'admin').
-- La FK id_user apunta a USERS.
--
-- Ciclo de la lista de precios:
--   lista_habilitada = 1 → los socios ven la lista y pueden cargar pedidos.
--   Se habilita al importar una lista nueva (o manualmente) y se cierra
--   automáticamente al consolidar los pedidos de ese proveedor.

CREATE TABLE IF NOT EXISTS PROVEEDORES (
    id_proveedor       INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user            INTEGER NOT NULL,
    -- Apunta al usuario ejecutivo responsable.

    nombre             TEXT    NOT NULL,
    email              TEXT,
    telefono           TEXT,
    direccion          TEXT,
    lista_habilitada   INTEGER NOT NULL DEFAULT 0 CHECK(lista_habilitada IN (0, 1)),
    fecha_habilitacion TEXT,
    -- Formato datetime: 'YYYY-MM-DD HH:MM:SS' (última habilitación)

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
    precio_base   REAL    NOT NULL DEFAULT 0.0, -- Precio de lista original del proveedor
    precio_final  REAL    NOT NULL DEFAULT 0.0, -- Precio final acordado (con descuento aplicado)
    descuento     REAL    NOT NULL DEFAULT 0.0, -- Descuento acordado (fracción, ej. 0.10 = 10%)

    PRIMARY KEY (id_proveedor, id_articulo),
    FOREIGN KEY (id_proveedor) REFERENCES PROVEEDORES(id_proveedor),
    FOREIGN KEY (id_articulo)  REFERENCES ARTICULOS(id_articulo)
);


-- ============================================================
-- TABLA 5: PEDIDOS
-- ============================================================
-- Un pedido es realizado por un usuario con role = 'socio' sobre la lista
-- de precios de UN proveedor. Si el socio carga varias listas a la vez,
-- el sistema genera un pedido independiente por cada proveedor.
-- Regla: un socio tiene como máximo un pedido 'Pendiente' por proveedor.

CREATE TABLE IF NOT EXISTS PEDIDOS (
    id_pedido        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user          INTEGER NOT NULL,
    -- Apunta al usuario socio que hace el pedido.

    id_proveedor     INTEGER NOT NULL,
    -- Proveedor (lista de precios) al que corresponde el pedido.

    codigo_comercial TEXT,
    -- Identificador ofuscado tipo 'RC-ORD-XXXXXX'.

    fecha            TEXT    NOT NULL,
    estado           TEXT    NOT NULL DEFAULT 'Pendiente' CHECK(estado IN ('Pendiente', 'Consolidado', 'Procesado', 'Repartido')),

    FOREIGN KEY (id_user)      REFERENCES USERS(id),
    FOREIGN KEY (id_proveedor) REFERENCES PROVEEDORES(id_proveedor)
);


-- ============================================================
-- TABLA 6: DETALLE_PEDIDOS  (tabla intermedia Pedidos ↔ Artículos)
-- ============================================================
-- Resuelve la relación N:M entre PEDIDOS y ARTICULOS.
-- PK compuesta: la combinación de id_pedido + id_articulo debe ser única.
-- precio_unitario congela el precio negociado: se actualiza mientras el
-- pedido está 'Pendiente' (si se importa una lista nueva) y queda fijo al consolidar.

CREATE TABLE IF NOT EXISTS DETALLE_PEDIDOS (
    id_pedido       INTEGER NOT NULL,
    id_articulo     INTEGER NOT NULL,
    cantidad_pedida INTEGER NOT NULL DEFAULT 1,
    precio_unitario REAL    NOT NULL DEFAULT 0.0,

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
-- Un remito corresponde a un único pedido (y por lo tanto a un único proveedor).

CREATE TABLE IF NOT EXISTS REMITOS (
    id_remito        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user          INTEGER NOT NULL,
    -- Apunta al usuario socio que recibe el remito.

    id_proceso       INTEGER NOT NULL,
    id_pedido        INTEGER,
    id_proveedor     INTEGER,
    codigo_comercial TEXT,
    -- Identificador ofuscado tipo 'RC-REM-XXXXXX' (derivado de id_remito, único).

    fecha_emision    TEXT    NOT NULL,
    detalle_entrega  TEXT,

    FOREIGN KEY (id_user)      REFERENCES USERS(id),
    FOREIGN KEY (id_proceso)   REFERENCES PROCESOS_REPARTO(id_proceso),
    FOREIGN KEY (id_pedido)    REFERENCES PEDIDOS(id_pedido),
    FOREIGN KEY (id_proveedor) REFERENCES PROVEEDORES(id_proveedor)
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
-- TABLA 10: NOTIFICACIONES
-- ============================================================
-- Avisos automáticos de pedidos cargados, consolidados y remitos.

CREATE TABLE IF NOT EXISTS NOTIFICACIONES (
    id_notificacion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user         INTEGER, -- NULL para notificaciones a ejecutivos/admin, o ID de socio específico
    mensaje         TEXT NOT NULL,
    tipo            TEXT NOT NULL DEFAULT 'info', -- 'nuevo_pedido', 'pedido_consolidado', 'reparto'
    fecha           TEXT NOT NULL,
    leida           INTEGER NOT NULL DEFAULT 0,

    FOREIGN KEY (id_user) REFERENCES USERS(id)
);


-- ============================================================
-- TABLA 11: COMPROBANTES_PROVEEDOR
-- ============================================================
-- Registro formal de Facturas / Remitos entregados por los proveedores.

CREATE TABLE IF NOT EXISTS COMPROBANTES_PROVEEDOR (
    id_comprobante    INTEGER PRIMARY KEY AUTOINCREMENT,
    id_proveedor      INTEGER NOT NULL,
    tipo_comprobante  TEXT NOT NULL DEFAULT 'Factura', -- 'Factura', 'Remito', 'Comprobante'
    nro_comprobante   TEXT NOT NULL,
    codigo_comercial  TEXT,
    fecha_emision     TEXT NOT NULL,
    fecha_recepcion   TEXT NOT NULL,
    observaciones     TEXT,

    FOREIGN KEY (id_proveedor) REFERENCES PROVEEDORES(id_proveedor)
);


-- ============================================================
-- TABLA 12: DETALLE_COMPROBANTES_PROVEEDOR
-- ============================================================
-- Control de Compras (Precios) y Control de Logística (Cantidades).

CREATE TABLE IF NOT EXISTS DETALLE_COMPROBANTES_PROVEEDOR (
    id_comprobante      INTEGER NOT NULL,
    id_articulo         INTEGER NOT NULL,
    cantidad_pedida     INTEGER NOT NULL,
    cantidad_recibida   INTEGER NOT NULL,
    precio_pactado      REAL NOT NULL,
    precio_facturado    REAL NOT NULL,

    PRIMARY KEY (id_comprobante, id_articulo),
    FOREIGN KEY (id_comprobante) REFERENCES COMPROBANTES_PROVEEDOR(id_comprobante),
    FOREIGN KEY (id_articulo)    REFERENCES ARTICULOS(id_articulo)
);


-- ============================================================
-- FIN DEL SCRIPT
-- ============================================================