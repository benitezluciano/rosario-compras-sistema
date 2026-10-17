from datetime import datetime
from src.database import Database
from src.models.notificacion_model import NotificacionModel
from src.utils.id_generator import generar_codigo_pedido, generar_codigo_comprobante, generar_codigo_remito
from src.services.pdf_service import PdfService

class RepartoModel:
    def obtener_proveedores_con_pedidos(self):
        """Devuelve los proveedores con artículos en pedidos consolidados."""
        query = """
            SELECT DISTINCT pr.id_proveedor, pr.nombre
            FROM DETALLE_PEDIDOS dp
            JOIN PEDIDOS p ON dp.id_pedido = p.id_pedido
            JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
            JOIN PROVEEDORES pr ON pn.id_proveedor = pr.id_proveedor
            WHERE p.estado = 'Consolidado'
            ORDER BY pr.nombre ASC;
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def obtener_pedidos_consolidados_por_proveedor(self, id_proveedor=None):
        """
        Devuelve el listado de pedidos consolidados disponibles para el proveedor seleccionado.
        Permite seleccionar individualmente un pedido consolidado cuando hay 2 o más simultáneos.
        """
        query = """
            SELECT DISTINCT p.id_pedido, p.codigo_comercial, p.fecha, p.estado, u.nombre AS socio_nombre, u.email AS socio_email,
                   pr.id_proveedor, pr.nombre AS proveedor_nombre,
                   group_concat(a.detalle || ' x' || dp.cantidad_pedida, ', ') AS resumen_articulos
            FROM PEDIDOS p
            JOIN USERS u ON p.id_user = u.id
            JOIN DETALLE_PEDIDOS dp ON p.id_pedido = dp.id_pedido
            JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
            JOIN PROVEEDORES pr ON pn.id_proveedor = pr.id_proveedor
            WHERE p.estado = 'Consolidado'
        """
        params = []
        if id_proveedor is not None:
            query += " AND pr.id_proveedor = ?"
            params.append(id_proveedor)

        query += " GROUP BY p.id_pedido ORDER BY p.id_pedido DESC;"

        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            filas = []
            for row in cursor.fetchall():
                ped = dict(row)
                if not ped.get('codigo_comercial'):
                    ped['codigo_comercial'] = generar_codigo_pedido(ped['id_pedido'], ped['fecha'])
                filas.append(ped)
            return filas

    def obtener_articulos_control_recepcion(self, id_proveedor=None, id_pedido=None):
        """
        Devuelve los artículos involucrados en pedidos 'Consolidado' con:
        - Cantidad demandada por los socios (Logística)
        - Precio pactado en catálogo (Compras)
        - Stock físico actual
        """
        query = """
            SELECT a.id_articulo,
                   a.id_articulo_proveedor,
                   a.detalle AS articulo_detalle,
                   COALESCE(pr.id_proveedor, 0) AS id_proveedor,
                   COALESCE(pr.nombre, 'Sin Proveedor') AS proveedor_nombre,
                   SUM(dp.cantidad_pedida) AS cantidad_demandada,
                   COALESCE(pn.precio_final, 0.0) AS precio_pactado,
                   a.cantidad_stock
            FROM DETALLE_PEDIDOS dp
            JOIN PEDIDOS p ON dp.id_pedido = p.id_pedido
            JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            LEFT JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
            LEFT JOIN PROVEEDORES pr ON pn.id_proveedor = pr.id_proveedor
            WHERE p.estado = 'Consolidado'
        """
        params = []
        if id_proveedor is not None:
            query += " AND pr.id_proveedor = ?"
            params.append(id_proveedor)
        if id_pedido is not None:
            query += " AND p.id_pedido = ?"
            params.append(id_pedido)

        query += " GROUP BY a.id_articulo ORDER BY pr.nombre, a.detalle;"
        
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def registrar_comprobante_y_stock(self, id_proveedor, tipo_comprobante, nro_comprobante, fecha_emision, observaciones, items_detalle):
        """
        Registra formalmente el comprobante del proveedor (Factura/Remito) con identificador interno,
        asienta el control de compras (precios) y logística (cantidades), y actualiza el stock físico.
        """
        fecha_recepcion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not fecha_emision:
            fecha_emision = datetime.now().strftime("%Y-%m-%d")

        with Database() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO COMPROBANTES_PROVEEDOR 
                (id_proveedor, tipo_comprobante, nro_comprobante, codigo_comercial, fecha_emision, fecha_recepcion, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (id_proveedor, tipo_comprobante, nro_comprobante, nro_comprobante, fecha_emision, fecha_recepcion, observaciones))
            
            id_comprobante = cursor.lastrowid

            for item in items_detalle:
                id_art = item['id_articulo']
                cant_ped = item['cantidad_pedida']
                cant_rec = item['cantidad_recibida']
                prec_pact = item['precio_pactado']
                prec_fact = item['precio_facturado']

                cursor.execute("""
                    INSERT INTO DETALLE_COMPROBANTES_PROVEEDOR
                    (id_comprobante, id_articulo, cantidad_pedida, cantidad_recibida, precio_pactado, precio_facturado)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (id_comprobante, id_art, cant_ped, cant_rec, prec_pact, prec_fact))

                # Actualizar stock físico en depósito
                cursor.execute("""
                    UPDATE ARTICULOS 
                    SET cantidad_stock = ?
                    WHERE id_articulo = ?
                """, (cant_rec, id_art))

            return id_comprobante

    def validar_stock_vs_pedidos(self, id_proveedor=None, id_pedido=None):
        """
        Compara la demanda consolidada contra el stock físico real registrado.
        Si la demanda supera el stock, calcula el prorrateo proporcional equitativo.
        """
        query = """
            SELECT dp.id_pedido, dp.id_articulo, dp.cantidad_pedida, 
                   a.detalle, a.cantidad_stock
            FROM DETALLE_PEDIDOS dp
            JOIN PEDIDOS p ON dp.id_pedido = p.id_pedido
            JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            LEFT JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
            WHERE p.estado = 'Consolidado'
        """
        params = []
        if id_proveedor is not None:
            query += " AND pn.id_proveedor = ?"
            params.append(id_proveedor)
        if id_pedido is not None:
            query += " AND p.id_pedido = ?"
            params.append(id_pedido)

        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
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

    def ejecutar_reparto_masivo(self, id_proveedor=None, id_pedido_sel=None, ajustes=None, nro_comprobante=None):
        """
        Ejecuta el reparto para los pedidos en 'Consolidado', genera registros en REMITOS,
        emite formalmente los REMITOS EN FORMATO PDF (uno por cada proveedor para cada socio),
        y notifica a los socios destinatarios.
        Retorna (True, lista_rutas_pdf) o (False, error).
        """
        fecha_proceso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_emision = datetime.now().strftime("%Y-%m-%d")

        if not nro_comprobante:
            nro_comprobante = generar_codigo_comprobante(id_proveedor or 0)

        remitos_para_pdf = []

        with Database() as conn:
            cursor = conn.cursor()
            
            query_pedidos = """
                SELECT DISTINCT p.id_pedido, p.id_user, p.codigo_comercial, p.fecha,
                                u.nombre AS socio_nombre, u.email AS socio_email,
                                pr.id_proveedor, pr.nombre AS proveedor_nombre
                FROM PEDIDOS p
                JOIN USERS u ON p.id_user = u.id
                JOIN DETALLE_PEDIDOS dp ON p.id_pedido = dp.id_pedido
                JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
                JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
                JOIN PROVEEDORES pr ON pn.id_proveedor = pr.id_proveedor
                WHERE p.estado = 'Consolidado'
            """
            params = []
            if id_proveedor is not None:
                query_pedidos += " AND pr.id_proveedor = ?"
                params.append(id_proveedor)
            if id_pedido_sel is not None:
                query_pedidos += " AND p.id_pedido = ?"
                params.append(id_pedido_sel)

            cursor.execute(query_pedidos, params)
            pedidos_consolidados = [dict(row) for row in cursor.fetchall()]
            
            if not pedidos_consolidados:
                return False, []
            
            # Registrar proceso de reparto
            cursor.execute(
                """
                INSERT INTO PROCESOS_REPARTO (fecha_proceso, archivo_consolidado, estado_reparto)
                VALUES (?, ?, ?)
                """,
                (fecha_proceso, nro_comprobante, 'completado')
            )
            id_proceso = cursor.lastrowid
            
            for pedido in pedidos_consolidados:
                id_pedido = pedido['id_pedido']
                id_user = pedido['id_user']
                prov_id_item = pedido['id_proveedor']
                cod_ped = pedido.get('codigo_comercial') or generar_codigo_pedido(id_pedido, pedido.get('fecha', ''))
                
                query_items = """
                    SELECT DISTINCT dp.id_articulo, dp.cantidad_pedida, a.detalle, a.id_articulo_proveedor
                    FROM DETALLE_PEDIDOS dp
                    JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
                    JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
                    WHERE dp.id_pedido = ? AND pn.id_proveedor = ?
                """
                params_items = [id_pedido, prov_id_item]

                cursor.execute(query_items, params_items)
                items = cursor.fetchall()
                if not items:
                    continue
                
                # Actualizar stock físico entregado
                items_finales_remito = []
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

                    items_finales_remito.append({
                        'id_articulo': id_articulo,
                        'codigo': item['id_articulo_proveedor'],
                        'detalle': item['detalle'],
                        'cantidad': cantidad_final
                    })
                
                # Actualizar estado a 'Procesado'
                cursor.execute(
                    "UPDATE PEDIDOS SET estado = 'Procesado' WHERE id_pedido = ?",
                    (id_pedido,)
                )
                
                # Insertar remito en la base de datos
                cod_remito = generar_codigo_remito(id_pedido, id_user, prov_id_item)
                cursor.execute(
                    """
                    INSERT INTO REMITOS (id_user, id_proceso, id_proveedor, id_pedido, codigo_remito, fecha_emision, detalle_entrega)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (id_user, id_proceso, prov_id_item, id_pedido, cod_remito, fecha_emision, f"Remito {cod_remito} emitido para pedido {cod_ped}")
                )
                id_remito = cursor.lastrowid
                
                for it in items_finales_remito:
                    cursor.execute(
                        """
                        INSERT INTO DETALLE_REMITOS (id_remito, id_articulo, cantidad_entregada)
                        VALUES (?, ?, ?)
                        """,
                        (id_remito, it['id_articulo'], it['cantidad'])
                    )

                remitos_para_pdf.append({
                    'id_remito': id_remito,
                    'codigo_remito': cod_remito,
                    'codigo_pedido': cod_ped,
                    'nro_comprobante': nro_comprobante,
                    'fecha': fecha_emision,
                    'id_user': id_user,
                    'socio_nombre': pedido['socio_nombre'],
                    'socio_email': pedido.get('socio_email', ''),
                    'proveedor_nombre': pedido['proveedor_nombre'],
                    'items': items_finales_remito
                })

        # Generar PDFs y emitir notificaciones
        pdf_service = PdfService.get_instance()
        notif = NotificacionModel()
        rutas_pdf_generados = []

        for r_data in remitos_para_pdf:
            try:
                ruta_pdf = pdf_service.generar_remito_pdf(r_data)
                rutas_pdf_generados.append(ruta_pdf)
                with Database() as conn_up:
                    cursor_up = conn_up.cursor()
                    cursor_up.execute("UPDATE REMITOS SET archivo_pdf = ? WHERE id_remito = ?", (ruta_pdf, r_data['id_remito']))
            except Exception as e:
                print(f"Advertencia al generar PDF para {r_data['codigo_remito']}: {e}")

            try:
                notif.crear_notificacion(
                    mensaje=f"¡Tu Remito {r_data['codigo_remito']} (Pedido {r_data['codigo_pedido']}) de {r_data['proveedor_nombre']} fue generado en formato PDF! La mercadería está lista para su entrega.",
                    tipo="reparto",
                    id_user=r_data['id_user']
                )
            except Exception as e:
                print(f"Advertencia al notificar remito: {e}")

        return True, rutas_pdf_generados

    def obtener_remitos(self, id_user=None, id_proveedor=None, rol='admin'):
        """
        Retorna la lista de remitos oficiales emitidos con su detalle resumido.
        Filtra por socio si rol == 'socio' o si id_user es provisto.
        Filtra por proveedor si id_proveedor es provisto.
        """
        query = """
            SELECT r.id_remito,
                   COALESCE(r.codigo_remito, 'RC-REM-' || r.id_remito) AS codigo_remito,
                   r.fecha_emision,
                   r.id_user,
                   u.nombre AS socio_nombre,
                   u.email AS socio_email,
                   COALESCE(pr.id_proveedor, r.id_proveedor, 0) AS id_proveedor,
                   COALESCE(pr.nombre, 'Proveedor General') AS proveedor_nombre,
                   COALESCE(p.id_pedido, r.id_pedido, 0) AS id_pedido,
                   COALESCE(p.codigo_comercial, 'RC-ORD-' || r.id_pedido) AS codigo_pedido,
                   r.archivo_pdf,
                   r.detalle_entrega,
                   COALESCE(SUM(dr.cantidad_entregada), 0) AS total_unidades,
                   group_concat(a.detalle || ' (' || dr.cantidad_entregada || ' u.)', ', ') AS resumen_articulos
            FROM REMITOS r
            JOIN USERS u ON r.id_user = u.id
            LEFT JOIN PROVEEDORES pr ON r.id_proveedor = pr.id_proveedor
            LEFT JOIN PEDIDOS p ON r.id_pedido = p.id_pedido
            LEFT JOIN DETALLE_REMITOS dr ON r.id_remito = dr.id_remito
            LEFT JOIN ARTICULOS a ON dr.id_articulo = a.id_articulo
            WHERE 1=1
        """
        params = []
        if rol == 'socio' or (id_user is not None and rol not in ['admin', 'ejecutivo']):
            query += " AND r.id_user = ?"
            params.append(id_user)
        elif id_user is not None:
            query += " AND r.id_user = ?"
            params.append(id_user)

        if id_proveedor is not None:
            query += " AND (r.id_proveedor = ? OR pr.id_proveedor = ?)"
            params.append(id_proveedor)
            params.append(id_proveedor)

        query += " GROUP BY r.id_remito ORDER BY r.id_remito DESC;"

        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def obtener_detalle_remito(self, id_remito):
        """Retorna los renglones individuales de mercadería de un remito específico."""
        query = """
            SELECT dr.id_articulo,
                   a.id_articulo_proveedor AS codigo,
                   a.detalle,
                   a.rubro,
                   dr.cantidad_entregada
            FROM DETALLE_REMITOS dr
            JOIN ARTICULOS a ON dr.id_articulo = a.id_articulo
            WHERE dr.id_remito = ?
            ORDER BY a.detalle ASC;
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_remito,))
            return [dict(row) for row in cursor.fetchall()]

    def obtener_socios_con_remitos(self):
        """Devuelve los socios que poseen al menos un remito emitido para poblar filtros."""
        query = """
            SELECT DISTINCT u.id, u.nombre, u.email
            FROM USERS u
            JOIN REMITOS r ON u.id = r.id_user
            ORDER BY u.nombre ASC;
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
