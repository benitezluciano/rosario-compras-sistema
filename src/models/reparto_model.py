from datetime import datetime
from src.database import Database
from src.models.notificacion_model import NotificacionModel
from src.config.empresa import PUNTO_VENTA_REMITOS
from src.utils.id_generator import (
    generar_codigo_pedido, generar_codigo_comprobante, generar_codigo_remito, generar_numero_remito
)
from src.models.remito_model import RemitoModel


class RepartoModel:
    """
    Recepción y reparto por proveedor.
    Cada pedido pertenece a un único proveedor (PEDIDOS.id_proveedor): repartir un
    proveedor solo afecta a sus pedidos y cada pedido genera exactamente un remito.
    NOTA: la lógica de stock (reemplazar vs. sumar al asentar) queda pendiente de
    definición del grupo y se mantiene como estaba.
    """

    def obtener_proveedores_con_pedidos(self):
        """Devuelve los proveedores con pedidos 'Consolidado' pendientes de recepción/reparto."""
        query = """
            SELECT DISTINCT pr.id_proveedor, pr.nombre
            FROM PEDIDOS p
            JOIN PROVEEDORES pr ON pr.id_proveedor = p.id_proveedor
            WHERE p.estado = 'Consolidado'
            ORDER BY pr.nombre ASC;
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def obtener_pedidos_consolidados_por_proveedor(self, id_proveedor):
        """
        Devuelve los pedidos consolidados del proveedor seleccionado.
        Permite seleccionar individualmente un pedido cuando hay 2 o más simultáneos.
        """
        if id_proveedor is None:
            return []
        query = """
            SELECT p.id_pedido, p.codigo_comercial, p.fecha, p.estado,
                   u.nombre AS socio_nombre, u.email AS socio_email,
                   pr.id_proveedor, pr.nombre AS proveedor_nombre,
                   group_concat(a.detalle || ' x' || dp.cantidad_pedida, ', ') AS resumen_articulos
            FROM PEDIDOS p
            JOIN USERS u ON p.id_user = u.id
            JOIN PROVEEDORES pr ON pr.id_proveedor = p.id_proveedor
            JOIN DETALLE_PEDIDOS dp ON p.id_pedido = dp.id_pedido
            JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            WHERE p.estado = 'Consolidado' AND p.id_proveedor = ?
            GROUP BY p.id_pedido
            ORDER BY p.id_pedido DESC;
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_proveedor,))
            filas = []
            for row in cursor.fetchall():
                ped = dict(row)
                if not ped.get('codigo_comercial'):
                    ped['codigo_comercial'] = generar_codigo_pedido(ped['id_pedido'], ped['fecha'])
                filas.append(ped)
            return filas

    def obtener_articulos_control_recepcion(self, id_proveedor, id_pedido=None):
        """
        Devuelve los artículos de los pedidos 'Consolidado' del proveedor con:
        - Cantidad demandada por los socios (Logística)
        - Precio pactado: precio congelado en los pedidos (Compras), promedio ponderado
        - Stock físico actual
        """
        if id_proveedor is None:
            return []
        query = """
            SELECT a.id_articulo,
                   a.id_articulo_proveedor,
                   a.detalle AS articulo_detalle,
                   pr.id_proveedor,
                   pr.nombre AS proveedor_nombre,
                   SUM(dp.cantidad_pedida) AS cantidad_demandada,
                   ROUND(SUM(dp.cantidad_pedida * dp.precio_unitario) * 1.0
                         / MAX(SUM(dp.cantidad_pedida), 1), 2) AS precio_pactado,
                   a.cantidad_stock
            FROM DETALLE_PEDIDOS dp
            JOIN PEDIDOS p ON dp.id_pedido = p.id_pedido
            JOIN PROVEEDORES pr ON pr.id_proveedor = p.id_proveedor
            JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            WHERE p.estado = 'Consolidado' AND p.id_proveedor = ?
        """
        params = [id_proveedor]
        if id_pedido is not None:
            query += " AND p.id_pedido = ?"
            params.append(id_pedido)

        query += " GROUP BY a.id_articulo ORDER BY a.detalle;"

        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def registrar_comprobante_y_stock(self, id_proveedor, tipo_comprobante, nro_comprobante, fecha_emision, observaciones, items_detalle):
        """
        Registra formalmente el comprobante del proveedor (Factura/Remito) con identificador interno,
        asienta el control de compras (precios) y logística (cantidades), y actualiza el stock físico.
        """
        if id_proveedor is None:
            raise ValueError("Debe seleccionarse el proveedor que realizó la entrega.")

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
                cursor.execute("""
                    INSERT INTO DETALLE_COMPROBANTES_PROVEEDOR
                    (id_comprobante, id_articulo, cantidad_pedida, cantidad_recibida, precio_pactado, precio_facturado)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (id_comprobante, item['id_articulo'], item['cantidad_pedida'], item['cantidad_recibida'],
                      item['precio_pactado'], item['precio_facturado']))

                # Actualizar stock físico en depósito
                # (pendiente de definición: reemplazar vs. sumar; se mantiene el comportamiento actual)
                cursor.execute(
                    "UPDATE ARTICULOS SET cantidad_stock = ? WHERE id_articulo = ?",
                    (item['cantidad_recibida'], item['id_articulo'])
                )

            return id_comprobante

    def validar_stock_vs_pedidos(self, id_proveedor, id_pedido=None):
        """
        Compara la demanda consolidada del proveedor contra el stock físico registrado.
        Si la demanda supera el stock, calcula el prorrateo proporcional equitativo
        (método de restos mayores).
        """
        if id_proveedor is None:
            return []
        query = """
            SELECT dp.id_pedido, dp.id_articulo, dp.cantidad_pedida,
                   a.detalle, a.cantidad_stock
            FROM DETALLE_PEDIDOS dp
            JOIN PEDIDOS p ON dp.id_pedido = p.id_pedido
            JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            WHERE p.estado = 'Consolidado' AND p.id_proveedor = ?
        """
        params = [id_proveedor]
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
            info = por_articulo.setdefault(fila['id_articulo'], {
                'detalle': fila['detalle'],
                'cantidad_stock': fila['cantidad_stock'],
                'pedidos': []
            })
            info['pedidos'].append((fila['id_pedido'], fila['cantidad_pedida']))

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
                        ajustes[id_ped] = asignado
                        suma_asignada += asignado
                        pre_asignados.append({'id_pedido': id_ped, 'fraccion': share - asignado})

                    remanente = stock_disponible - suma_asignada
                    if remanente > 0:
                        pre_asignados.sort(key=lambda x: x['fraccion'], reverse=True)
                        for i in range(int(remanente)):
                            ajustes[pre_asignados[i % len(pre_asignados)]['id_pedido']] += 1

                discrepancias.append({
                    'id_articulo': id_art,
                    'detalle': info['detalle'],
                    'solicitado': total_pedido,
                    'disponible': stock_disponible,
                    'ajustes': ajustes
                })

        return discrepancias

    def ejecutar_reparto_masivo(self, id_proveedor, id_pedido_sel=None, ajustes=None, nro_comprobante=None):
        """
        Ejecuta el reparto de los pedidos 'Consolidado' de UN proveedor (o de un pedido puntual):
        - Genera un REMITO por pedido (vinculado a pedido y proveedor, con código único).
        - Emite el remito en formato PDF y notifica al socio.
        - El pedido pasa a 'Procesado'.
        Retorna (True, lista_rutas_pdf) o (False, []).
        """
        if id_proveedor is None:
            raise ValueError("Debe seleccionarse el proveedor a repartir.")

        fecha_proceso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fecha_emision = datetime.now().strftime("%Y-%m-%d")

        if not nro_comprobante:
            nro_comprobante = generar_codigo_comprobante(id_proveedor)

        remitos_para_pdf = []

        with Database() as conn:
            cursor = conn.cursor()

            query_pedidos = """
                SELECT p.id_pedido, p.id_user, p.codigo_comercial, p.fecha,
                       u.nombre AS socio_nombre, u.email AS socio_email,
                       pr.id_proveedor, pr.nombre AS proveedor_nombre
                FROM PEDIDOS p
                JOIN USERS u ON p.id_user = u.id
                JOIN PROVEEDORES pr ON pr.id_proveedor = p.id_proveedor
                WHERE p.estado = 'Consolidado' AND p.id_proveedor = ?
            """
            params = [id_proveedor]
            if id_pedido_sel is not None:
                query_pedidos += " AND p.id_pedido = ?"
                params.append(id_pedido_sel)

            cursor.execute(query_pedidos, params)
            pedidos_consolidados = [dict(row) for row in cursor.fetchall()]

            if not pedidos_consolidados:
                return False, []

            cursor.execute("""
                INSERT INTO PROCESOS_REPARTO (fecha_proceso, archivo_consolidado, estado_reparto)
                VALUES (?, ?, ?)
            """, (fecha_proceso, nro_comprobante, 'completado'))
            id_proceso = cursor.lastrowid

            for pedido in pedidos_consolidados:
                id_pedido = pedido['id_pedido']
                id_user = pedido['id_user']
                cod_ped = pedido.get('codigo_comercial') or generar_codigo_pedido(id_pedido, pedido.get('fecha', ''))

                # Todos los renglones del pedido pertenecen a este proveedor
                cursor.execute("""
                    SELECT dp.id_articulo, dp.cantidad_pedida, a.detalle, a.id_articulo_proveedor
                    FROM DETALLE_PEDIDOS dp
                    JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
                    WHERE dp.id_pedido = ?
                """, (id_pedido,))
                items = cursor.fetchall()
                if not items:
                    continue

                items_finales_remito = []
                for item in items:
                    id_articulo = item['id_articulo']
                    cantidad_final = item['cantidad_pedida']
                    if ajustes and (id_pedido, id_articulo) in ajustes:
                        cantidad_final = ajustes[(id_pedido, id_articulo)]

                    # Descontar stock físico entregado
                    cursor.execute("""
                        UPDATE ARTICULOS
                        SET cantidad_stock = MAX(0, cantidad_stock - ?)
                        WHERE id_articulo = ?
                    """, (cantidad_final, id_articulo))

                    items_finales_remito.append({
                        'id_articulo': id_articulo,
                        'codigo': item['id_articulo_proveedor'],
                        'detalle': item['detalle'],
                        'cantidad': cantidad_final
                    })

                cursor.execute("UPDATE PEDIDOS SET estado = 'Procesado' WHERE id_pedido = ?", (id_pedido,))

                # Remito vinculado al pedido y proveedor; el código se deriva del id_remito (único)
                cursor.execute("""
                    INSERT INTO REMITOS (id_user, id_proceso, id_pedido, id_proveedor, fecha_emision, detalle_entrega)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (id_user, id_proceso, id_pedido, id_proveedor, fecha_emision, None))
                id_remito = cursor.lastrowid
                cod_remito = generar_codigo_remito(id_remito, id_user)
                numero_remito = generar_numero_remito(id_remito, PUNTO_VENTA_REMITOS)
                cursor.execute(
                    "UPDATE REMITOS SET codigo_comercial = ?, numero_remito = ?, detalle_entrega = ? WHERE id_remito = ?",
                    (cod_remito, numero_remito,
                     f"Remito {numero_remito} (ref. {cod_remito}) emitido para pedido {cod_ped}", id_remito)
                )

                for it in items_finales_remito:
                    cursor.execute("""
                        INSERT INTO DETALLE_REMITOS (id_remito, id_articulo, cantidad_entregada)
                        VALUES (?, ?, ?)
                    """, (id_remito, it['id_articulo'], it['cantidad']))

                remitos_para_pdf.append({
                    'id_remito': id_remito,
                    'codigo_remito': cod_remito,
                    'numero_remito': numero_remito,
                    'codigo_pedido': cod_ped,
                    'id_user': id_user,
                    'proveedor_nombre': pedido['proveedor_nombre'],
                })

        # Generar PDFs (desde la base, igual que al regenerarlos) y emitir notificaciones
        remito_model = RemitoModel()
        notif = NotificacionModel()
        rutas_pdf_generados = []

        for r_data in remitos_para_pdf:
            try:
                rutas_pdf_generados.append(remito_model.generar_pdf(r_data['id_remito']))
            except Exception as e:
                print(f"Advertencia al generar PDF para {r_data['numero_remito']}: {e}")

            try:
                notif.crear_notificacion(
                    mensaje=(
                        f"¡Tu Remito {r_data['numero_remito']} (Pedido {r_data['codigo_pedido']}) de "
                        f"{r_data['proveedor_nombre']} fue emitido! La mercadería está lista para su entrega."
                    ),
                    tipo="reparto",
                    id_user=r_data['id_user']
                )
            except Exception as e:
                print(f"Advertencia al notificar remito: {e}")

        return True, rutas_pdf_generados
