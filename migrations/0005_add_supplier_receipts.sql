-- Migración: Crear tablas COMPROBANTES_PROVEEDOR y DETALLE_COMPROBANTES_PROVEEDOR para control de compras y logística

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS COMPROBANTES_PROVEEDOR (
    id_comprobante    INTEGER PRIMARY KEY AUTOINCREMENT,
    id_proveedor      INTEGER NOT NULL,
    tipo_comprobante  TEXT NOT NULL DEFAULT 'Factura', -- 'Factura', 'Remito', 'Comprobante'
    nro_comprobante   TEXT NOT NULL,
    fecha_emision     TEXT NOT NULL,
    fecha_recepcion   TEXT NOT NULL,
    observaciones     TEXT,
    FOREIGN KEY (id_proveedor) REFERENCES PROVEEDORES(id_proveedor)
);

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
