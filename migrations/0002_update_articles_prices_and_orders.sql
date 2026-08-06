-- Migración: Reestructuración de artículos, precios negociados y pedidos
-- 1. Elimina la tabla LISTAS_PRECIOS.
-- 2. Crea la tabla intermedia PRECIOS_NEGOCIADOS.
-- 3. Remueve id_lista y precio_final de la tabla ARTICULOS (el precio final ahora es negociado).
-- 4. Modifica la tabla PEDIDOS para incluir la restricción CHECK en los estados en español.

PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- ==========================================
-- 1. MIGRACIÓN DE LA TABLA ARTICULOS Y PRECIOS_NEGOCIADOS
-- ==========================================

-- Renombrar tabla original de artículos
ALTER TABLE ARTICULOS RENAME TO ARTICULOS_old;

-- Crear la nueva tabla de artículos (sin id_lista ni precio_final)
CREATE TABLE ARTICULOS (
    id_articulo           INTEGER PRIMARY KEY AUTOINCREMENT,
    id_articulo_proveedor TEXT,
    detalle               TEXT    NOT NULL,
    rubro                 TEXT,
    cantidad_stock        INTEGER NOT NULL DEFAULT 0
);

-- Copiar los datos de los artículos
INSERT INTO ARTICULOS (id_articulo, id_articulo_proveedor, detalle, rubro, cantidad_stock)
SELECT id_articulo, id_articulo_proveedor, detalle, rubro, cantidad_stock
FROM ARTICULOS_old;

-- Crear la nueva tabla intermedia de precios negociados
CREATE TABLE PRECIOS_NEGOCIADOS (
    id_proveedor  INTEGER NOT NULL,
    id_articulo   INTEGER NOT NULL,
    precio_final  REAL    NOT NULL DEFAULT 0.0,
    descuento     REAL    NOT NULL DEFAULT 0.0,
    PRIMARY KEY (id_proveedor, id_articulo),
    FOREIGN KEY (id_proveedor) REFERENCES PROVEEDORES(id_proveedor),
    FOREIGN KEY (id_articulo)  REFERENCES ARTICULOS(id_articulo)
);

-- Migrar la información de precios desde la relación anterior (Artículos -> Listas -> Proveedores)
-- Esto preserva el precio final de los artículos ya asociados a un proveedor
INSERT INTO PRECIOS_NEGOCIADOS (id_proveedor, id_articulo, precio_final, descuento)
SELECT lp.id_proveedor, a.id_articulo, a.precio_final, 0.0
FROM ARTICULOS_old a
JOIN LISTAS_PRECIOS lp ON a.id_lista = lp.id_lista;

-- Eliminar tablas antiguas e intermedias obsoletas
DROP TABLE LISTAS_PRECIOS;
DROP TABLE ARTICULOS_old;


-- ==========================================
-- 2. MIGRACIÓN DE LA TABLA PEDIDOS (Actualización de estados)
-- ==========================================

-- Renombrar la tabla original de pedidos
ALTER TABLE PEDIDOS RENAME TO PEDIDOS_old;

-- Crear la nueva tabla de pedidos con la restricción CHECK en español
CREATE TABLE PEDIDOS (
    id_pedido  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user    INTEGER NOT NULL,
    fecha      TEXT    NOT NULL,
    estado     TEXT    NOT NULL DEFAULT 'Pendiente' CHECK(estado IN ('Pendiente', 'Consolidado', 'Procesado', 'Repartido')),
    FOREIGN KEY (id_user) REFERENCES USERS(id)
);

-- Copiar los datos traduciendo y homologando los estados anteriores
INSERT INTO PEDIDOS (id_pedido, id_user, fecha, estado)
SELECT 
    id_pedido, 
    id_user, 
    fecha,
    CASE LOWER(estado)
        WHEN 'confirmado' THEN 'Consolidado'
        WHEN 'procesado'  THEN 'Procesado'
        WHEN 'repartido'  THEN 'Repartido'
        ELSE 'Pendiente'
    END
FROM PEDIDOS_old;

-- Eliminar tabla antigua
DROP TABLE PEDIDOS_old;

COMMIT;

PRAGMA foreign_keys = ON;
