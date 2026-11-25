import sqlite3
import os

# Ruta absoluta a la raíz del proyecto y rutas de archivos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "database.db")
SQL_PATH = os.path.join(BASE_DIR, "db", "rosario_compras.sql")

def get_connection():
    """
    Establece una conexión a la base de datos SQLite.
    Configura la fábrica de filas para poder acceder por nombre de columna
    y activa explícitamente el soporte de claves foráneas.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def migrar_db(conn):
    """
    Aplica migraciones incrementales automáticas y seguras
    para garantizar compatibilidad con bases de datos existentes.
    Las bases nuevas ya se crean con estas columnas desde rosario_compras.sql;
    esto solo completa columnas faltantes en bases creadas con versiones anteriores.
    """
    cursor = conn.cursor()

    def columnas(tabla):
        cursor.execute(f"PRAGMA table_info({tabla});")
        return [row[1] for row in cursor.fetchall()]

    def agregar_si_falta(tabla, columna, definicion):
        if columna not in columnas(tabla):
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion};")

    # PROVEEDORES: contacto y ciclo de la lista de precios
    agregar_si_falta("PROVEEDORES", "email", "TEXT")
    agregar_si_falta("PROVEEDORES", "telefono", "TEXT")
    agregar_si_falta("PROVEEDORES", "lista_habilitada", "INTEGER NOT NULL DEFAULT 0")
    agregar_si_falta("PROVEEDORES", "fecha_habilitacion", "TEXT")

    # PEDIDOS: código comercial y proveedor del pedido
    agregar_si_falta("PEDIDOS", "codigo_comercial", "TEXT")
    agregar_si_falta("PEDIDOS", "id_proveedor", "INTEGER REFERENCES PROVEEDORES(id_proveedor)")
    # (ORDENES_COMPRA se crea con CREATE TABLE IF NOT EXISTS desde rosario_compras.sql)
    agregar_si_falta("PEDIDOS", "id_orden_compra", "INTEGER REFERENCES ORDENES_COMPRA(id_orden_compra)")

    # DETALLE_PEDIDOS: precio congelado y cantidad original pedida por el socio
    agregar_si_falta("DETALLE_PEDIDOS", "precio_unitario", "REAL NOT NULL DEFAULT 0.0")
    agregar_si_falta("DETALLE_PEDIDOS", "cantidad_original", "INTEGER")
    cursor.execute(
        "UPDATE DETALLE_PEDIDOS SET cantidad_original = cantidad_pedida WHERE cantidad_original IS NULL"
    )

    # REMITOS: vínculo con pedido/proveedor y código único
    agregar_si_falta("REMITOS", "id_pedido", "INTEGER REFERENCES PEDIDOS(id_pedido)")
    agregar_si_falta("REMITOS", "id_proveedor", "INTEGER REFERENCES PROVEEDORES(id_proveedor)")
    agregar_si_falta("REMITOS", "codigo_comercial", "TEXT")

    agregar_si_falta("REMITOS", "numero_remito", "TEXT")
    # Completar el número formal de remitos emitidos antes de esta versión
    from src.config.empresa import PUNTO_VENTA_REMITOS
    cursor.execute(
        "UPDATE REMITOS SET numero_remito = printf('%04d-%08d', ?, id_remito) WHERE numero_remito IS NULL",
        (PUNTO_VENTA_REMITOS,)
    )

    # USERS: datos fiscales y de entrega del socio (remitos)
    agregar_si_falta("USERS", "cuit_dni", "TEXT")
    agregar_si_falta("USERS", "condicion_iva", "TEXT")
    agregar_si_falta("USERS", "domicilio", "TEXT")

    # ARTICULOS: unidad de venta/entrega
    agregar_si_falta("ARTICULOS", "unidad", "TEXT NOT NULL DEFAULT 'Unidad'")

    # COMPROBANTES_PROVEEDOR y PRECIOS_NEGOCIADOS
    agregar_si_falta("COMPROBANTES_PROVEEDOR", "codigo_comercial", "TEXT")
    agregar_si_falta("PRECIOS_NEGOCIADOS", "precio_base", "REAL DEFAULT 0.0")

def inicializar_db():
    """
    Inicializa la base de datos ejecutando el script de creación y
    aplicando migraciones necesarias.
    """
    if not os.path.exists(SQL_PATH):
        raise FileNotFoundError(f"No se encontró el script de esquema SQL en: {SQL_PATH}")

    conn = get_connection()
    try:
        with open(SQL_PATH, "r", encoding="utf-8") as f:
            script_sql = f.read()
        conn.executescript(script_sql)
        migrar_db(conn)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

class Database:
    """
    Clase utilitaria que implementa el protocolo de contexto para
    gestionar de forma segura transacciones y el ciclo de vida de la conexión.
    Uso:
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(...)
    """
    def __enter__(self):
        self.connection = get_connection()
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.connection.rollback()
        else:
            self.connection.commit()
        self.connection.close()