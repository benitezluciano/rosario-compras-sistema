-- Migración: Agregar rol 'admin' al constraint de la tabla USERS
-- De: CHECK(role IN ('ejecutivo', 'socio'))
-- A:  CHECK(role IN ('ejecutivo', 'socio', 'admin'))

PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- 1. Crear tabla temporal con datos de USERS
CREATE TABLE USERS_new (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK(role IN ('ejecutivo', 'socio', 'admin'))
);

INSERT INTO USERS_new (id, nombre, email, password_hash, role)
SELECT id, nombre, email, password_hash, role
FROM USERS;

-- 2. Eliminar USERS y renombrar USERS_new a USERS
DROP TABLE USERS;
ALTER TABLE USERS_new RENAME TO USERS;

-- 3. Recrear PROVEEDORES para asegurar FK a USERS
CREATE TABLE PROVEEDORES_new (
    id_proveedor  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user       INTEGER NOT NULL,
    nombre        TEXT    NOT NULL,
    direccion     TEXT,
    FOREIGN KEY (id_user) REFERENCES USERS(id)
);
INSERT INTO PROVEEDORES_new SELECT * FROM PROVEEDORES;
DROP TABLE PROVEEDORES;
ALTER TABLE PROVEEDORES_new RENAME TO PROVEEDORES;

-- 4. Recrear PEDIDOS para asegurar FK a USERS
CREATE TABLE PEDIDOS_new (
    id_pedido  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user    INTEGER NOT NULL,
    fecha      TEXT    NOT NULL,
    estado     TEXT    NOT NULL DEFAULT 'Pendiente' CHECK(estado IN ('Pendiente', 'Consolidado', 'Procesado', 'Repartido')),
    FOREIGN KEY (id_user) REFERENCES USERS(id)
);
INSERT INTO PEDIDOS_new SELECT * FROM PEDIDOS;
DROP TABLE PEDIDOS;
ALTER TABLE PEDIDOS_new RENAME TO PEDIDOS;

-- 5. Recrear REMITOS para asegurar FK a USERS
CREATE TABLE REMITOS_new (
    id_remito        INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user          INTEGER NOT NULL,
    id_proceso       INTEGER NOT NULL,
    fecha_emision    TEXT    NOT NULL,
    detalle_entrega  TEXT,
    FOREIGN KEY (id_user)    REFERENCES USERS(id),
    FOREIGN KEY (id_proceso) REFERENCES PROCESOS_REPARTO(id_proceso)
);
INSERT INTO REMITOS_new SELECT * FROM REMITOS;
DROP TABLE REMITOS;
ALTER TABLE REMITOS_new RENAME TO REMITOS;

COMMIT;

PRAGMA foreign_keys = ON;
