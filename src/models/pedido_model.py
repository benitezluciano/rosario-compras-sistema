from datetime import datetime
from src.database import Database
from src.models.notificacion_model import NotificacionModel
from src.utils.id_generator import generar_codigo_pedido

class PedidoModel:
    def obtener_socios(self):
        """Devuelve los usuarios con rol socio para el selector."""
        query = "SELECT id, nombre, email FROM USERS WHERE role = 'socio' ORDER BY nombre ASC"
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def obtener_proveedores(self):
        """Devuelve los proveedores registrados que tienen artículos cotizados."""
        query = """
            SELECT DISTINCT p.id_proveedor, p.nombre
            FROM PROVEEDORES p
            JOIN PRECIOS_NEGOCIADOS pn ON p.id_proveedor = pn.id_proveedor
            ORDER BY p.nombre ASC
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def obtener_catalogo_articulos(self, id_proveedor=None):
        """
        Consulta el catálogo de artículos agrupados con sus precios negociados actuales.
        """
        query = """
            SELECT a.id_articulo, a.id_articulo_proveedor, a.detalle, a.rubro, a.cantidad_stock,
                   COALESCE(pn.precio_base, pn.precio_final, 0.0) AS precio_base,
                   COALESCE(pn.precio_final, 0.0) AS precio_final, 
                   COALESCE(pn.descuento, 0.0) AS descuento, 
                   p.nombre AS proveedor_nombre, p.id_proveedor
            FROM ARTICULOS a
            JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
            JOIN PROVEEDORES p ON pn.id_proveedor = p.id_proveedor
        """
        params = []
        if id_proveedor is not None:
            query += " WHERE p.id_proveedor = ?"
            params.append(id_proveedor)
            
        query += " ORDER BY p.nombre ASC, a.detalle ASC"
            
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def registrar_pedido(self, id_socio, articulos_pedido):
        """
        Inserta un nuevo pedido en la base de datos con estado 'Pendiente', 
        guarda sus detalles y genera una notificación para el ejecutivo.
        """
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        
        with Database() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT nombre FROM USERS WHERE id = ?", (id_socio,))
            user_row = cursor.fetchone()
            nombre_socio = user_row['nombre'] if user_row else f"Socio #{id_socio}"
            
            # 1. Insertar cabecera de PEDIDOS
            cursor.execute(
                "INSERT INTO PEDIDOS (id_user, fecha, estado) VALUES (?, ?, ?)",
                (id_socio, fecha_actual, "Pendiente")
            )
            id_pedido = cursor.lastrowid
            codigo_comercial = generar_codigo_pedido(id_pedido, fecha_actual)
            
            cursor.execute(
                "UPDATE PEDIDOS SET codigo_comercial = ? WHERE id_pedido = ?",
                (codigo_comercial, id_pedido)
            )
            
            # 2. Insertar renglones en DETALLE_PEDIDOS
            for id_articulo, cantidad in articulos_pedido:
                cursor.execute(
                    "INSERT INTO DETALLE_PEDIDOS (id_pedido, id_articulo, cantidad_pedida) VALUES (?, ?, ?)",
                    (id_pedido, id_articulo, cantidad)
                )
                
        # 3. Disparar notificación automática al Ejecutivo
        try:
            notif = NotificacionModel()
            notif.crear_notificacion(
                mensaje=f"El socio {nombre_socio} registró el Pedido {codigo_comercial} ({len(articulos_pedido)} productos).",
                tipo="nuevo_pedido",
                id_user=None
            )
        except Exception as e:
            print(f"Advertencia al emitir notificación: {e}")
                
        return id_pedido

    def obtener_pedido_vigente(self, id_socio):
        """
        Retorna el pedido actualmente en curso y sin cerrar (estado 'Pendiente') del socio,
        junto con un mapa de {id_articulo: cantidad_pedida}.
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id_pedido, codigo_comercial, fecha, estado 
                FROM PEDIDOS 
                WHERE id_user = ? AND estado = 'Pendiente'
                ORDER BY id_pedido DESC LIMIT 1
            """, (id_socio,))
            pedido_row = cursor.fetchone()
            if not pedido_row:
                return None

            pedido = dict(pedido_row)
            if not pedido.get('codigo_comercial'):
                pedido['codigo_comercial'] = generar_codigo_pedido(pedido['id_pedido'], pedido['fecha'])

            cursor.execute("""
                SELECT id_articulo, cantidad_pedida 
                FROM DETALLE_PEDIDOS 
                WHERE id_pedido = ?
            """, (pedido['id_pedido'],))
            
            items = {}
            for row in cursor.fetchall():
                items[row['id_articulo']] = row['cantidad_pedida']

            pedido['items'] = items
            return pedido

    def actualizar_pedido_vigente(self, id_pedido, articulos_pedido):
        """
        Permite al socio actualizar las cantidades y artículos de su pedido vigente pendiente.
        """
        with Database() as conn:
            cursor = conn.cursor()
            # Limpiar renglones anteriores
            cursor.execute("DELETE FROM DETALLE_PEDIDOS WHERE id_pedido = ?", (id_pedido,))
            
            # Insertar los nuevos artículos seleccionados
            for id_articulo, cantidad in articulos_pedido:
                if cantidad > 0:
                    cursor.execute("""
                        INSERT INTO DETALLE_PEDIDOS (id_pedido, id_articulo, cantidad_pedida)
                        VALUES (?, ?, ?)
                    """, (id_pedido, id_articulo, cantidad))
        return True

    def obtener_historial_pedidos(self, id_socio):
        """
        Consulta todos los pedidos registrados por el socio, con sus estados,
        totales calculados e identificadores comerciales protegidos.
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id_pedido, p.codigo_comercial, p.fecha, p.estado,
                       COUNT(dp.id_articulo) AS cantidad_articulos,
                       COALESCE(SUM(dp.cantidad_pedida), 0) AS total_unidades,
                       COALESCE(SUM(dp.cantidad_pedida * pn.precio_final), 0.0) AS total_estimado,
                       group_concat(a.detalle || ' (' || dp.cantidad_pedida || 'u)', ', ') AS resumen_productos
                FROM PEDIDOS p
                LEFT JOIN DETALLE_PEDIDOS dp ON p.id_pedido = dp.id_pedido
                LEFT JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
                LEFT JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
                WHERE p.id_user = ?
                GROUP BY p.id_pedido
                ORDER BY p.id_pedido DESC
            """, (id_socio,))
            
            pedidos = []
            for row in cursor.fetchall():
                ped = dict(row)
                if not ped.get('codigo_comercial'):
                    ped['codigo_comercial'] = generar_codigo_pedido(ped['id_pedido'], ped['fecha'])
                pedidos.append(ped)
            return pedidos

