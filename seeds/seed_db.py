import sqlite3
import os
import sys
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from src.database import migrar_db

DB_PATH = os.path.join(BASE_DIR, "database.db")
SQL_PATH = os.path.join(BASE_DIR, "db", "rosario_compras.sql")

def seed():
    print(f"Conectando a la base de datos en: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    try:
        # 1. Asegurar esquema limpio y estructurado
        with open(SQL_PATH, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
        migrar_db(conn)
            
        # Limpiar datos previos si existieran para evitar duplicados en reprocesamiento
        cursor.execute("DELETE FROM DETALLE_COMPROBANTES_PROVEEDOR;")
        cursor.execute("DELETE FROM COMPROBANTES_PROVEEDOR;")
        cursor.execute("DELETE FROM DETALLE_REMITOS;")
        cursor.execute("DELETE FROM REMITOS;")
        cursor.execute("DELETE FROM PROCESOS_REPARTO;")
        cursor.execute("DELETE FROM NOTIFICACIONES;")
        cursor.execute("DELETE FROM DETALLE_PEDIDOS;")
        cursor.execute("DELETE FROM PEDIDOS;")
        cursor.execute("DELETE FROM PRECIOS_NEGOCIADOS;")
        cursor.execute("DELETE FROM ARTICULOS;")
        cursor.execute("DELETE FROM PROVEEDORES;")
        cursor.execute("DELETE FROM USERS;")
            
        # 2. Insertar Usuarios (1 Admin, 2 Ejecutivos, 8 Socios del rubro gastronómico/hotelero)
        pwd_admin = generate_password_hash('admin123')
        pwd_exec = generate_password_hash('account123')
        pwd_socio = generate_password_hash('socio123')
        
        usuarios = [
            (1, 'Administrador General', 'admin@rosariocompras.com', pwd_admin, 'admin'),
            (2, 'Luciano Benítez (Ejecutivo Principal)', 'ejecutivo@rosariocompras.com', pwd_exec, 'ejecutivo'),
            (3, 'Martina Valenzuela (Ejecutiva Zona Norte)', 'ejecutivo2@rosariocompras.com', pwd_exec, 'ejecutivo'),
            (4, 'Café Central (Pichincha)', 'socio1@rosariocompras.com', pwd_socio, 'socio'),
            (5, 'Panadería & Confitería La Rosa (Centro)', 'socio2@rosariocompras.com', pwd_socio, 'socio'),
            (6, 'Restaurante Italia Tradizionale (Pellegrini)', 'socio3@rosariocompras.com', pwd_socio, 'socio'),
            (7, 'Bar & Bodegón Pellegrini (Echesortu)', 'socio4@rosariocompras.com', pwd_socio, 'socio'),
            (8, 'Gran Hotel Rosario (Costanera)', 'socio5@rosariocompras.com', pwd_socio, 'socio'),
            (9, 'Pizzería La Popular (Fisherton)', 'socio6@rosariocompras.com', pwd_socio, 'socio'),
            (10, 'Cervecería del Monumento (Monumento)', 'socio7@rosariocompras.com', pwd_socio, 'socio'),
            (11, 'Cafetería & Brunch El Parque (Parque Urquiza)', 'socio8@rosariocompras.com', pwd_socio, 'socio'),
        ]
        
        cursor.executemany("""
            INSERT INTO USERS (id, nombre, email, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        """, usuarios)
        print(f"OK: {len(usuarios)} Usuarios insertados con contraseñas seguras.")
        
        # 3. Insertar Proveedores representativos de Rosario y la región
        proveedores = [
            (1, 2, 'Distribuidora Central Rosario', 'ventas@distribuidoracentral.com', '(0341) 482-9000', 'Av. Pellegrini 1500, Rosario'),
            (2, 2, 'Lácteos del Litoral', 'pedidos@lacteosdellitoral.com', '(0341) 440-1122', 'Calle Santa Fe 2300, Rosario'),
            (3, 2, 'Insumos Gastronómicos del Sur', 'contacto@insumosdelsur.com', '(0341) 425-7788', 'Bv. Oroño 850, Rosario'),
            (4, 2, 'Frigorífico & Carnes del Paraná', 'ventas@carnesdelparana.com.ar', '(0341) 456-3344', 'Av. Circunvalación 4200, Rosario'),
            (5, 3, 'Bebidas & Bodegas Rosario', 'pedidos@bodegasrosario.com', '(0341) 438-5566', 'San Lorenzo 1120, Rosario'),
            (6, 3, 'Distribuidora Limpieza & Higiene Pro', 'info@limpiezapro.com.ar', '(0341) 471-8899', 'Salta 2840, Rosario'),
        ]
        cursor.executemany("""
            INSERT INTO PROVEEDORES (id_proveedor, id_user, nombre, email, telefono, direccion)
            VALUES (?, ?, ?, ?, ?, ?)
        """, proveedores)
        print(f"OK: {len(proveedores)} Proveedores insertados con email y teléfono.")
        
        # 4. Insertar Artículos del catálogo clasificados por rubro
        articulos = [
            # Distribuidora Central Rosario (id=1)
            (1, 'CAF-001', 'Café en Grano Tostado Especial x 1kg', 'Cafetería', 140),
            (2, 'CAF-002', 'Endulzante en Sobres x 800u', 'Cafetería', 95),
            (3, 'CAF-003', 'Té Variedades en Saquitos x 100u', 'Cafetería', 70),
            (4, 'ALM-001', 'Aceite de Girasol x 5L', 'Almacén', 55),
            (5, 'ALM-002', 'Azúcar Blanco Superior x 10kg', 'Almacén', 80),
            
            # Lácteos del Litoral (id=2)
            (6, 'LAC-001', 'Leche Entera Larga Vida x 1L', 'Lácteos', 380),
            (7, 'LAC-002', 'Crema de Leche Pastelera x 1L', 'Lácteos', 95),
            (8, 'LAC-003', 'Queso Mozzarella en Barra x 4kg', 'Lácteos', 120),
            (9, 'LAC-004', 'Manteca Calidad Extra x 500g', 'Lácteos', 85),
            (10, 'LAC-005', 'Dulce de Leche Repostero x 5kg', 'Lácteos', 60),
            
            # Insumos Gastronómicos del Sur (id=3)
            (11, 'PAN-001', 'Harina 0000 Especial Pizzería x 25kg', 'Panadería', 75),
            (12, 'PAN-002', 'Levadura Seca Instantánea x 500g', 'Panadería', 110),
            (13, 'ALM-003', 'Tomate Triturado en Lata x 4kg', 'Almacén', 130),
            (14, 'ALM-004', 'Aceitunas Verdes Descarozadas x 5kg', 'Almacén', 45),
            
            # Frigorífico & Carnes del Paraná (id=4)
            (15, 'CAR-001', 'Bife de Chorizo Envasado al Vacío x 5kg', 'Carnicería', 40),
            (16, 'CAR-002', 'Pechuga de Pollo Fresca x 10kg', 'Carnicería', 55),
            (17, 'FIA-001', 'Jamón Cocido Feteado x 3kg', 'Fiambrería', 45),
            
            # Bebidas & Bodegas Rosario (id=5)
            (18, 'BEB-001', 'Agua Mineral sin Gas x 1.5L (Pack 6u)', 'Bebidas', 160),
            (19, 'BEB-002', 'Gaseosa Cola Línea Premium x 1.5L (Pack 6u)', 'Bebidas', 140),
            (20, 'BEB-003', 'Cerveza Rubia Artesanal Barril 30L', 'Bebidas', 25),
            
            # Distribuidora Limpieza & Higiene Pro (id=6)
            (21, 'DES-001', 'Servilletas de Papel Interdobladas x 1000u', 'Descartables', 220),
            (22, 'LIM-001', 'Detergente Biodegradable Concentrado x 5L', 'Limpieza', 85),
            (23, 'LIM-002', 'Lavandina Concentrada Desinfectante x 5L', 'Limpieza', 90),
        ]
        cursor.executemany("""
            INSERT INTO ARTICULOS (id_articulo, id_articulo_proveedor, detalle, rubro, cantidad_stock)
            VALUES (?, ?, ?, ?, ?)
        """, articulos)
        print(f"OK: {len(articulos)} Artículos insertados.")
        
        # 5. Insertar Precios Negociados (id_proveedor, id_articulo, precio_final, descuento)
        precios = [
            # Distribuidora Central (id=1)
            (1, 1, 14500.0, 0.05),
            (1, 2, 3200.0, 0.0),
            (1, 3, 2800.0, 0.0),
            (1, 4, 8200.0, 0.0),
            (1, 5, 9500.0, 0.05),
            
            # Lácteos del Litoral (id=2)
            (2, 6, 1150.0, 0.0),
            (2, 7, 4200.0, 0.0),
            (2, 8, 21600.0, 0.08),
            (2, 9, 3800.0, 0.0),
            (2, 10, 15400.0, 0.05),
            
            # Insumos Gastronómicos (id=3)
            (3, 11, 18500.0, 0.10),
            (3, 12, 4600.0, 0.0),
            (3, 13, 6900.0, 0.0),
            (3, 14, 16800.0, 0.05),
            
            # Frigorífico Paraná (id=4)
            (4, 15, 34500.0, 0.05),
            (4, 16, 28000.0, 0.0),
            (4, 17, 19200.0, 0.0),
            
            # Bebidas Rosario (id=5)
            (5, 18, 4200.0, 0.0),
            (5, 19, 6800.0, 0.05),
            (5, 20, 48000.0, 0.10),
            
            # Limpieza Pro (id=6)
            (6, 21, 2400.0, 0.0),
            (6, 22, 6300.0, 0.0),
            (6, 23, 3900.0, 0.0),
        ]
        cursor.executemany("""
            INSERT INTO PRECIOS_NEGOCIADOS (id_proveedor, id_articulo, precio_final, descuento)
            VALUES (?, ?, ?, ?)
        """, precios)
        print(f"OK: {len(precios)} Precios negociados insertados.")

        # 6. Insertar Pedidos con estados 'Pendiente' y 'Consolidado'
        # Pedidos 1 a 5: 'Pendiente' (listos para la pantalla de Consolidación y Envío a Proveedor)
        # Pedidos 6 y 7: 'Consolidado' (listos para la pantalla de Recepción con Doble Control y Reparto)
        pedidos = [
            (1, 4, '2026-10-02', 'Pendiente'),    # Café Central
            (2, 5, '2026-10-02', 'Pendiente'),    # Panadería La Rosa
            (3, 6, '2026-10-02', 'Pendiente'),    # Restaurante Italia
            (4, 9, '2026-10-02', 'Pendiente'),    # Pizzería La Popular
            (5, 10, '2026-10-02', 'Pendiente'),   # Cervecería del Monumento
            (6, 7, '2026-10-01', 'Consolidado'),  # Bar Pellegrini (Listo para recibir/repartir)
            (7, 8, '2026-10-01', 'Consolidado'),  # Gran Hotel Rosario (Listo para recibir/repartir)
        ]
        cursor.executemany("""
            INSERT INTO PEDIDOS (id_pedido, id_user, fecha, estado)
            VALUES (?, ?, ?, ?)
        """, pedidos)
        
        detalles_pedidos = [
            # Pedido 1: Café Central (Café, Leche, Endulzante, Servilletas)
            (1, 1, 6),   # 6 Café en Grano
            (1, 6, 25),  # 25 Leche Entera
            (1, 2, 4),   # 4 Endulzante
            (1, 21, 5),  # 5 Servilletas
            
            # Pedido 2: Panadería La Rosa (Harina, Levadura, Manteca, Dulce de Leche)
            (2, 11, 4),  # 4 Harina 0000 25kg
            (2, 12, 6),  # 6 Levadura Seca
            (2, 9, 5),   # 5 Manteca
            (2, 10, 2),  # 2 Dulce de Leche 5kg
            
            # Pedido 3: Restaurante Italia (Mozzarella, Tomate, Bife, Aceite, Agua)
            (3, 8, 3),   # 3 Mozzarella 4kg
            (3, 13, 5),  # 5 Tomate Triturado 4kg
            (3, 15, 2),  # 2 Bife de Chorizo 5kg
            (3, 4, 3),   # 3 Aceite 5L
            (3, 18, 6),  # 6 Packs Agua Mineral
            
            # Pedido 4: Pizzería La Popular (Harina, Mozzarella, Tomate, Aceitunas, Servilletas)
            (4, 11, 6),  # 6 Harina 0000 25kg
            (4, 8, 5),   # 5 Mozzarella 4kg
            (4, 13, 4),  # 4 Tomate Triturado
            (4, 14, 2),  # 2 Aceitunas 5kg
            (4, 21, 4),  # 4 Servilletas
            
            # Pedido 5: Cervecería del Monumento (Barril Cerveza, Gaseosas, Limpieza)
            (5, 20, 3),  # 3 Barriles Cerveza 30L
            (5, 19, 8),  # 8 Packs Gaseosa
            (5, 22, 4),  # 4 Detergente 5L
            
            # Pedido 6 (Consolidado): Bar Pellegrini (Café, Leche, Jamón Cocido, Gaseosa)
            (6, 1, 4),   # 4 Café
            (6, 6, 15),  # 15 Leche
            (6, 17, 2),  # 2 Jamón Cocido
            (6, 19, 4),  # 4 Gaseosa
            
            # Pedido 7 (Consolidado): Gran Hotel Rosario (Café, Leche, Crema, Servilletas, Lavandina)
            (7, 1, 10),  # 10 Café
            (7, 6, 40),  # 40 Leche
            (7, 7, 8),   # 8 Crema de Leche
            (7, 21, 6),  # 6 Servilletas
            (7, 23, 4),  # 4 Lavandina
        ]
        cursor.executemany("""
            INSERT INTO DETALLE_PEDIDOS (id_pedido, id_articulo, cantidad_pedida)
            VALUES (?, ?, ?)
        """, detalles_pedidos)
        print(f"OK: {len(pedidos)} Pedidos y {len(detalles_pedidos)} ítems de detalle insertados.")

        # 7. Insertar Historial de Comprobantes de Proveedor (Doble Control ya registrado)
        comprobantes = [
            (1, 1, 'Factura', 'FC-A-0001-00045120', '2026-09-28', '2026-09-28 10:30:00', 'Recepción de pedido semanal - OK'),
            (2, 2, 'Remito', 'REM-R-0002-00018944', '2026-09-29', '2026-09-29 11:15:00', 'Faltante de 5 unidades de leche por rotura en flete'),
        ]
        cursor.executemany("""
            INSERT INTO COMPROBANTES_PROVEEDOR (id_comprobante, id_proveedor, tipo_comprobante, nro_comprobante, fecha_emision, fecha_recepcion, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, comprobantes)
        
        detalles_comprobantes = [
            # Comprobante 1 (Distribuidora Central - Factura)
            (1, 1, 14, 14, 14500.0, 14500.0),
            (1, 2, 4, 4, 3200.0, 3200.0),
            # Comprobante 2 (Lácteos del Litoral - Remito con entrega parcial)
            (2, 6, 55, 50, 1150.0, 1150.0),
        ]
        cursor.executemany("""
            INSERT INTO DETALLE_COMPROBANTES_PROVEEDOR (id_comprobante, id_articulo, cantidad_pedida, cantidad_recibida, precio_pactado, precio_facturado)
            VALUES (?, ?, ?, ?, ?, ?)
        """, detalles_comprobantes)
        print(f"OK: {len(comprobantes)} Comprobantes históricos de proveedores insertados.")

        # 8. Insertar Historial de Repartos y Remitos previos
        cursor.execute("""
            INSERT INTO PROCESOS_REPARTO (id_proceso, fecha_proceso, archivo_consolidado, estado_reparto)
            VALUES (1, '2026-09-29 16:00:00', 'scratch/consolidado_semana_39.xlsx', 'completado');
        """)
        
        remitos = [
            (1, 4, 1, '2026-09-29 16:30:00', 'Remito de entrega correspondiente a consolidado semanal'),
            (2, 5, 1, '2026-09-29 16:35:00', 'Remito de entrega correspondiente a consolidado semanal'),
        ]
        cursor.executemany("""
            INSERT INTO REMITOS (id_remito, id_user, id_proceso, fecha_emision, detalle_entrega)
            VALUES (?, ?, ?, ?, ?)
        """, remitos)
        
        detalles_remitos = [
            (1, 1, 4),   # Café Central recibió 4 Café
            (1, 6, 12),  # Café Central recibió 12 Leche (prorrateado)
            (2, 6, 38),  # Panadería La Rosa recibió 38 Leche (prorrateado)
        ]
        cursor.executemany("""
            INSERT INTO DETALLE_REMITOS (id_remito, id_articulo, cantidad_entregada)
            VALUES (?, ?, ?)
        """, detalles_remitos)
        print(f"OK: Historial de procesos de reparto y remitos insertado.")

        # 9. Insertar Notificaciones Realistas para Todos los Roles
        notificaciones = [
            # Notificaciones generales para Ejecutivos / Admin (id_user = NULL)
            (None, '📥 Nuevo pedido #1 registrado por Café Central ($118.900)', 'nuevo_pedido', '2026-10-02 09:15:00', 0),
            (None, '📥 Nuevo pedido #2 registrado por Panadería & Confitería La Rosa ($151.400)', 'nuevo_pedido', '2026-10-02 09:30:00', 0),
            (None, '📥 Nuevo pedido #3 registrado por Restaurante Italia Tradizionale ($203.000)', 'nuevo_pedido', '2026-10-02 10:05:00', 0),
            (None, '📥 Nuevo pedido #4 registrado por Pizzería La Popular ($251.700)', 'nuevo_pedido', '2026-10-02 10:45:00', 0),
            (None, '📥 Nuevo pedido #5 registrado por Cervecería del Monumento ($223.600)', 'nuevo_pedido', '2026-10-02 11:20:00', 0),
            
            # Notificaciones para Socios (id_user específico)
            (4, '✨ El Catálogo Único fue actualizado con nuevas listas y precios de temporada.', 'catalogo_actualizado', '2026-10-01 08:00:00', 1),
            (5, '✨ El Catálogo Único fue actualizado con nuevas listas y precios de temporada.', 'catalogo_actualizado', '2026-10-01 08:00:00', 1),
            (6, '✨ El Catálogo Único fue actualizado con nuevas listas y precios de temporada.', 'catalogo_actualizado', '2026-10-01 08:00:00', 0),
            (7, '📦 Tu Pedido #6 ha sido consolidado y enviado formalmente a los distribuidores.', 'pedido_consolidado', '2026-10-01 14:00:00', 0),
            (8, '📦 Tu Pedido #7 ha sido consolidado y enviado formalmente a los distribuidores.', 'pedido_consolidado', '2026-10-01 14:00:00', 0),
            (4, '🚚 Tu Remito de entrega #1 ya está disponible para recepción de mercadería.', 'reparto', '2026-09-29 16:30:00', 1),
            (5, '🚚 Tu Remito de entrega #2 ya está disponible para recepción de mercadería.', 'reparto', '2026-09-29 16:35:00', 1),
        ]
        cursor.executemany("""
            INSERT INTO NOTIFICACIONES (id_user, mensaje, tipo, fecha, leida)
            VALUES (?, ?, ?, ?, ?)
        """, notificaciones)
        print(f"OK: {len(notificaciones)} Notificaciones insertadas.")
        
        conn.commit()
        print("\n=======================================================")
        print("  ¡BASE DE DATOS POBLADA EXITOSAMENTE CON MOCK DATA!  ")
        print("=======================================================")
        
    except Exception as e:
        conn.rollback()
        print(f"Error al poblar la base de datos: {e}")
        raise e
    finally:
        conn.close()

if __name__ == '__main__':
    seed()
