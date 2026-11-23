from src.database import Database
from src.models.remito_model import RemitoModel


class HistorialEjecutivoModel:
    """
    Consultas del historial del ejecutivo: órdenes de compra, remitos emitidos
    y comprobantes recibidos de los proveedores. Todos los ejecutivos ven todo.
    """

    # Filtros de estado de la pestaña Órdenes de Compra
    ESTADO_PENDIENTE_ENTREGA = "pendiente_entrega"
    ESTADO_REPARTIDA = "repartida"
    ESTADO_SIN_ENVIAR = "sin_enviar"

    # Filtros de control de la pestaña Comprobantes
    CONTROL_CON_DIFERENCIAS = "con_diferencias"
    CONTROL_SIN_DIFERENCIAS = "sin_diferencias"

    def obtener_proveedores(self):
        with Database() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT id_proveedor, nombre FROM PROVEEDORES ORDER BY nombre"
            ).fetchall()]

    def obtener_socios(self):
        with Database() as conn:
            return [dict(r) for r in conn.execute(
                "SELECT id, nombre FROM USERS WHERE role = 'socio' ORDER BY nombre"
            ).fetchall()]

    # ------------------------------------------------------------------
    # Órdenes de compra
    # ------------------------------------------------------------------

    def obtener_ordenes(self, id_proveedor=None, estado=None):
        """
        Órdenes de compra (más recientes primero) con su estado de entrega y de envío:
        - pendientes_entrega: pedidos de la orden todavía 'Consolidado' (sin repartir).
        - enviada: 1 si se envió por correo al proveedor.
        """
        query = """
            SELECT o.id_orden_compra, o.codigo_comercial, o.fecha, o.cantidad_pedidos, o.total,
                   o.fecha_envio_email, o.email_destino,
                   pr.id_proveedor, pr.nombre AS proveedor_nombre,
                   u.nombre AS ejecutivo_nombre,
                   SUM(CASE WHEN p.estado = 'Consolidado' THEN 1 ELSE 0 END) AS pendientes_entrega
            FROM ORDENES_COMPRA o
            JOIN PROVEEDORES pr ON pr.id_proveedor = o.id_proveedor
            LEFT JOIN USERS u ON u.id = o.id_user
            LEFT JOIN PEDIDOS p ON p.id_orden_compra = o.id_orden_compra
            WHERE 1 = 1
        """
        params = []
        if id_proveedor:
            query += " AND o.id_proveedor = ?"
            params.append(id_proveedor)
        if estado == self.ESTADO_SIN_ENVIAR:
            query += " AND o.fecha_envio_email IS NULL"
        query += " GROUP BY o.id_orden_compra"
        if estado == self.ESTADO_PENDIENTE_ENTREGA:
            query += " HAVING pendientes_entrega > 0"
        elif estado == self.ESTADO_REPARTIDA:
            query += " HAVING pendientes_entrega = 0"
        query += " ORDER BY o.fecha DESC, o.id_orden_compra DESC"

        with Database() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def obtener_pedidos_de_orden(self, id_orden):
        """Pedidos que componen una orden: socio, estado, unidades, total (precio congelado) y remito."""
        query = """
            SELECT p.id_pedido, p.codigo_comercial, p.fecha, p.estado,
                   u.nombre AS socio_nombre,
                   COALESCE(SUM(dp.cantidad_pedida), 0) AS unidades,
                   COALESCE(SUM(dp.cantidad_pedida * dp.precio_unitario), 0) AS total,
                   (SELECT COALESCE(r.numero_remito, r.codigo_comercial) FROM REMITOS r WHERE r.id_pedido = p.id_pedido
                    ORDER BY r.id_remito DESC LIMIT 1) AS remito_codigo
            FROM PEDIDOS p
            JOIN USERS u ON u.id = p.id_user
            LEFT JOIN DETALLE_PEDIDOS dp ON dp.id_pedido = p.id_pedido
            WHERE p.id_orden_compra = ?
            GROUP BY p.id_pedido
            ORDER BY u.nombre
        """
        with Database() as conn:
            return [dict(r) for r in conn.execute(query, (id_orden,)).fetchall()]

    # ------------------------------------------------------------------
    # Remitos emitidos
    # ------------------------------------------------------------------

    def obtener_remitos(self, id_proveedor=None, id_socio=None):
        """Remitos emitidos (más recientes primero), con la ruta del PDF si el archivo existe."""
        query = """
            SELECT r.id_remito, r.codigo_comercial, r.numero_remito, r.fecha_emision,
                   u.nombre AS socio_nombre, pr.nombre AS proveedor_nombre,
                   p.codigo_comercial AS pedido_codigo, o.codigo_comercial AS orden_codigo,
                   pc.archivo_consolidado AS comprobante,
                   COALESCE((SELECT SUM(dr.cantidad_entregada) FROM DETALLE_REMITOS dr
                             WHERE dr.id_remito = r.id_remito), 0) AS unidades
            FROM REMITOS r
            JOIN USERS u ON u.id = r.id_user
            LEFT JOIN PROVEEDORES pr ON pr.id_proveedor = r.id_proveedor
            LEFT JOIN PEDIDOS p ON p.id_pedido = r.id_pedido
            LEFT JOIN ORDENES_COMPRA o ON o.id_orden_compra = p.id_orden_compra
            LEFT JOIN PROCESOS_REPARTO pc ON pc.id_proceso = r.id_proceso
            WHERE 1 = 1
        """
        params = []
        if id_proveedor:
            query += " AND r.id_proveedor = ?"
            params.append(id_proveedor)
        if id_socio:
            query += " AND r.id_user = ?"
            params.append(id_socio)
        query += " ORDER BY r.fecha_emision DESC, r.id_remito DESC"

        with Database() as conn:
            remitos = [dict(r) for r in conn.execute(query, params).fetchall()]
        remito_model = RemitoModel()
        for rem in remitos:
            rem['ruta_pdf'] = remito_model.ruta_pdf_existente(rem['codigo_comercial'])
        return remitos

    def asegurar_pdf_remito(self, id_remito):
        """Ruta del PDF del remito; si no existe, lo regenera desde la base con el formato actual."""
        return RemitoModel().asegurar_pdf(id_remito)

    # ------------------------------------------------------------------
    # Comprobantes de proveedores
    # ------------------------------------------------------------------

    def obtener_comprobantes(self, id_proveedor=None, control=None):
        """
        Comprobantes recibidos (más recientes primero) con el resultado del doble control:
        - faltantes: unidades pedidas no recibidas (suma de diferencias positivas).
        - excedentes: unidades recibidas de más.
        - articulos_dif_precio: renglones con precio facturado distinto del pactado.
        """
        query = """
            SELECT c.id_comprobante, c.tipo_comprobante, c.nro_comprobante, c.fecha_emision,
                   c.fecha_recepcion, c.observaciones, pr.nombre AS proveedor_nombre,
                   COUNT(d.id_articulo) AS articulos,
                   COALESCE(SUM(CASE WHEN d.cantidad_pedida > d.cantidad_recibida
                                     THEN d.cantidad_pedida - d.cantidad_recibida ELSE 0 END), 0) AS faltantes,
                   COALESCE(SUM(CASE WHEN d.cantidad_recibida > d.cantidad_pedida
                                     THEN d.cantidad_recibida - d.cantidad_pedida ELSE 0 END), 0) AS excedentes,
                   COALESCE(SUM(CASE WHEN ABS(d.precio_facturado - d.precio_pactado) > 0.009
                                     THEN 1 ELSE 0 END), 0) AS articulos_dif_precio,
                   COALESCE(SUM(d.cantidad_recibida * d.precio_facturado), 0) AS total_facturado
            FROM COMPROBANTES_PROVEEDOR c
            JOIN PROVEEDORES pr ON pr.id_proveedor = c.id_proveedor
            LEFT JOIN DETALLE_COMPROBANTES_PROVEEDOR d ON d.id_comprobante = c.id_comprobante
            WHERE 1 = 1
        """
        params = []
        if id_proveedor:
            query += " AND c.id_proveedor = ?"
            params.append(id_proveedor)
        query += " GROUP BY c.id_comprobante"
        if control == self.CONTROL_CON_DIFERENCIAS:
            query += " HAVING faltantes > 0 OR excedentes > 0 OR articulos_dif_precio > 0"
        elif control == self.CONTROL_SIN_DIFERENCIAS:
            query += " HAVING faltantes = 0 AND excedentes = 0 AND articulos_dif_precio = 0"
        query += " ORDER BY c.fecha_recepcion DESC, c.id_comprobante DESC"

        with Database() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def obtener_detalle_comprobante(self, id_comprobante):
        """Renglones del comprobante con las diferencias de cantidad y precio."""
        query = """
            SELECT a.id_articulo_proveedor AS codigo, a.detalle,
                   d.cantidad_pedida, d.cantidad_recibida,
                   d.cantidad_recibida - d.cantidad_pedida AS diferencia,
                   d.precio_pactado, d.precio_facturado
            FROM DETALLE_COMPROBANTES_PROVEEDOR d
            JOIN ARTICULOS a ON a.id_articulo = d.id_articulo
            WHERE d.id_comprobante = ?
            ORDER BY a.detalle
        """
        with Database() as conn:
            return [dict(r) for r in conn.execute(query, (id_comprobante,)).fetchall()]
