import sqlite3
import os
import sys
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from src.database import migrar_db
from src.config.empresa import PUNTO_VENTA_REMITOS
from src.utils.id_generator import generar_codigo_pedido, generar_codigo_remito, generar_codigo_orden_compra, generar_numero_remito

DB_PATH = os.path.join(BASE_DIR, "database.db")
SQL_PATH = os.path.join(BASE_DIR, "db", "rosario_compras.sql")

# Orden de borrado: primero las tablas dependientes
TABLAS = [
    "DETALLE_COMPROBANTES_PROVEEDOR",
    "COMPROBANTES_PROVEEDOR",
    "DETALLE_REMITOS",
    "REMITOS",
    "PROCESOS_REPARTO",
    "NOTIFICACIONES",
    "DETALLE_PEDIDOS",
    "PEDIDOS",
    "ORDENES_COMPRA",
    "PRECIOS_NEGOCIADOS",
    "ARTICULOS",
    "PROVEEDORES",
    "USERS",
]


def seed():
    print(f"Conectando a la base de datos en: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Recrear el esquema desde cero (garantiza columnas, FKs y CHECKs actualizados)
        cursor.execute("PRAGMA foreign_keys = OFF;")
        for tabla in TABLAS:
            cursor.execute(f"DROP TABLE IF EXISTS {tabla};")
        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON;")

        with open(SQL_PATH, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
        migrar_db(conn)

        # 2. Usuarios (1 Admin, 2 Ejecutivos, 8 Socios del rubro gastronómico/hotelero)
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
        # Datos fiscales y de entrega de los socios (se imprimen en los remitos).
        # SIMULADOS: el CUIT queda como 'XX-XXXXXXXX-X' y los domicilios son ficticios.
        CUIT_SIMULADO = 'XX-XXXXXXXX-X'
        datos_socios = {
            4: ('Responsable Inscripto', 'Bv. Oroño 1450, Pichincha, Rosario'),
            5: ('Monotributista', 'Córdoba 1230, Centro, Rosario'),
            6: ('Responsable Inscripto', 'Av. Pellegrini 1850, Rosario'),
            7: ('Responsable Inscripto', 'Mendoza 3400, Echesortu, Rosario'),
            8: ('Responsable Inscripto', 'Av. Costanera 500, Rosario'),
            9: ('Monotributista', 'Av. Eva Perón 8100, Fisherton, Rosario'),
            10: ('Responsable Inscripto', 'Santa Fe 1000, Monumento, Rosario'),
            11: ('Monotributista', 'Av. Belgrano 2500, Parque Urquiza, Rosario'),
        }
        cursor.executemany("""
            INSERT INTO USERS (id, nombre, email, password_hash, role, cuit_dni, condicion_iva, domicilio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (i, n, e, pw, r,
             CUIT_SIMULADO if i in datos_socios else None,
             datos_socios.get(i, (None, None))[0],
             datos_socios.get(i, (None, None))[1])
            for i, n, e, pw, r in usuarios
        ])
        print(f"OK: {len(usuarios)} Usuarios insertados con contraseñas seguras (datos fiscales de socios simulados).")

        # 3. Proveedores
        #    lista_habilitada = 1 → ciclo de pedidos abierto (los socios ven la hoja)
        #    lista_habilitada = 0 → ciclo cerrado (pedidos ya consolidados, esperando entrega)
        proveedores = [
            (1, 2, 'Distribuidora Central Rosario', 'ventas@distribuidoracentral.com', '(0341) 482-9000', 'Av. Pellegrini 1500, Rosario', 1, '2026-10-01 08:00:00'),
            (2, 2, 'Lácteos del Litoral', 'pedidos@lacteosdellitoral.com', '(0341) 440-1122', 'Calle Santa Fe 2300, Rosario', 1, '2026-10-01 08:05:00'),
            (3, 2, 'Insumos Gastronómicos del Sur', 'contacto@insumosdelsur.com', '(0341) 425-7788', 'Bv. Oroño 850, Rosario', 1, '2026-10-01 08:10:00'),
            (4, 2, 'Frigorífico & Carnes del Paraná', 'ventas@carnesdelparana.com.ar', '(0341) 456-3344', 'Av. Circunvalación 4200, Rosario', 0, '2026-09-25 08:00:00'),
            (5, 3, 'Bebidas & Bodegas Rosario', 'pedidos@bodegasrosario.com', '(0341) 438-5566', 'San Lorenzo 1120, Rosario', 1, '2026-10-01 08:15:00'),
            (6, 3, 'Distribuidora Limpieza & Higiene Pro', 'info@limpiezapro.com.ar', '(0341) 471-8899', 'Salta 2840, Rosario', 0, '2026-09-25 08:05:00'),
        ]
        cursor.executemany("""
            INSERT INTO PROVEEDORES (id_proveedor, id_user, nombre, email, telefono, direccion, lista_habilitada, fecha_habilitacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, proveedores)
        print(f"OK: {len(proveedores)} Proveedores insertados (4 listas habilitadas, 2 cerradas).")

        # 4. Artículos del catálogo (cada artículo pertenece a la lista de un único proveedor)
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
        # Unidad de venta/entrega de cada artículo (se imprime en el remito)
        unidades = {
            1: 'Paquete', 2: 'Caja', 3: 'Caja', 4: 'Bidón', 5: 'Bolsa',
            6: 'Unidad', 7: 'Unidad', 8: 'Barra', 9: 'Unidad', 10: 'Balde',
            11: 'Bolsa', 12: 'Paquete', 13: 'Lata', 14: 'Balde',
            15: 'Caja', 16: 'Caja', 17: 'Paquete',
            18: 'Pack', 19: 'Pack', 20: 'Barril',
            21: 'Paquete', 22: 'Bidón', 23: 'Bidón',
        }
        cursor.executemany("""
            INSERT INTO ARTICULOS (id_articulo, id_articulo_proveedor, detalle, rubro, cantidad_stock, unidad)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [(*a, unidades.get(a[0], 'Unidad')) for a in articulos])
        print(f"OK: {len(articulos)} Artículos insertados.")

        # 5. Precios negociados (id_proveedor, id_articulo, precio_final, descuento)
        #    precio_base se deriva: precio_final = precio_base * (1 - descuento)
        precios = [
            (1, 1, 14500.0, 0.05), (1, 2, 3200.0, 0.0), (1, 3, 2800.0, 0.0), (1, 4, 8200.0, 0.0), (1, 5, 9500.0, 0.05),
            (2, 6, 1150.0, 0.0), (2, 7, 4200.0, 0.0), (2, 8, 21600.0, 0.08), (2, 9, 3800.0, 0.0), (2, 10, 15400.0, 0.05),
            (3, 11, 18500.0, 0.10), (3, 12, 4600.0, 0.0), (3, 13, 6900.0, 0.0), (3, 14, 16800.0, 0.05),
            (4, 15, 34500.0, 0.05), (4, 16, 28000.0, 0.0), (4, 17, 19200.0, 0.0),
            (5, 18, 4200.0, 0.0), (5, 19, 6800.0, 0.05), (5, 20, 48000.0, 0.10),
            (6, 21, 2400.0, 0.0), (6, 22, 6300.0, 0.0), (6, 23, 3900.0, 0.0),
        ]
        cursor.executemany("""
            INSERT INTO PRECIOS_NEGOCIADOS (id_proveedor, id_articulo, precio_base, precio_final, descuento)
            VALUES (?, ?, ?, ?, ?)
        """, [(p, a, round(pf / (1.0 - d), 2), pf, d) for p, a, pf, d in precios])
        precio_de = {(p, a): pf for p, a, pf, _ in precios}
        print(f"OK: {len(precios)} Precios negociados insertados.")

        # 6. Órdenes de compra de los ciclos ya consolidados
        #    (id_orden, id_proveedor, id_user ejecutivo, fecha, fecha_envio_email, email_destino)
        #    El archivo Excel no se incluye: el sistema lo genera al abrirlo por primera vez.
        ordenes = [
            (1, 4, 2, '2026-09-27 14:00:00', '2026-09-27 14:10:00', 'ventas@carnesdelparana.com.ar'),
            (2, 6, 3, '2026-09-27 14:00:00', None, None),
            (3, 1, 2, '2026-09-23 10:00:00', '2026-09-23 10:15:00', 'ventas@distribuidoracentral.com'),
            (4, 2, 2, '2026-09-23 10:05:00', '2026-09-23 10:20:00', 'pedidos@lacteosdellitoral.com'),
        ]
        cursor.executemany("""
            INSERT INTO ORDENES_COMPRA (id_orden_compra, id_proveedor, id_user, codigo_comercial, fecha, fecha_envio_email, email_destino)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [(i, p, u, generar_codigo_orden_compra(i, f), f, fe, em) for i, p, u, f, fe, em in ordenes])
        cod_oc = {i: generar_codigo_orden_compra(i, f) for i, _, _, f, _, _ in ordenes}

        # 7. Pedidos: cada pedido es de UN socio para UN proveedor
        #    (id_pedido, id_user, id_proveedor, fecha, estado)
        pedidos = [
            # --- Ciclo abierto: 'Pendiente' (pantalla de Consolidación) ---
            (1, 4, 1, '2026-10-02', 'Pendiente'),    # Café Central → Distribuidora Central
            (2, 4, 2, '2026-10-02', 'Pendiente'),    # Café Central → Lácteos
            (3, 5, 3, '2026-10-02', 'Pendiente'),    # Panadería La Rosa → Insumos del Sur
            (4, 5, 2, '2026-10-02', 'Pendiente'),    # Panadería La Rosa → Lácteos
            (5, 6, 2, '2026-10-02', 'Pendiente'),    # Restaurante Italia → Lácteos
            (6, 6, 3, '2026-10-02', 'Pendiente'),    # Restaurante Italia → Insumos del Sur
            (7, 6, 1, '2026-10-02', 'Pendiente'),    # Restaurante Italia → Distribuidora Central
            (8, 9, 3, '2026-10-02', 'Pendiente'),    # Pizzería La Popular → Insumos del Sur
            (9, 9, 2, '2026-10-02', 'Pendiente'),    # Pizzería La Popular → Lácteos
            (10, 10, 5, '2026-10-02', 'Pendiente'),  # Cervecería del Monumento → Bebidas
            # --- Ciclo cerrado: 'Consolidado' (pantalla de Recepción y Reparto) ---
            (11, 6, 4, '2026-09-26', 'Consolidado'),  # Restaurante Italia → Frigorífico
            (12, 7, 4, '2026-09-26', 'Consolidado'),  # Bar Pellegrini → Frigorífico
            (13, 8, 6, '2026-09-26', 'Consolidado'),  # Gran Hotel → Limpieza Pro
            (14, 7, 6, '2026-09-26', 'Consolidado'),  # Bar Pellegrini → Limpieza Pro
            # --- Historial: 'Procesado' (ya repartidos, con remito) ---
            (15, 4, 1, '2026-09-22', 'Procesado'),    # Café Central → Distribuidora Central
            (16, 5, 2, '2026-09-22', 'Procesado'),    # Panadería La Rosa → Lácteos
        ]
        # Pedidos ya consolidados → orden de compra en la que se agruparon
        orden_de_pedido = {11: 1, 12: 1, 13: 2, 14: 2, 15: 3, 16: 4}
        cursor.executemany("""
            INSERT INTO PEDIDOS (id_pedido, id_user, id_proveedor, codigo_comercial, fecha, estado, id_orden_compra)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [(i, u, p, generar_codigo_pedido(i, f), f, e, orden_de_pedido.get(i)) for i, u, p, f, e in pedidos])
        prov_de_pedido = {i: p for i, _, p, _, _ in pedidos}

        # (id_pedido, id_articulo, cantidad) — el precio se congela desde la lista del proveedor del pedido
        detalles_pedidos = [
            (1, 1, 6), (1, 2, 4),                    # Café Central: Café, Endulzante
            (2, 6, 25),                              # Café Central: Leche
            (3, 11, 4), (3, 12, 6),                  # Panadería: Harina, Levadura
            (4, 9, 5), (4, 10, 2),                   # Panadería: Manteca, Dulce de Leche
            (5, 8, 3),                               # Restaurante: Mozzarella
            (6, 13, 5),                              # Restaurante: Tomate Triturado
            (7, 4, 3),                               # Restaurante: Aceite
            (8, 11, 6), (8, 13, 4), (8, 14, 2),      # Pizzería: Harina, Tomate, Aceitunas
            (9, 8, 5),                               # Pizzería: Mozzarella
            (10, 20, 3), (10, 19, 8),                # Cervecería: Barril, Gaseosas
            (11, 15, 2),                             # Restaurante: Bife de Chorizo
            (12, 17, 2), (12, 16, 3),                # Bar Pellegrini: Jamón, Pollo
            (13, 21, 6), (13, 23, 4),                # Gran Hotel: Servilletas, Lavandina
            (14, 22, 2),                             # Bar Pellegrini: Detergente
            (15, 1, 4),                              # Café Central (histórico): Café
            (16, 6, 40),                             # Panadería (histórico): Leche
        ]
        cursor.executemany("""
            INSERT INTO DETALLE_PEDIDOS (id_pedido, id_articulo, cantidad_pedida, precio_unitario)
            VALUES (?, ?, ?, ?)
        """, [(ped, art, cant, precio_de[(prov_de_pedido[ped], art)]) for ped, art, cant in detalles_pedidos])
        print(f"OK: {len(pedidos)} Pedidos (uno por proveedor) y {len(detalles_pedidos)} ítems de detalle insertados.")

        # Totales y cantidad de pedidos de cada orden, calculados desde sus pedidos
        cursor.execute("""
            UPDATE ORDENES_COMPRA SET
                cantidad_pedidos = (SELECT COUNT(*) FROM PEDIDOS p WHERE p.id_orden_compra = ORDENES_COMPRA.id_orden_compra),
                total = (SELECT COALESCE(SUM(dp.cantidad_pedida * dp.precio_unitario), 0)
                         FROM DETALLE_PEDIDOS dp JOIN PEDIDOS p ON p.id_pedido = dp.id_pedido
                         WHERE p.id_orden_compra = ORDENES_COMPRA.id_orden_compra)
        """)
        print(f"OK: {len(ordenes)} Órdenes de compra insertadas (2 pendientes de entrega, 2 ya repartidas).")

        # 8. Historial de comprobantes de proveedor (doble control ya registrado)
        comprobantes = [
            (1, 1, 'Factura', 'FC-A-0001-00045120', '2026-09-28', '2026-09-28 10:30:00', 'Recepción de pedido semanal - OK'),
            (2, 2, 'Remito', 'REM-R-0002-00018944', '2026-09-29', '2026-09-29 11:15:00', 'Faltante de 2 unidades de leche por rotura en flete'),
        ]
        cursor.executemany("""
            INSERT INTO COMPROBANTES_PROVEEDOR (id_comprobante, id_proveedor, tipo_comprobante, nro_comprobante, fecha_emision, fecha_recepcion, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, comprobantes)

        detalles_comprobantes = [
            (1, 1, 4, 4, 14500.0, 14500.0),     # Distribuidora Central: Café OK
            (2, 6, 40, 38, 1150.0, 1150.0),     # Lácteos: Leche con faltante de 2
        ]
        cursor.executemany("""
            INSERT INTO DETALLE_COMPROBANTES_PROVEEDOR (id_comprobante, id_articulo, cantidad_pedida, cantidad_recibida, precio_pactado, precio_facturado)
            VALUES (?, ?, ?, ?, ?, ?)
        """, detalles_comprobantes)
        print(f"OK: {len(comprobantes)} Comprobantes históricos de proveedores insertados.")

        # 9. Historial de repartos y remitos (un remito por pedido)
        cursor.executemany("""
            INSERT INTO PROCESOS_REPARTO (id_proceso, fecha_proceso, archivo_consolidado, estado_reparto)
            VALUES (?, ?, ?, ?)
        """, [
            (1, '2026-09-28 16:00:00', 'FC-A-0001-00045120', 'completado'),
            (2, '2026-09-29 16:00:00', 'REM-R-0002-00018944', 'completado'),
        ])

        # (id_remito, id_user, id_proceso, id_pedido, id_proveedor, fecha_emision)
        remitos = [
            (1, 4, 1, 15, 1, '2026-09-28'),
            (2, 5, 2, 16, 2, '2026-09-29'),
        ]
        numeros_remito = {}
        for id_rem, id_user, id_proc, id_ped, id_prov, fecha in remitos:
            cod_rem = generar_codigo_remito(id_rem, id_user)
            numero = generar_numero_remito(id_rem, PUNTO_VENTA_REMITOS)
            numeros_remito[id_rem] = numero
            cursor.execute("""
                INSERT INTO REMITOS (id_remito, id_user, id_proceso, id_pedido, id_proveedor, codigo_comercial, numero_remito, fecha_emision, detalle_entrega)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (id_rem, id_user, id_proc, id_ped, id_prov, cod_rem, numero, fecha,
                  f"Remito {numero} (ref. {cod_rem}) emitido para pedido {generar_codigo_pedido(id_ped, '2026-09-22')}"))

        cursor.executemany("""
            INSERT INTO DETALLE_REMITOS (id_remito, id_articulo, cantidad_entregada)
            VALUES (?, ?, ?)
        """, [
            (1, 1, 4),    # Café Central recibió 4 Café
            (2, 6, 38),   # Panadería La Rosa recibió 38 Leche (faltante de 2)
        ])
        print("OK: Historial de procesos de reparto y remitos insertado.")

        # 10. Notificaciones realistas para todos los roles
        def cod(id_ped):
            fecha = next(f for i, _, _, f, _ in pedidos if i == id_ped)
            return generar_codigo_pedido(id_ped, fecha)

        notificaciones = [
            # Ejecutivos / Admin (id_user = NULL)
            (None, f"El socio Café Central (Pichincha) registró el Pedido {cod(1)} para 'Distribuidora Central Rosario' (2 productos).", 'nuevo_pedido', '2026-10-02 09:15:00', 0),
            (None, f"El socio Café Central (Pichincha) registró el Pedido {cod(2)} para 'Lácteos del Litoral' (1 productos).", 'nuevo_pedido', '2026-10-02 09:16:00', 0),
            (None, f"El socio Panadería & Confitería La Rosa (Centro) registró el Pedido {cod(3)} para 'Insumos Gastronómicos del Sur' (2 productos).", 'nuevo_pedido', '2026-10-02 09:30:00', 0),
            (None, f"El socio Restaurante Italia Tradizionale (Pellegrini) registró el Pedido {cod(5)} para 'Lácteos del Litoral' (1 productos).", 'nuevo_pedido', '2026-10-02 10:05:00', 0),
            (None, f"El socio Pizzería La Popular (Fisherton) registró el Pedido {cod(8)} para 'Insumos Gastronómicos del Sur' (3 productos).", 'nuevo_pedido', '2026-10-02 10:45:00', 0),
            (None, f"El socio Cervecería del Monumento (Monumento) registró el Pedido {cod(10)} para 'Bebidas & Bodegas Rosario' (2 productos).", 'nuevo_pedido', '2026-10-02 11:20:00', 0),

            # Socios (id_user específico)
            (4, "El Ejecutivo habilitó la lista de precios de 'Distribuidora Central Rosario' (5 productos). Ya puedes cargar tu pedido.", 'catalogo_actualizado', '2026-10-01 08:00:00', 1),
            (5, "El Ejecutivo habilitó la lista de precios de 'Lácteos del Litoral' (5 productos). Ya puedes cargar tu pedido.", 'catalogo_actualizado', '2026-10-01 08:05:00', 1),
            (6, "El Ejecutivo habilitó la lista de precios de 'Insumos Gastronómicos del Sur' (4 productos). Ya puedes cargar tu pedido.", 'catalogo_actualizado', '2026-10-01 08:10:00', 0),
            (7, f"Tu Pedido {cod(12)} para 'Frigorífico & Carnes del Paraná' fue consolidado en la Orden de Compra {cod_oc[1]} para su envío al proveedor.", 'pedido_consolidado', '2026-09-27 14:00:00', 0),
            (8, f"Tu Pedido {cod(13)} para 'Distribuidora Limpieza & Higiene Pro' fue consolidado en la Orden de Compra {cod_oc[2]} para su envío al proveedor.", 'pedido_consolidado', '2026-09-27 14:00:00', 0),
            (4, f"¡Tu Remito {numeros_remito[1]} (Pedido {cod(15)}) de Distribuidora Central Rosario fue emitido! La mercadería está lista para su entrega.", 'reparto', '2026-09-28 16:30:00', 1),
            (5, f"¡Tu Remito {numeros_remito[2]} (Pedido {cod(16)}) de Lácteos del Litoral fue emitido! La mercadería está lista para su entrega.", 'reparto', '2026-09-29 16:35:00', 1),
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
