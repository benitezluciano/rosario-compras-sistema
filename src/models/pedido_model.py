from datetime import datetime
from src.database import Database

class PedidoModel:
    def obtener_catalogo_articulos(self, id_proveedor=None):
        """
        Consulta la base de datos para obtener el catálogo de artículos 
        junto con sus precios negociados actuales.
        Opcionalmente filtra por un proveedor específico.
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
            
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def registrar_pedido(self, id_socio, articulos_pedido):
        """
        Inserta un nuevo pedido en la base de datos con estado 'Pendiente' y 
        guarda sus respectivos renglones/detalles de artículos y cantidades.
        
        articulos_pedido: Lista de tuplas/diccionarios con (id_articulo, cantidad_pedida)
        Retorna el ID del pedido registrado.
        """
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        
        with Database() as conn:
            cursor = conn.cursor()
            
            # 1. Insertar en la cabecera de la tabla PEDIDOS
            cursor.execute(
                "INSERT INTO PEDIDOS (id_user, fecha, estado) VALUES (?, ?, ?)",
                (id_socio, fecha_actual, "Pendiente")
            )
            id_pedido = cursor.lastrowid
            
            # 2. Insertar los detalles correspondientes en DETALLE_PEDIDOS
            for id_articulo, cantidad in articulos_pedido:
                cursor.execute(
                    "INSERT INTO DETALLE_PEDIDOS (id_pedido, id_articulo, cantidad_pedida) VALUES (?, ?, ?)",
                    (id_pedido, id_articulo, cantidad)
                )
                
            return id_pedido
