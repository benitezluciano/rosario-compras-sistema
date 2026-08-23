from datetime import datetime
from src.database import Database
from src.models.notificacion_model import NotificacionModel

class RepartoModel:
    def obtener_articulos_recepcion(self):
        """
        Devuelve los artículos involucrados en pedidos 'Consolidado's con la cantidad demandada y el stock actual.
        """
        query = """
            SELECT a.id_articulo,
                   a.detalle AS articulo_detalle,
                   a.rubro,
                   COALESCE(pr.nombre, 'Sin Proveedor') AS proveedor_nombre,
                   SUM(dp.cantidad_pedida) AS cantidad_demandada,
                   a.cantidad_stock
            FROM DETALLE_PEDIDOS dp
            JOIN PEDIDOS p ON dp.id_pedido = p.id_pedido
            JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            LEFT JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
            LEFT JOIN PROVEEDORES pr ON pn.id_proveedor = pr.id_proveedor
            WHERE p.estado = 'Consolidado'
            GROUP BY a.id_articulo
            ORDER BY pr.nombre, a.detalle;
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def actualizar_stock_recibido(self, stock_map):
        """
        Actualiza la cantidad física de stock en la tabla ARTICULOS.
        stock_map: dict {id_articulo: cantidad_stock_nuevo}
        """
        with Database() as conn:
            cursor = conn.cursor()
            for id_art, cant in stock_map.items():
                cursor.execute(
                    "UPDATE ARTICULOS SET cantidad_stock = ? WHERE id_articulo = ?",
                    (cant, id_art)
                )
        return True

    def obtener_pedidos_consolidados(self):
        """
        Devuelve los pedidos en estado 'Consolidado'.
        """
        query = """
            SELECT p.id_pedido, u.nombre AS socio_nombre, p.estado, 
                   group_concat(a.detalle || ' x' || dp.cantidad_pedida, ', ') AS resumen_articulos
            FROM PEDIDOS p
            JOIN USERS u ON p.id_user = u.id
            LEFT JOIN DETALLE_PEDIDOS dp ON p.id_pedido = dp.id_pedido
            LEFT JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            WHERE p.estado = 'Consolidado'
            GROUP BY p.id_pedido;
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def validar_stock_vs_pedidos(self):
        """
        Compara la cantidad pedida contra el stock disponible.
        Si la demanda supera el stock, calcula el prorrateo equitativo.
        """
        query = """
            SELECT dp.id_pedido, dp.id_articulo, dp.cantidad_pedida, 
                   a.detalle, a.cantidad_stock
            FROM DETALLE_PEDIDOS dp
            JOIN PEDIDOS p ON dp.id_pedido = p.id_pedido
            JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            WHERE p.estado = 'Consolidado'
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            filas = [dict(row) for row in cursor.fetchall()]
            
        if not filas:
            return []
            
        por_articulo = {}
        for fila in filas:
            id_art = fila['id_articulo']
            if id_art not in por_articulo:
                por_articulo[id_art] = {
                    'detalle': fila['detalle'],
                    'cantidad_stock': fila['cantidad_stock'],
                    'pedidos': []
                }
            por_articulo[id_art]['pedidos'].append((fila['id_pedido'], fila['cantidad_pedida']))
            
        discrepancias = []
        
        for id_art, info in por_articulo.items():
            total_pedido = sum(cant for _, cant in info['pedidos'])
            stock_disponible = info['cantidad_stock']
            
            if total_pedido > stock_disponible:
                ajustes = {}
                if stock_disponible <= 0:
                    for id_ped, _ in info['pedidos']:
                        ajustes[id_ped] = 0
                else:
                    factor = stock_disponible / total_pedido
                    pre_asignados = []
                    suma_asignada = 0
                    
                    for id_ped, cant in info['pedidos']:
                        share = cant * factor
                        asignado = int(share)
                        fraccion = share - asignado
                        ajustes[id_ped] = asignado
                        suma_asignada += asignado
                        pre_asignados.append({
                            'id_pedido': id_ped,
                            'fraccion': fraccion
                        })
                        
                    remanente = stock_disponible - suma_asignada
                    if remanente > 0:
                        pre_asignados.sort(key=lambda x: x['fraccion'], reverse=True)
                        for i in range(int(remanente)):
                            id_ped_rem = pre_asignados[i % len(pre_asignados)]['id_pedido']
                            ajustes[id_ped_rem] += 1
                
                discrepancias.append({
                    'id_articulo': id_art,
                    'detalle': info['detalle'],
                    'solicitado': total_pedido,
                    'disponible': stock_disponible,
                    'ajustes': ajustes
                })
                
        return discrepancias

    def ejecutar_reparto_masivo(self, ajustes=None):
        """
        Ejecuta el reparto para todos los pedidos en 'Consolidado', genera REMITOS y notifica a los socios.
        """
        fecha_proceso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_emision = datetime.now().strftime("%Y-%m-%d")

        remitos_generados = []

        with Database() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id_pedido, id_user FROM PEDIDOS WHERE estado = 'Consolidado'"
            )
            pedidos_consolidados = [dict(row) for row in cursor.fetchall()]
            
            if not pedidos_consolidados:
                return False
            
            # Registrar proceso de reparto
            cursor.execute(
                """
                INSERT INTO PROCESOS_REPARTO (fecha_proceso, archivo_consolidado, estado_reparto)
                VALUES (?, ?, ?)
                """,
                (fecha_proceso, None, 'completado')
            )
            id_proceso = cursor.lastrowid
            
            for pedido in pedidos_consolidados:
                id_pedido = pedido['id_pedido']
                id_user = pedido['id_user']
                
                cursor.execute(
                    "SELECT id_articulo, cantidad_pedida FROM DETALLE_PEDIDOS WHERE id_pedido = ?",
                    (id_pedido,)
                )
                items = cursor.fetchall()
                
                # Descontar stock
                for item in items:
                    id_articulo = item['id_articulo']
                    cantidad_final = item['cantidad_pedida']
                    
                    if ajustes and (id_pedido, id_articulo) in ajustes:
                        cantidad_final = ajustes[(id_pedido, id_articulo)]
                    
                    cursor.execute(
                        """
                        UPDATE ARTICULOS 
                        SET cantidad_stock = MAX(0, cantidad_stock - ?) 
                        WHERE id_articulo = ?
                        """,
                        (cantidad_final, id_articulo)
                    )
                
                # Actualizar estado del pedido a 'Procesado'
                cursor.execute(
                    "UPDATE PEDIDOS SET estado = 'Procesado' WHERE id_pedido = ?",
                    (id_pedido,)
                )
                
                # Insertar remito
                cursor.execute(
                    """
                    INSERT INTO REMITOS (id_user, id_proceso, fecha_emision, detalle_entrega)
                    VALUES (?, ?, ?, ?)
                    """,
                    (id_user, id_proceso, fecha_emision, f"Remito emitido para el pedido #{id_pedido}")
                )
                id_remito = cursor.lastrowid
                remitos_generados.append((id_remito, id_pedido, id_user))
                
                # Insertar detalles de remito
                for item in items:
                    id_articulo = item['id_articulo']
                    cantidad_final = item['cantidad_pedida']
                    if ajustes and (id_pedido, id_articulo) in ajustes:
                        cantidad_final = ajustes[(id_pedido, id_articulo)]
                        
                    cursor.execute(
                        """
                        INSERT INTO DETALLE_REMITOS (id_remito, id_articulo, cantidad_entregada)
                        VALUES (?, ?, ?)
                        """,
                        (id_remito, id_articulo, cantidad_final)
                    )

        # Emitir notificaciones de entrega a los socios
        try:
            notif = NotificacionModel()
            for id_remito, id_pedido, id_user in remitos_generados:
                notif.crear_notificacion(
                    mensaje=f"¡Tu Remito #{id_remito} (Pedido #{id_pedido}) fue generado! La mercadería está lista para su retiro/envío.",
                    tipo="reparto",
                    id_user=id_user
                )
        except Exception as e:
            print(f"Advertencia al notificar remitos: {e}")

        return True
