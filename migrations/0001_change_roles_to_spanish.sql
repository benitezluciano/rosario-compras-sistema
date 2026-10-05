-- Migración: Cambiar constraint de roles en la tabla USERS al español
-- De: CHECK(role IN ('procurement', 'partner'))
-- A:  CHECK(role IN ('ejecutivo', 'socio'))

-- Desactivar claves foráneas temporalmente para evitar problemas de integridad durante la migración
PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

-- 1. Renombrar la tabla original
ALTER TABLE USERS RENAME TO USERS_old;

-- 2. Crear la nueva tabla con el constraint actualizado
CREATE TABLE USERS (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    role          TEXT    NOT NULL CHECK(role IN ('ejecutivo', 'socio'))
);

-- 3. Copiar los datos traduciendo los roles existentes
INSERT INTO USERS (id, nombre, email, password_hash, role)
SELECT 
    id, 
    nombre, 
    email, 
    password_hash,
    CASE role
        WHEN 'procurement' THEN 'ejecutivo'
        WHEN 'partner' THEN 'socio'
        ELSE role
    END
FROM USERS_old;

-- 4. Eliminar la tabla antigua
DROP TABLE USERS_old;

COMMIT;

-- Reestablecer el chequeo de claves foráneas
PRAGMA foreign_keys = ON;
