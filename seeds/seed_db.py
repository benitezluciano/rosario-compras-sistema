import sqlite3
import os

# Determinar la ruta absoluta a database.db
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def seed():
    print(f"Conectando a la base de datos en: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Habilitar claves foráneas
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    try:
        # 1. Insertar usuario de prueba con rol 'socio'
        # Campos: id, nombre, email, password_hash, role
        cursor.execute("""
            INSERT OR REPLACE INTO USERS (id, nombre, email, password_hash, role)
            VALUES (1, 'Socio de Prueba', 'socio@prueba.com', 'pbkdf2:sha256:dummyhash', 'socio')
        """)
        print("OK: Usuario insertado.")
        
        # 2. Insertar proveedor de prueba
        # Campos: id_proveedor, id_user, nombre, direccion
        cursor.execute("""
            INSERT OR REPLACE INTO PROVEEDORES (id_proveedor, id_user, nombre, direccion)
            VALUES (1, 1, 'Distribuidora Central', 'Av. Pellegrini 1500, Rosario')
        """)
        print("OK: Proveedor insertado.")
        
        # 3. Insertar tres artículos en el catálogo
        # Campos: id_articulo, id_articulo_proveedor, detalle, rubro, cantidad_stock
        articulos = [
            (1, 'ART-001', 'Cafe en Grano para Espresso', 'Cafeteria', 100),
            (2, 'ART-002', 'Leche Entera Larga Vida', 'Cafeteria', 100),
            (3, 'ART-003', 'Endulzante en Sobres', 'Cafeteria', 100)
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO ARTICULOS (id_articulo, id_articulo_proveedor, detalle, rubro, cantidad_stock)
            VALUES (?, ?, ?, ?, ?)
        """, articulos)
        print("OK: Articulos insertados.")
        
        # 4. Insertar los precios negociados de los artículos con el proveedor 1
        # Campos: id_proveedor, id_articulo, precio_final, descuento
        precios = [
            (1, 1, 15000.0, 0.0),
            (1, 2, 1200.0, 0.0),
            (1, 3, 3500.0, 0.0)
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO PRECIOS_NEGOCIADOS (id_proveedor, id_articulo, precio_final, descuento)
            VALUES (?, ?, ?, ?)
        """, precios)
        print("OK: Precios negociados insertados.")
        
        conn.commit()
        print("Base de datos poblada con exito!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error al poblar la base de datos: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    seed()
