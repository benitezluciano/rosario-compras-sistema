import sqlite3
import os

# Ruta absoluta a la carpeta db/, sin importar desde dónde se ejecute el script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "db", "rosario_compras.db")
SQL_PATH = os.path.join(BASE_DIR, "db", "rosario_compras.sql")

class Database:
    def __init__(self):
        # Crea el archivo .db si no existe, o conecta al existente
        self.connection = sqlite3.connect(DB_PATH)
        
        # Devuelve las filas como diccionarios en lugar de tuplas
        # Así podés acceder a los datos por nombre: fila["nombre"] en vez de fila[0]
        self.connection.row_factory = sqlite3.Row
        
        # Activa el control de claves foráneas (SQLite lo tiene apagado por defecto)
        self.connection.execute("PRAGMA foreign_keys = ON")
        
        # Inicializa las tablas si no existen todavía
        self._inicializar()

    def _inicializar(self):
        # Lee el archivo .sql y ejecuta todo el script de creación de tablas
        with open(SQL_PATH, "r", encoding="utf-8") as f:
            self.connection.executescript(f.read())

    def get_cursor(self):
        # Devuelve un cursor para ejecutar consultas
        return self.connection.cursor()

    def commit(self):
        # Confirma los cambios pendientes (INSERT, UPDATE, DELETE)
        self.connection.commit()

    def close(self):
        # Cierra la conexión correctamente
        self.connection.close()