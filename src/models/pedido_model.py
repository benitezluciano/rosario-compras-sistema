from datetime import datetime
from src.database import Database
from src.models.notificacion_model import NotificacionModel

class PedidoModel:
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
        Consulta el catálogo de artículos con sus precios negociados actuales.
        Permite filtrar opcionalmente por proveedor.
        """
        query = """
            SELECT a.id_articulo, a.id_articulo_proveedor, a.detalle, a.rubro, a.cantidad_stock,
                   pn.precio_final, pn.descuento, p.nombre AS proveedor_nombre, p.id_proveedor
            FROM ARTICULOS a
            JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
            JOIN PROVEEDORES p ON pn.id_proveedor = p.id_proveedor
        """
        params = []
        if id_proveedor is not None:
            query += " WHERE p.id_proveedor = ?"
            params.append(id_proveedor)
            
        query += " ORDER BY p.nombre, a.detalle"
            
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
            
            # Obtener nombre del socio para la notificación
            cursor.execute("SELECT nombre FROM USERS WHERE id = ?", (id_socio,))
            user_row = cursor.fetchone()
            nombre_socio = user_row['nombre'] if user_row else f"Socio #{id_socio}"
            
            # 1. Insertar cabecera de PEDIDOS
            cursor.execute(
                "INSERT INTO PEDIDOS (id_user, fecha, estado) VALUES (?, ?, ?)",
                (id_socio, fecha_actual, "Pendiente")
            )
            id_pedido = cursor.lastrowid
            
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
                mensaje=f"El socio {nombre_socio} registró el Pedido #{id_pedido} ({len(articulos_pedido)} productos).",
                tipo="nuevo_pedido",
                id_user=None # Para ejecutivos y admin
            )
        except Exception as e:
            print(f"Advertencia al emitir notificación: {e}")
                
        return id_pedido
