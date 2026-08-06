from src.database import Database

class RepartoModel:
    def obtener_pedidos_consolidados(self):
        """
        Consulta y devuelve todos los pedidos que estén en estado 'Pendiente' o 'Consolidado',
        generando un resumen de artículos y cantidades concatenados en un solo string por pedido.
        """
        query = """
            SELECT p.id_pedido, u.nombre AS socio_nombre, p.estado, 
                   group_concat(a.detalle || ' x' || dp.cantidad_pedida, ', ') AS resumen_articulos
            FROM PEDIDOS p
            JOIN USERS u ON p.id_user = u.id
            LEFT JOIN DETALLE_PEDIDOS dp ON p.id_pedido = dp.id_pedido
            LEFT JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            WHERE p.estado IN ('Pendiente', 'Consolidado')
            GROUP BY p.id_pedido;
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def validar_stock_vs_pedidos(self):
        """
        Compara la cantidad pedida de cada artículo contra su stock disponible
        para todos los pedidos consolidados.
        Si la demanda supera el stock físico, calcula un reparto proporcional equitativo.
        Retorna una lista de discrepancias:
        [
            {
                'id_articulo': int,
                'detalle': str,
                'solicitado': int,
                'disponible': int,
                'ajustes': {id_pedido: cantidad_ajustada}
            }
        ]
        Si todo está bien, retorna una lista vacía.
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
            
        # Agrupar por artículo
        por_articulo = {}
        for fila in filas:
            id_art = fila['id_articulo']
            if id_art not in por_articulo:
                por_articulo[id_art] = {
                    'detalle': fila['detalle'],
                    'cantidad_stock': fila['cantidad_stock'],
                    'pedidos': [] # Lista de tuplas: (id_pedido, cantidad_pedida)
                }
            por_articulo[id_art]['pedidos'].append((fila['id_pedido'], fila['cantidad_pedida']))
            
        discrepancias = []
        
        for id_art, info in por_articulo.items():
            total_pedido = sum(cant for _, cant in info['pedidos'])
            stock_disponible = info['cantidad_stock']
            
            if total_pedido > stock_disponible:
                # Calcular el reparto proporcional equitativo (método de cuotas con remanente)
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
                        asignado = int(share) # Redondear hacia abajo (floor)
                        fraccion = share - asignado # Fracción remanente
                        ajustes[id_ped] = asignado
                        suma_asignada += asignado
                        pre_asignados.append({
                            'id_pedido': id_ped,
                            'fraccion': fraccion
                        })
                        
                    # Distribuir el remanente restante por mayor fracción
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
        Ejecuta la asignación de reparto para todos los pedidos en estado 'Consolidado'.
        Descuenta stock, cambia estados a 'Procesado', crea un registro de proceso, 
        y genera los correspondientes REMITOS y DETALLE_REMITOS de forma transaccional.
        
        ajustes: Diccionario opcional con clave (id_pedido, id_articulo) -> cantidad_ajustada
        """
        from datetime import datetime
        fecha_proceso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_emision = datetime.now().strftime("%Y-%m-%d")

        with Database() as conn:
            cursor = conn.cursor()
            
            # 1. Buscar todos los id_pedido e id_user de la tabla PEDIDOS cuyo estado sea 'Consolidado'
            cursor.execute(
                "SELECT id_pedido, id_user FROM PEDIDOS WHERE estado = 'Consolidado'"
            )
            pedidos_consolidados = [dict(row) for row in cursor.fetchall()]
            
            if not pedidos_consolidados:
                return False
            
            # 2. Insertar un nuevo registro en PROCESOS_REPARTO con la fecha actual y estado 'completado'
            cursor.execute(
                """
                INSERT INTO PROCESOS_REPARTO (fecha_proceso, archivo_consolidado, estado_reparto)
                VALUES (?, ?, ?)
                """,
                (fecha_proceso, None, 'completado')
            )
            id_proceso = cursor.lastrowid
            
            # 3. Procesar cada pedido
            for pedido in pedidos_consolidados:
                id_pedido = pedido['id_pedido']
                id_user = pedido['id_user']
                
                # Buscar artículos y cantidades en DETALLE_PEDIDOS
                cursor.execute(
                    "SELECT id_articulo, cantidad_pedida FROM DETALLE_PEDIDOS WHERE id_pedido = ?",
                    (id_pedido,)
                )
                items = cursor.fetchall()
                
                # Descontar la cantidad_pedida (o ajustada) de cantidad_stock en la tabla ARTICULOS
                for item in items:
                    id_articulo = item['id_articulo']
                    cantidad_original = item['cantidad_pedida']
                    
                    # Verificar si existe un recorte asignado para este artículo en este pedido
                    cantidad_final = cantidad_original
                    if ajustes and (id_pedido, id_articulo) in ajustes:
                        cantidad_final = ajustes[(id_pedido, id_articulo)]
                    
                    cursor.execute(
                        """
                        UPDATE ARTICULOS 
                        SET cantidad_stock = cantidad_stock - ? 
                        WHERE id_articulo = ?
                        """,
                        (cantidad_final, id_articulo)
                    )
                
                # Actualizar el estado del pedido a 'Procesado'
                cursor.execute(
                    "UPDATE PEDIDOS SET estado = 'Procesado' WHERE id_pedido = ?",
                    (id_pedido,)
                )
                
                # Insertar el remito correspondiente
                cursor.execute(
                    """
                    INSERT INTO REMITOS (id_user, id_proceso, fecha_emision, detalle_entrega)
                    VALUES (?, ?, ?, ?)
                    """,
                    (id_user, id_proceso, fecha_emision, f"Remito generado automaticamente para el pedido #{id_pedido}")
                )
                id_remito = cursor.lastrowid
                
                # Insertar los renglones en DETALLE_REMITOS
                for item in items:
                    id_articulo = item['id_articulo']
                    cantidad_original = item['cantidad_pedida']
                    
                    # Utilizar la cantidad final para la entrega del remito
                    cantidad_final = cantidad_original
                    if ajustes and (id_pedido, id_articulo) in ajustes:
                        cantidad_final = ajustes[(id_pedido, id_articulo)]
                        
                    cursor.execute(
                        """
                        INSERT INTO DETALLE_REMITOS (id_remito, id_articulo, cantidad_entregada)
                        VALUES (?, ?, ?)
                        """,
                        (id_remito, id_articulo, cantidad_final)
                    )
            
            return True
