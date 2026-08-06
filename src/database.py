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

def inicializar_db():
    """
    Inicializa la base de datos ejecutando el script de creación.
    Crea el archivo database.db en la raíz si no existe.
    """
    if not os.path.exists(SQL_PATH):
        raise FileNotFoundError(f"No se encontró el script de esquema SQL en: {SQL_PATH}")

    conn = get_connection()
    try:
        with open(SQL_PATH, "r", encoding="utf-8") as f:
            script_sql = f.read()
        conn.executescript(script_sql)
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