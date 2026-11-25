import os
from datetime import datetime
import pandas as pd
from src.database import Database
from src.models.notificacion_model import NotificacionModel
from src.services.orden_compra_service import OrdenCompraService
from src.utils.id_generator import generar_codigo_pedido, generar_codigo_orden_compra


class ConsolidacionModel:
    """
    Consolidación de pedidos por proveedor.
    Cada pedido pertenece a un único proveedor (PEDIDOS.id_proveedor), por lo que
    todas las consultas filtran por ese campo y usan el precio congelado del renglón.
    """

    def obtener_proveedores(self):
        """Devuelve los proveedores para el selector, con su cantidad de pedidos pendientes."""
        query = """
            SELECT pr.id_proveedor, pr.nombre, pr.email, pr.lista_habilitada,
                   (SELECT COUNT(*) FROM PEDIDOS p
                    WHERE p.id_proveedor = pr.id_proveedor AND p.estado = 'Pendiente') AS pedidos_pendientes
            FROM PROVEEDORES pr
            ORDER BY pr.nombre ASC
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def obtener_socios_con_pedidos_pendientes(self, id_proveedor):
        """Devuelve los socios con pedido 'Pendiente' para el proveedor indicado."""
        query = """
            SELECT u.id, u.nombre, u.email, p.id_pedido, p.codigo_comercial, p.fecha
            FROM PEDIDOS p
            JOIN USERS u ON p.id_user = u.id
            WHERE p.estado = 'Pendiente' AND p.id_proveedor = ?
            ORDER BY u.nombre ASC, p.id_pedido DESC
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_proveedor,))
            socios = []
            vistos = set()
            for row in cursor.fetchall():
                s = dict(row)
                if s['id'] in vistos:
                    continue  # Un pedido pendiente por socio y proveedor
                vistos.add(s['id'])
                if not s.get('codigo_comercial'):
                    s['codigo_comercial'] = generar_codigo_pedido(s['id_pedido'], s['fecha'])
                socios.append(s)
            return socios

    def obtener_matriz_pedidos_proveedor(self, id_proveedor):
        """
        Retorna la matriz de consolidación por proveedor:
        - socios: socios con pedido pendiente para este proveedor
        - articulos: productos de la lista del proveedor con:
          - id_articulo, codigo, detalle, precio_unitario
          - total_cantidad: suma de pedidos de todos los socios
          - cantidades_por_socio: {id_socio: {'cantidad': int, 'id_pedido': int}}
        NOTA: Excluye explícitamente la columna 'Rubro' según requerimiento.
        """
        socios = self.obtener_socios_con_pedidos_pendientes(id_proveedor)
        if not socios:
            return {'socios': [], 'articulos': []}

        map_pedido_socio = {s['id_pedido']: s['id'] for s in socios}

        with Database() as conn:
            cursor = conn.cursor()
            # Artículos de la lista del proveedor
            cursor.execute("""
                SELECT a.id_articulo,
                       COALESCE(a.id_articulo_proveedor, '-') AS codigo,
                       a.detalle,
                       COALESCE(pn.precio_final, 0.0) AS precio_unitario
                FROM ARTICULOS a
                JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
                WHERE pn.id_proveedor = ?
            """, (id_proveedor,))
            articulos_lista = [dict(r) for r in cursor.fetchall()]

            # Renglones de los pedidos pendientes del proveedor
            marcadores = ",".join("?" for _ in map_pedido_socio)
            cursor.execute(f"""
                SELECT dp.id_pedido, dp.id_articulo, dp.cantidad_pedida,
                       COALESCE(dp.cantidad_original, dp.cantidad_pedida) AS cantidad_original,
                       dp.precio_unitario,
                       a.id_articulo_proveedor, a.detalle
                FROM DETALLE_PEDIDOS dp
                JOIN ARTICULOS a ON a.id_articulo = dp.id_articulo
                WHERE dp.id_pedido IN ({marcadores})
            """, list(map_pedido_socio.keys()))
            renglones = [dict(r) for r in cursor.fetchall()]

        articulos_dict = {}

        def asegurar_articulo(id_art, codigo, detalle, precio):
            if id_art not in articulos_dict:
                articulos_dict[id_art] = {
                    'id_articulo': id_art,
                    'codigo': codigo or '-',
                    'detalle': detalle,
                    'precio_unitario': precio,
                    'cantidades_por_socio': {
                        s['id']: {'cantidad': 0, 'cantidad_original': 0, 'id_pedido': s['id_pedido']} for s in socios
                    },
                    'total_cantidad': 0
                }
            return articulos_dict[id_art]

        for art in articulos_lista:
            asegurar_articulo(art['id_articulo'], art['codigo'], art['detalle'], art['precio_unitario'])

        for r in renglones:
            # Si un artículo ya no figura en la lista vigente, igual se muestra (con su precio congelado)
            art = asegurar_articulo(r['id_articulo'], r['id_articulo_proveedor'], r['detalle'], r['precio_unitario'])
            id_socio = map_pedido_socio[r['id_pedido']]
            art['cantidades_por_socio'][id_socio]['cantidad'] = r['cantidad_pedida']
            art['cantidades_por_socio'][id_socio]['cantidad_original'] = r['cantidad_original']

        lista_articulos = []
        for art in articulos_dict.values():
            art['total_cantidad'] = sum(item['cantidad'] for item in art['cantidades_por_socio'].values())
            lista_articulos.append(art)

        # Ordenar: primero los artículos con demanda > 0, luego alfabéticamente
        lista_articulos.sort(key=lambda x: (-x['total_cantidad'], x['detalle'].lower()))

        return {'socios': socios, 'articulos': lista_articulos}

    def guardar_modificaciones_ejecutivo(self, modificaciones, nombre_ejecutivo="Ejecutivo"):
        """
        Aplica los ajustes de cantidades realizados por el ejecutivo directamente sobre DETALLE_PEDIDOS.
        Emite una notificación inmediata a cada socio cuyo pedido fue modificado.
        modificaciones: lista de dicts con:
          id_pedido, id_socio, id_articulo, detalle, cant_anterior, cant_nueva
        """
        if not modificaciones:
            return 0

        socios_afectados = {}  # id_socio: {'codigo': str, 'cambios': [texto]}

        with Database() as conn:
            cursor = conn.cursor()
            for mod in modificaciones:
                id_ped = mod['id_pedido']
                id_art = mod['id_articulo']
                cant_nueva = mod['cant_nueva']
                id_socio = mod['id_socio']

                cursor.execute(
                    "SELECT codigo_comercial, fecha, id_proveedor, estado FROM PEDIDOS WHERE id_pedido = ?",
                    (id_ped,)
                )
                ped = cursor.fetchone()
                if not ped or ped['estado'] != 'Pendiente':
                    continue  # Solo se ajustan pedidos aún no consolidados

                if cant_nueva > 0:
                    cursor.execute("""
                        SELECT precio_final FROM PRECIOS_NEGOCIADOS
                        WHERE id_proveedor = ? AND id_articulo = ?
                    """, (ped['id_proveedor'], id_art))
                    pn = cursor.fetchone()
                    precio = pn['precio_final'] if pn else 0.0
                    # Si el renglón ya existe, conserva precio_unitario y cantidad_original;
                    # si es agregado por el ejecutivo, cantidad_original queda en 0.
                    cursor.execute("""
                        INSERT INTO DETALLE_PEDIDOS (id_pedido, id_articulo, cantidad_pedida, cantidad_original, precio_unitario)
                        VALUES (?, ?, ?, 0, ?)
                        ON CONFLICT(id_pedido, id_articulo) DO UPDATE SET cantidad_pedida = excluded.cantidad_pedida
                    """, (id_ped, id_art, cant_nueva, precio))
                else:
                    # Conservar el renglón con cantidad_pedida = 0 para mantener trazabilidad de cantidad_original
                    cursor.execute(
                        "UPDATE DETALLE_PEDIDOS SET cantidad_pedida = 0 WHERE id_pedido = ? AND id_articulo = ?",
                        (id_ped, id_art)
                    )

                if id_socio not in socios_afectados:
                    codigo = ped['codigo_comercial'] or generar_codigo_pedido(id_ped, ped['fecha'])
                    socios_afectados[id_socio] = {'codigo': codigo, 'cambios': []}
                socios_afectados[id_socio]['cambios'].append(
                    f"{mod['detalle']}: {mod['cant_anterior']}u ➔ {cant_nueva}u"
                )

        # Emitir notificaciones automáticas a los socios
        try:
            notif = NotificacionModel()
            for id_socio, data in socios_afectados.items():
                mensaje = (
                    f"⚠️ Tu Pedido {data['codigo']} fue modificado por el Ejecutivo ({nombre_ejecutivo}): "
                    f"{', '.join(data['cambios'])}. Los ajustes responden a disponibilidad confirmada del proveedor."
                )
                notif.crear_notificacion(mensaje=mensaje, tipo="pedido_modificado", id_user=id_socio)
        except Exception as e:
            print(f"Advertencia al notificar modificación de pedidos: {e}")

        return len(socios_afectados)

    def obtener_pedidos_pendientes_detalle(self, id_proveedor=None):
        """Consulta los pedidos 'Pendiente' (opcionalmente de un proveedor) con su desglose completo."""
        query = """
            SELECT p.id_pedido,
                   p.codigo_comercial,
                   u.id AS id_user,
                   u.nombre AS socio_nombre,
                   u.email AS socio_email,
                   p.fecha,
                   a.id_articulo,
                   a.id_articulo_proveedor,
                   a.detalle AS articulo_detalle,
                   dp.cantidad_pedida,
                   dp.precio_unitario,
                   (dp.cantidad_pedida * dp.precio_unitario) AS subtotal,
                   pr.id_proveedor,
                   pr.nombre AS proveedor_nombre
            FROM PEDIDOS p
            JOIN USERS u ON p.id_user = u.id
            JOIN PROVEEDORES pr ON pr.id_proveedor = p.id_proveedor
            JOIN DETALLE_PEDIDOS dp ON p.id_pedido = dp.id_pedido
            JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            WHERE p.estado = 'Pendiente' AND dp.cantidad_pedida > 0
        """
        params = []
        if id_proveedor is not None:
            query += " AND p.id_proveedor = ?"
            params.append(id_proveedor)
        query += " ORDER BY pr.nombre, a.detalle, u.nombre;"

        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            filas = []
            for row in cursor.fetchall():
                r = dict(row)
                if not r.get('codigo_comercial'):
                    r['codigo_comercial'] = generar_codigo_pedido(r['id_pedido'], r['fecha'])
                filas.append(r)
            return filas

    def obtener_resumen_consolidado(self, id_proveedor=None):
        """Agrupa la demanda total por artículo de los pedidos pendientes (opcionalmente de un proveedor)."""
        query = """
            SELECT a.id_articulo,
                   a.id_articulo_proveedor,
                   a.detalle AS articulo_detalle,
                   pr.id_proveedor,
                   pr.nombre AS proveedor_nombre,
                   SUM(dp.cantidad_pedida) AS cantidad_total,
                   MAX(dp.precio_unitario) AS precio_unitario,
                   SUM(dp.cantidad_pedida * dp.precio_unitario) AS total_estimado,
                   group_concat(u.nombre || ' (' || dp.cantidad_pedida || ')', ', ') AS detalle_socios
            FROM PEDIDOS p
            JOIN USERS u ON p.id_user = u.id
            JOIN PROVEEDORES pr ON pr.id_proveedor = p.id_proveedor
            JOIN DETALLE_PEDIDOS dp ON p.id_pedido = dp.id_pedido
            JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            WHERE p.estado = 'Pendiente' AND dp.cantidad_pedida > 0
        """
        params = []
        if id_proveedor is not None:
            query += " AND p.id_proveedor = ?"
            params.append(id_proveedor)

        query += " GROUP BY pr.id_proveedor, a.id_articulo ORDER BY pr.nombre, a.detalle;"

        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def exportar_planilla(self, ruta_archivo, id_proveedor=None):
        """Genera la planilla consolidada (.xlsx o .csv), general o de un proveedor."""
        detalles = self.obtener_pedidos_pendientes_detalle(id_proveedor)
        resumen = self.obtener_resumen_consolidado(id_proveedor)

        if not detalles:
            return False, "No hay pedidos pendientes para exportar y consolidar."

        try:
            df_resumen = pd.DataFrame(resumen)
            df_detalles = pd.DataFrame(detalles)

            columnas_resumen = {
                'id_articulo': 'ID Art.',
                'id_articulo_proveedor': 'Cód. Proveedor',
                'articulo_detalle': 'Artículo / Detalle',
                'proveedor_nombre': 'Proveedor',
                'cantidad_total': 'Cantidad Total Pedida',
                'precio_unitario': 'Precio Unitario ($)',
                'total_estimado': 'Total Estimado ($)',
                'detalle_socios': 'Desglose por Socio'
            }
            df_resumen = df_resumen.rename(columns={k: v for k, v in columnas_resumen.items() if k in df_resumen.columns})
            df_resumen = df_resumen.drop(columns=['id_proveedor'], errors='ignore')

            columnas_detalles = {
                'id_pedido': 'Nro Pedido',
                'codigo_comercial': 'Cód. Comercial',
                'socio_nombre': 'Socio',
                'socio_email': 'Email Socio',
                'fecha': 'Fecha Pedido',
                'id_articulo': 'ID Art.',
                'id_articulo_proveedor': 'Cód. Proveedor',
                'articulo_detalle': 'Artículo / Detalle',
                'cantidad_pedida': 'Cantidad Pedida',
                'precio_unitario': 'Precio Unitario ($)',
                'subtotal': 'Subtotal ($)',
                'proveedor_nombre': 'Proveedor'
            }
            df_detalles = df_detalles.rename(columns={k: v for k, v in columnas_detalles.items() if k in df_detalles.columns})
            df_detalles = df_detalles.drop(columns=['id_user', 'id_proveedor'], errors='ignore')

            ext = os.path.splitext(ruta_archivo)[1].lower()
            if ext in ['.xlsx', '.xls']:
                with pd.ExcelWriter(ruta_archivo, engine='openpyxl') as writer:
                    df_resumen.to_excel(writer, sheet_name='Resumen Consolidado', index=False)
                    df_detalles.to_excel(writer, sheet_name='Detalle por Socio', index=False)
            else:
                df_resumen.to_csv(ruta_archivo, index=False, sep=';', encoding='utf-8-sig')

            return True, None
        except Exception as e:
            return False, f"Error al generar archivo consolidado: {str(e)}"

    # ------------------------------------------------------------------
    # Consolidación y órdenes de compra
    # ------------------------------------------------------------------

    def consolidar_proveedor(self, id_proveedor, ejecutivo=None):
        """
        Consolida los pedidos 'Pendiente' de UN proveedor y emite su orden de compra:
        - Crea la ORDEN DE COMPRA y vincula los pedidos (PEDIDOS.id_orden_compra).
        - Los pedidos pasan a 'Consolidado' (precio congelado).
        - Genera el archivo Excel de la orden en la carpeta ordenes_compra/.
        - Cierra la lista de precios del proveedor (fin del ciclo de pedidos).
        - Notifica a cada socio involucrado.
        Todo ocurre en una sola transacción: si el archivo no puede generarse, no se consolida nada.
        ejecutivo = {'id', 'nombre', 'email'} del usuario que consolida.
        Retorna el dict de la orden (ver obtener_orden_compra) o None si no había pedidos pendientes.
        """
        if id_proveedor is None:
            raise ValueError("Debe indicarse el proveedor a consolidar.")
        ejecutivo = ejecutivo or {}
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ruta_generada = None

        try:
            with Database() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.id_pedido, p.codigo_comercial, p.fecha, p.id_user, pr.nombre AS proveedor_nombre
                    FROM PEDIDOS p
                    JOIN PROVEEDORES pr ON pr.id_proveedor = p.id_proveedor
                    WHERE p.estado = 'Pendiente' AND p.id_proveedor = ?
                """, (id_proveedor,))
                pedidos_pendientes = []
                for row in cursor.fetchall():
                    ped = dict(row)
                    if not ped.get('codigo_comercial'):
                        ped['codigo_comercial'] = generar_codigo_pedido(ped['id_pedido'], ped['fecha'])
                    pedidos_pendientes.append(ped)

                if not pedidos_pendientes:
                    return None

                cursor.execute(
                    "INSERT INTO ORDENES_COMPRA (id_proveedor, id_user, fecha, cantidad_pedidos) VALUES (?, ?, ?, ?)",
                    (id_proveedor, ejecutivo.get('id'), fecha, len(pedidos_pendientes))
                )
                id_orden = cursor.lastrowid
                codigo = generar_codigo_orden_compra(id_orden, fecha)

                cursor.execute("""
                    UPDATE PEDIDOS SET estado = 'Consolidado', id_orden_compra = ?
                    WHERE estado = 'Pendiente' AND id_proveedor = ?
                """, (id_orden, id_proveedor))
                cursor.execute("UPDATE PROVEEDORES SET lista_habilitada = 0 WHERE id_proveedor = ?", (id_proveedor,))

                cursor.execute(
                    "UPDATE ORDENES_COMPRA SET codigo_comercial = ? WHERE id_orden_compra = ?", (codigo, id_orden)
                )
                datos = self._datos_orden(cursor, id_orden, ejecutivo)
                servicio = OrdenCompraService.get_instance()
                nombre_archivo = servicio.nombre_archivo(codigo, datos['proveedor']['nombre'], fecha)
                ruta_generada = servicio.generar_excel(datos, nombre_archivo)

                cursor.execute(
                    "UPDATE ORDENES_COMPRA SET archivo = ?, total = ? WHERE id_orden_compra = ?",
                    (nombre_archivo, datos['total'], id_orden)
                )
        except Exception:
            # Si la transacción falló después de escribir el archivo, no dejar un archivo huérfano
            if ruta_generada and os.path.exists(ruta_generada):
                try:
                    os.remove(ruta_generada)
                except OSError:
                    pass
            raise

        try:
            notif = NotificacionModel()
            for ped in pedidos_pendientes:
                notif.crear_notificacion(
                    mensaje=(
                        f"Tu Pedido {ped['codigo_comercial']} para '{ped['proveedor_nombre']}' fue consolidado "
                        f"en la Orden de Compra {codigo} para su envío al proveedor."
                    ),
                    tipo="pedido_consolidado",
                    id_user=ped['id_user']
                )
        except Exception as e:
            print(f"Advertencia al emitir notificaciones de consolidación: {e}")

        return self.obtener_orden_compra(id_orden)

    def _datos_orden(self, cursor, id_orden, ejecutivo=None):
        """Arma los datos de la orden (encabezado + totales por artículo) a partir de sus pedidos."""
        cursor.execute("""
            SELECT o.id_orden_compra, o.codigo_comercial, o.fecha, o.cantidad_pedidos, o.id_user,
                   pr.id_proveedor, pr.nombre, pr.email, pr.telefono, pr.direccion,
                   u.nombre AS ejecutivo_nombre, u.email AS ejecutivo_email
            FROM ORDENES_COMPRA o
            JOIN PROVEEDORES pr ON pr.id_proveedor = o.id_proveedor
            LEFT JOIN USERS u ON u.id = o.id_user
            WHERE o.id_orden_compra = ?
        """, (id_orden,))
        cab = cursor.fetchone()
        if not cab:
            raise ValueError(f"No existe la orden de compra {id_orden}.")
        cab = dict(cab)

        cursor.execute("""
            SELECT a.id_articulo, a.id_articulo_proveedor AS codigo_proveedor, a.detalle,
                   dp.precio_unitario, SUM(dp.cantidad_pedida) AS cantidad
            FROM DETALLE_PEDIDOS dp
            JOIN PEDIDOS p ON p.id_pedido = dp.id_pedido
            JOIN ARTICULOS a ON a.id_articulo = dp.id_articulo
            WHERE p.id_orden_compra = ?
            GROUP BY a.id_articulo, dp.precio_unitario
            HAVING SUM(dp.cantidad_pedida) > 0
            ORDER BY a.detalle
        """, (id_orden,))
        items = []
        for row in cursor.fetchall():
            it = dict(row)
            it['subtotal'] = round(it['cantidad'] * (it['precio_unitario'] or 0.0), 2)
            items.append(it)

        ejecutivo = ejecutivo or {}
        return {
            'id_orden_compra': cab['id_orden_compra'],
            'codigo': cab['codigo_comercial'],
            'fecha': cab['fecha'],
            'cantidad_pedidos': cab['cantidad_pedidos'],
            'proveedor': {
                'id_proveedor': cab['id_proveedor'], 'nombre': cab['nombre'], 'email': cab['email'],
                'telefono': cab['telefono'], 'direccion': cab['direccion'],
            },
            'ejecutivo': {
                'nombre': cab['ejecutivo_nombre'] or ejecutivo.get('nombre', 'Ejecutivo de Cuentas'),
                'email': cab['ejecutivo_email'] or ejecutivo.get('email', ''),
            },
            'items': items,
            'total': round(sum(i['subtotal'] for i in items), 2),
        }

    def obtener_orden_compra(self, id_orden):
        """
        Devuelve la orden de compra con sus datos de cabecera, artículos y la ruta absoluta del archivo:
        {id_orden_compra, codigo, fecha, cantidad_pedidos, proveedor{...}, ejecutivo{...}, items[...],
         total, archivo, ruta_archivo, fecha_envio_email, email_destino}
        """
        with Database() as conn:
            cursor = conn.cursor()
            datos = self._datos_orden(cursor, id_orden)
            cursor.execute(
                "SELECT archivo, fecha_envio_email, email_destino FROM ORDENES_COMPRA WHERE id_orden_compra = ?",
                (id_orden,)
            )
            extra = dict(cursor.fetchone())
        datos.update(extra)
        datos['ruta_archivo'] = (
            OrdenCompraService.get_instance().ruta_archivo(extra['archivo']) if extra['archivo'] else None
        )
        return datos

    def asegurar_archivo_orden(self, id_orden):
        """
        Devuelve la ruta del Excel de la orden. Si el archivo no existe (por ejemplo, se borró
        la carpeta o la orden viene de los datos de prueba), lo vuelve a generar desde la base.
        """
        orden = self.obtener_orden_compra(id_orden)
        if orden['ruta_archivo'] and os.path.exists(orden['ruta_archivo']):
            return orden['ruta_archivo']

        servicio = OrdenCompraService.get_instance()
        nombre_archivo = orden['archivo'] or servicio.nombre_archivo(
            orden['codigo'], orden['proveedor']['nombre'], orden['fecha']
        )
        ruta = servicio.generar_excel(orden, nombre_archivo)
        with Database() as conn:
            conn.execute(
                "UPDATE ORDENES_COMPRA SET archivo = ?, total = ? WHERE id_orden_compra = ?",
                (nombre_archivo, orden['total'], id_orden)
            )
        return ruta

    def registrar_envio_orden(self, id_orden, email_destino):
        """Registra que la orden fue enviada por correo al proveedor."""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with Database() as conn:
            conn.execute(
                "UPDATE ORDENES_COMPRA SET fecha_envio_email = ?, email_destino = ? WHERE id_orden_compra = ?",
                (fecha, email_destino, id_orden)
            )
        return fecha
