import sqlite3
import os
from werkzeug.security import generate_password_hash

# Determinar la ruta absoluta a database.db en la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")
SQL_PATH = os.path.join(BASE_DIR, "db", "rosario_compras.sql")

def seed():
    print(f"Conectando a la base de datos en: {DB_PATH}")
    
    # Asegurar que el esquema base esté inicializado
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    try:
        # Si las tablas no existen, cargar el esquema
        with open(SQL_PATH, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
            
        # 1. Insertar Usuarios de prueba (1 Admin, 1 Ejecutivo, 5 Socios)
        usuarios = [
            (1, 'Administrador General', 'admin@rosariocompras.com', generate_password_hash('admin123'), 'admin'),
            (2, 'Ejecutivo de Cuentas', 'ejecutivo@rosariocompras.com', generate_password_hash('account123'), 'ejecutivo'),
            (3, 'Café Central (Socio 1)', 'socio1@rosariocompras.com', generate_password_hash('socio123'), 'socio'),
            (4, 'Panadería La Rosa (Socio 2)', 'socio2@rosariocompras.com', generate_password_hash('socio123'), 'socio'),
            (5, 'Restaurante Italia (Socio 3)', 'socio3@rosariocompras.com', generate_password_hash('socio123'), 'socio'),
            (6, 'Bar Pellegrini (Socio 4)', 'socio4@rosariocompras.com', generate_password_hash('socio123'), 'socio'),
            (7, 'Hotel Rosario (Socio 5)', 'socio5@rosariocompras.com', generate_password_hash('socio123'), 'socio'),
        ]
        
        cursor.executemany("""
            INSERT OR REPLACE INTO USERS (id, nombre, email, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        """, usuarios)
        print("OK: 7 Usuarios insertados con contraseñas seguras.")
        
        # 2. Insertar Proveedores de prueba (asignados al ejecutivo id=2)
        proveedores = [
            (1, 2, 'Distribuidora Central Rosario', 'Av. Pellegrini 1500, Rosario'),
            (2, 2, 'Lácteos del Litoral', 'Calle Santa Fe 2300, Rosario'),
            (3, 2, 'Insumos Gastronómicos del Sur', 'Bv. Oroño 850, Rosario'),
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO PROVEEDORES (id_proveedor, id_user, nombre, direccion)
            VALUES (?, ?, ?, ?)
        """, proveedores)
        print("OK: 3 Proveedores insertados.")
        
        # 3. Insertar Artículos en el catálogo
        articulos = [
            (1, 'ART-001', 'Café en Grano Tostado x 1kg', 'Cafetería', 150),
            (2, 'ART-002', 'Leche Entera Larga Vida x 1L', 'Lácteos', 300),
            (3, 'ART-003', 'Endulzante en Sobres x 800u', 'Cafetería', 100),
            (4, 'ART-004', 'Harina 0000 Especial x 25kg', 'Insumos', 80),
            (5, 'ART-005', 'Aceite de Girasol x 5L', 'Insumos', 60),
            (6, 'ART-006', 'Servilletas de Papel x 1000u', 'Descartables', 200),
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO ARTICULOS (id_articulo, id_articulo_proveedor, detalle, rubro, cantidad_stock)
            VALUES (?, ?, ?, ?, ?)
        """, articulos)
        print("OK: 6 Artículos insertados.")
        
        # 4. Insertar Precios Negociados
        precios = [
            (1, 1, 14500.0, 0.05),
            (2, 2, 1150.0, 0.0),
            (1, 3, 3200.0, 0.0),
            (3, 4, 18500.0, 0.10),
            (3, 5, 8200.0, 0.0),
            (3, 6, 2400.0, 0.0),
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO PRECIOS_NEGOCIADOS (id_proveedor, id_articulo, precio_final, descuento)
            VALUES (?, ?, ?, ?)
        """, precios)
        print("OK: Precios negociados insertados.")

        # 5. Insertar Pedidos iniciales de prueba (en estado 'Pendiente' para Socios 3, 4 y 5)
        pedidos = [
            (1, 3, '2026-08-20', 'Pendiente'),
            (2, 4, '2026-08-21', 'Pendiente'),
            (3, 5, '2026-08-21', 'Pendiente'),
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO PEDIDOS (id_pedido, id_user, fecha, estado)
            VALUES (?, ?, ?, ?)
        """, pedidos)
        
        detalles_pedidos = [
            (1, 1, 5),   # Socio 1 pide 5 cafe
            (1, 2, 20),  # Socio 1 pide 20 leche
            (2, 1, 3),   # Socio 2 pide 3 cafe
            (2, 4, 2),   # Socio 2 pide 2 harina
            (3, 2, 15),  # Socio 3 pide 15 leche
            (3, 6, 4),   # Socio 3 pide 4 servilletas
        ]
        cursor.executemany("""
            INSERT OR REPLACE INTO DETALLE_PEDIDOS (id_pedido, id_articulo, cantidad_pedida)
            VALUES (?, ?, ?)
        """, detalles_pedidos)
        print("OK: Pedidos iniciales de prueba insertados.")
        
        conn.commit()
        print("¡Base de datos poblada con éxito!")
        
    except Exception as e:
        conn.rollback()
        print(f"Error al poblar la base de datos: {e}")
        raise e
    finally:
        conn.close()

if __name__ == '__main__':
    seed()
