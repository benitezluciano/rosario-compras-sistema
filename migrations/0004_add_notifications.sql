-- Migración: Crear tabla de NOTIFICACIONES para avisos de pedidos y consolidaciones

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS NOTIFICACIONES (
    id_notificacion INTEGER PRIMARY KEY AUTOINCREMENT,
    id_user         INTEGER, -- NULL para ejecutivos/admin, o ID de socio específico
    mensaje         TEXT NOT NULL,
    tipo            TEXT NOT NULL DEFAULT 'info', -- 'nuevo_pedido', 'pedido_consolidado', 'reparto'
    fecha           TEXT NOT NULL,
    leida           INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (id_user) REFERENCES USERS(id)
);
