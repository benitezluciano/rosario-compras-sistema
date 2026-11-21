from datetime import datetime
from src.database import Database
from src.models.notificacion_model import NotificacionModel
from src.utils.id_generator import generar_codigo_pedido


class PedidoModel:
    """
    Pedidos de los socios.
    Regla de negocio: cada pedido corresponde a UN proveedor (su lista de precios).
    Un socio puede tener como máximo un pedido 'Pendiente' por proveedor, que puede
    editar mientras no se consolide. "Enviar todo" es una comodidad: genera/actualiza
    un pedido independiente por cada proveedor con cantidades.
    """

    def obtener_socios(self):
        """Devuelve los usuarios con rol socio para el selector."""
        query = "SELECT id, nombre, email FROM USERS WHERE role = 'socio' ORDER BY nombre ASC"
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def obtener_proveedores(self):
        """Devuelve los proveedores con lista de precios HABILITADA para pedidos."""
        query = """
            SELECT DISTINCT p.id_proveedor, p.nombre, p.fecha_habilitacion
            FROM PROVEEDORES p
            JOIN PRECIOS_NEGOCIADOS pn ON p.id_proveedor = pn.id_proveedor
            WHERE p.lista_habilitada = 1
            ORDER BY p.nombre ASC
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def obtener_catalogo_articulos(self, id_proveedor=None, solo_habilitadas=True):
        """
        Consulta los artículos con sus precios negociados.
        Por defecto solo incluye las listas habilitadas (lo que el socio puede pedir).
        """
        query = """
            SELECT a.id_articulo, a.id_articulo_proveedor, a.detalle, a.rubro, a.cantidad_stock,
                   COALESCE(NULLIF(pn.precio_base, 0), pn.precio_final, 0.0) AS precio_base,
                   COALESCE(pn.precio_final, 0.0) AS precio_final,
                   COALESCE(pn.descuento, 0.0) AS descuento,
                   p.nombre AS proveedor_nombre, p.id_proveedor
            FROM ARTICULOS a
            JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
            JOIN PROVEEDORES p ON pn.id_proveedor = p.id_proveedor
            WHERE 1 = 1
        """
        params = []
        if solo_habilitadas:
            query += " AND p.lista_habilitada = 1"
        if id_proveedor is not None:
            query += " AND p.id_proveedor = ?"
            params.append(id_proveedor)

        query += " ORDER BY p.nombre ASC, a.detalle ASC"

        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Pedidos vigentes (estado 'Pendiente'), uno por proveedor
    # ------------------------------------------------------------------

    def obtener_pedido_vigente(self, id_socio, id_proveedor):
        """
        Retorna el pedido 'Pendiente' del socio para un proveedor, junto con
        un mapa {id_articulo: cantidad_pedida}. None si no existe.
        """
        vigentes = self.obtener_pedidos_vigentes(id_socio)
        return vigentes.get(id_proveedor)

    def obtener_pedidos_vigentes(self, id_socio):
        """
        Retorna los pedidos 'Pendiente' del socio agrupados por proveedor:
        {id_proveedor: {id_pedido, codigo_comercial, fecha, estado, proveedor_nombre, items: {id_articulo: cantidad}}}
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id_pedido, p.id_proveedor, p.codigo_comercial, p.fecha, p.estado,
                       pr.nombre AS proveedor_nombre
                FROM PEDIDOS p
                JOIN PROVEEDORES pr ON pr.id_proveedor = p.id_proveedor
                WHERE p.id_user = ? AND p.estado = 'Pendiente'
                ORDER BY p.id_pedido DESC
            """, (id_socio,))
            pedidos = {}
            for row in cursor.fetchall():
                ped = dict(row)
                if ped['id_proveedor'] in pedidos:
                    continue  # Ante datos inconsistentes, prevalece el más reciente
                if not ped.get('codigo_comercial'):
                    ped['codigo_comercial'] = generar_codigo_pedido(ped['id_pedido'], ped['fecha'])
                ped['items'] = {}
                pedidos[ped['id_proveedor']] = ped

            for ped in pedidos.values():
                cursor.execute(
                    "SELECT id_articulo, cantidad_pedida FROM DETALLE_PEDIDOS WHERE id_pedido = ?",
                    (ped['id_pedido'],)
                )
                ped['items'] = {r['id_articulo']: r['cantidad_pedida'] for r in cursor.fetchall()}
            return pedidos

    def guardar_pedido_proveedor(self, id_socio, id_proveedor, articulos_pedido):
        """
        Crea o actualiza el pedido vigente del socio para UN proveedor.
        articulos_pedido: lista de (id_articulo, cantidad) con cantidad > 0.
        Retorna dict {id_pedido, codigo_comercial, proveedor_nombre, es_nuevo, cantidad_productos}.
        """
        resultados = self.guardar_pedidos(id_socio, {id_proveedor: articulos_pedido})
        return resultados[0]

    def guardar_pedidos(self, id_socio, pedidos_por_proveedor):
        """
        Crea o actualiza, en una sola transacción, un pedido por cada proveedor.
        pedidos_por_proveedor: {id_proveedor: [(id_articulo, cantidad), ...]}
        - Valida que la lista del proveedor esté habilitada y que cada artículo pertenezca a ella.
        - Congela el precio negociado vigente en DETALLE_PEDIDOS.precio_unitario.
        - Notifica al ejecutivo por cada pedido nuevo.
        Lanza ValueError ante datos inválidos (no se guarda nada).
        Retorna lista de dicts {id_pedido, codigo_comercial, proveedor_nombre, es_nuevo, cantidad_productos}.
        """
        if not pedidos_por_proveedor:
            raise ValueError("No hay productos para registrar en el pedido.")

        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        resultados = []
        nombre_socio = f"Socio #{id_socio}"

        with Database() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT nombre FROM USERS WHERE id = ?", (id_socio,))
            user_row = cursor.fetchone()
            if user_row:
                nombre_socio = user_row['nombre']

            for id_proveedor, articulos in pedidos_por_proveedor.items():
                articulos = [(int(a), int(c)) for a, c in articulos if int(c) > 0]

                cursor.execute(
                    "SELECT nombre, lista_habilitada FROM PROVEEDORES WHERE id_proveedor = ?",
                    (id_proveedor,)
                )
                prov_row = cursor.fetchone()
                if not prov_row:
                    raise ValueError(f"El proveedor #{id_proveedor} no existe.")
                nombre_prov = prov_row['nombre']
                if not prov_row['lista_habilitada']:
                    raise ValueError(
                        f"La lista de '{nombre_prov}' no está habilitada: no se pueden cargar pedidos sobre ella."
                    )
                if not articulos:
                    raise ValueError(f"El pedido para '{nombre_prov}' no tiene productos con cantidad.")

                # Precios vigentes de la lista del proveedor
                cursor.execute(
                    "SELECT id_articulo, precio_final FROM PRECIOS_NEGOCIADOS WHERE id_proveedor = ?",
                    (id_proveedor,)
                )
                precios = {r['id_articulo']: r['precio_final'] for r in cursor.fetchall()}
                ajenos = [a for a, _ in articulos if a not in precios]
                if ajenos:
                    raise ValueError(
                        f"Hay artículos que no pertenecen a la lista de '{nombre_prov}' (IDs: {ajenos})."
                    )

                # ¿Existe pedido vigente para este proveedor?
                cursor.execute("""
                    SELECT id_pedido, codigo_comercial, fecha FROM PEDIDOS
                    WHERE id_user = ? AND id_proveedor = ? AND estado = 'Pendiente'
                    ORDER BY id_pedido DESC LIMIT 1
                """, (id_socio, id_proveedor))
                vigente = cursor.fetchone()

                if vigente:
                    id_pedido = vigente['id_pedido']
                    codigo = vigente['codigo_comercial'] or generar_codigo_pedido(id_pedido, vigente['fecha'])
                    es_nuevo = False
                    cursor.execute("DELETE FROM DETALLE_PEDIDOS WHERE id_pedido = ?", (id_pedido,))
                else:
                    cursor.execute(
                        "INSERT INTO PEDIDOS (id_user, id_proveedor, fecha, estado) VALUES (?, ?, ?, 'Pendiente')",
                        (id_socio, id_proveedor, fecha_actual)
                    )
                    id_pedido = cursor.lastrowid
                    codigo = generar_codigo_pedido(id_pedido, fecha_actual)
                    es_nuevo = True

                cursor.execute(
                    "UPDATE PEDIDOS SET codigo_comercial = ? WHERE id_pedido = ?", (codigo, id_pedido)
                )

                for id_articulo, cantidad in articulos:
                    cursor.execute("""
                        INSERT INTO DETALLE_PEDIDOS (id_pedido, id_articulo, cantidad_pedida, precio_unitario)
                        VALUES (?, ?, ?, ?)
                    """, (id_pedido, id_articulo, cantidad, precios[id_articulo]))

                resultados.append({
                    'id_pedido': id_pedido,
                    'id_proveedor': id_proveedor,
                    'codigo_comercial': codigo,
                    'proveedor_nombre': nombre_prov,
                    'es_nuevo': es_nuevo,
                    'cantidad_productos': len(articulos),
                })

        # Notificación automática al Ejecutivo por cada pedido nuevo
        try:
            notif = NotificacionModel()
            for r in resultados:
                if r['es_nuevo']:
                    notif.crear_notificacion(
                        mensaje=(
                            f"El socio {nombre_socio} registró el Pedido {r['codigo_comercial']} "
                            f"para '{r['proveedor_nombre']}' ({r['cantidad_productos']} productos)."
                        ),
                        tipo="nuevo_pedido",
                        id_user=None
                    )
        except Exception as e:
            print(f"Advertencia al emitir notificación: {e}")

        return resultados

    def anular_pedido_vigente(self, id_socio, id_proveedor):
        """
        Anula (elimina) el pedido 'Pendiente' del socio para un proveedor.
        Solo es posible mientras el pedido no fue consolidado.
        Retorna el código del pedido anulado, o None si no había pedido vigente.
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id_pedido, p.codigo_comercial, p.fecha, pr.nombre AS proveedor_nombre, u.nombre AS socio_nombre
                FROM PEDIDOS p
                JOIN PROVEEDORES pr ON pr.id_proveedor = p.id_proveedor
                JOIN USERS u ON u.id = p.id_user
                WHERE p.id_user = ? AND p.id_proveedor = ? AND p.estado = 'Pendiente'
                ORDER BY p.id_pedido DESC LIMIT 1
            """, (id_socio, id_proveedor))
            ped = cursor.fetchone()
            if not ped:
                return None
            codigo = ped['codigo_comercial'] or generar_codigo_pedido(ped['id_pedido'], ped['fecha'])
            cursor.execute("DELETE FROM DETALLE_PEDIDOS WHERE id_pedido = ?", (ped['id_pedido'],))
            cursor.execute("DELETE FROM PEDIDOS WHERE id_pedido = ?", (ped['id_pedido'],))
            socio_nombre, proveedor_nombre = ped['socio_nombre'], ped['proveedor_nombre']

        try:
            NotificacionModel().crear_notificacion(
                mensaje=f"El socio {socio_nombre} anuló su Pedido {codigo} para '{proveedor_nombre}'.",
                tipo="pedido_anulado",
                id_user=None
            )
        except Exception as e:
            print(f"Advertencia al notificar anulación: {e}")
        return codigo

    # ------------------------------------------------------------------
    # Historial
    # ------------------------------------------------------------------

    def obtener_historial_pedidos(self, id_socio):
        """
        Consulta todos los pedidos registrados por el socio, con su proveedor, estado,
        totales calculados con el precio congelado e identificadores comerciales protegidos.
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id_pedido, p.codigo_comercial, p.fecha, p.estado,
                       pr.nombre AS proveedor_nombre,
                       COUNT(dp.id_articulo) AS cantidad_articulos,
                       COALESCE(SUM(dp.cantidad_pedida), 0) AS total_unidades,
                       COALESCE(SUM(dp.cantidad_pedida * dp.precio_unitario), 0.0) AS total_estimado,
                       group_concat(a.detalle || ' (' || dp.cantidad_pedida || 'u)', ', ') AS resumen_productos
                FROM PEDIDOS p
                LEFT JOIN PROVEEDORES pr ON pr.id_proveedor = p.id_proveedor
                LEFT JOIN DETALLE_PEDIDOS dp ON p.id_pedido = dp.id_pedido
                LEFT JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
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
