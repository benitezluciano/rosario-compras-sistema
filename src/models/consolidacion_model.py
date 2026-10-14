import os
import re
import pandas as pd
from src.database import Database
from src.models.notificacion_model import NotificacionModel
from src.utils.id_generator import generar_codigo_pedido

class ConsolidacionModel:
    def obtener_proveedores(self):
        """Devuelve los proveedores registrados para el selector de consolidación."""
        query = "SELECT id_proveedor, nombre, email FROM PROVEEDORES ORDER BY nombre ASC"
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def obtener_socios_con_pedidos_pendientes(self):
        """Devuelve los socios que tienen pedidos activos en estado 'Pendiente'."""
        query = """
            SELECT DISTINCT u.id, u.nombre, u.email, p.id_pedido, p.codigo_comercial, p.fecha
            FROM PEDIDOS p
            JOIN USERS u ON p.id_user = u.id
            WHERE p.estado = 'Pendiente'
            ORDER BY u.nombre ASC
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            socios = []
            for row in cursor.fetchall():
                s = dict(row)
                if not s.get('codigo_comercial'):
                    s['codigo_comercial'] = generar_codigo_pedido(s['id_pedido'], s['fecha'])
                socios.append(s)
            return socios

    def obtener_matriz_pedidos_proveedor(self, id_proveedor):
        """
        Retorna la matriz de consolidación por proveedor:
        - socios: lista de socios con pedidos pendientes
        - articulos: lista de productos del proveedor con:
          - id_articulo, codigo, detalle, precio_unitario
          - total_cantidad: suma de pedidos de todos los socios
          - cantidades_por_socio: {id_socio: {'cantidad': int, 'id_pedido': int}}
        NOTA: Excluye explícitamente la columna 'Rubro' según requerimiento.
        """
        socios = self.obtener_socios_con_pedidos_pendientes()
        if not socios:
            return {'socios': [], 'articulos': []}

        map_socio_pedido = {s['id']: s['id_pedido'] for s in socios}

        query = """
            SELECT a.id_articulo, 
                   COALESCE(a.id_articulo_proveedor, '-') AS codigo, 
                   a.detalle,
                   COALESCE(pn.precio_final, 0.0) AS precio_unitario,
                   p.id_pedido, 
                   p.id_user AS id_socio, 
                   COALESCE(dp.cantidad_pedida, 0) AS cantidad_pedida
            FROM ARTICULOS a
            JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
            LEFT JOIN DETALLE_PEDIDOS dp ON a.id_articulo = dp.id_articulo
            LEFT JOIN PEDIDOS p ON dp.id_pedido = p.id_pedido AND p.estado = 'Pendiente'
            WHERE pn.id_proveedor = ?
            ORDER BY a.detalle ASC;
        """

        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_proveedor,))
            filas = [dict(row) for row in cursor.fetchall()]

        # Agrupar por artículo
        articulos_dict = {}
        for f in filas:
            id_art = f['id_articulo']
            if id_art not in articulos_dict:
                articulos_dict[id_art] = {
                    'id_articulo': id_art,
                    'codigo': f['codigo'],
                    'detalle': f['detalle'],
                    'precio_unitario': f['precio_unitario'],
                    'cantidades_por_socio': {s['id']: {'cantidad': 0, 'id_pedido': map_socio_pedido.get(s['id'])} for s in socios},
                    'total_cantidad': 0
                }

            id_socio = f.get('id_socio')
            cant = f.get('cantidad_pedida', 0)
            if id_socio and id_socio in articulos_dict[id_art]['cantidades_por_socio']:
                articulos_dict[id_art]['cantidades_por_socio'][id_socio]['cantidad'] = cant
                if f.get('id_pedido'):
                    articulos_dict[id_art]['cantidades_por_socio'][id_socio]['id_pedido'] = f['id_pedido']

        # Calcular totales por artículo
        lista_articulos = []
        for art in articulos_dict.values():
            suma = sum(item['cantidad'] for item in art['cantidades_por_socio'].values())
            art['total_cantidad'] = suma
            lista_articulos.append(art)

        # Ordenar: primero los artículos con demanda > 0, luego alfabéticamente
        lista_articulos.sort(key=lambda x: (-x['total_cantidad'], x['detalle'].lower()))

        return {
            'socios': socios,
            'articulos': lista_articulos
        }

    def guardar_modificaciones_ejecutivo(self, modificaciones, nombre_ejecutivo="Ejecutivo"):
        """
        Aplica los ajustes de cantidades realizados por el ejecutivo directamente sobre DETALLE_PEDIDOS.
        Emite una notificación inmediata a cada socio cuyo pedido fue modificado.
        modificaciones: lista de dicts con:
          id_pedido, id_socio, id_articulo, detalle, cant_anterior, cant_nueva
        """
        if not modificaciones:
            return 0

        socios_afectados = {} # id_socio: {'id_pedido': id_ped, 'cambios': [texto]}

        with Database() as conn:
            cursor = conn.cursor()
            for mod in modificaciones:
                id_ped = mod['id_pedido']
                id_art = mod['id_articulo']
                cant_nueva = mod['cant_nueva']
                id_socio = mod['id_socio']
                detalle = mod['detalle']
                cant_ant = mod['cant_anterior']

                if cant_nueva > 0:
                    cursor.execute("""
                        INSERT OR REPLACE INTO DETALLE_PEDIDOS (id_pedido, id_articulo, cantidad_pedida)
                        VALUES (?, ?, ?)
                    """, (id_ped, id_art, cant_nueva))
                else:
                    cursor.execute("""
                        DELETE FROM DETALLE_PEDIDOS WHERE id_pedido = ? AND id_articulo = ?
                    """, (id_ped, id_art))

                if id_socio not in socios_afectados:
                    socios_afectados[id_socio] = {'id_pedido': id_ped, 'cambios': []}
                socios_afectados[id_socio]['cambios'].append(f"{detalle}: {cant_ant}u ➔ {cant_nueva}u")

        # Emitir notificaciones automáticas a los socios
        try:
            notif = NotificacionModel()
            for id_socio, data in socios_afectados.items():
                id_ped = data['id_pedido']
                resumen_cambios = ", ".join(data['cambios'])
                codigo_ped = generar_codigo_pedido(id_ped)
                mensaje = (
                    f"⚠️ Tu Pedido {codigo_ped} fue modificado por el Ejecutivo ({nombre_ejecutivo}): "
                    f"{resumen_cambios}. Los ajustes responden a disponibilidad confirmada del proveedor."
                )
                notif.crear_notificacion(
                    mensaje=mensaje,
                    tipo="pedido_modificado",
                    id_user=id_socio
                )
        except Exception as e:
            print(f"Advertencia al notificar modificación de pedidos: {e}")

        return len(socios_afectados)

    def obtener_pedidos_pendientes_detalle(self):
        """Consulta todos los pedidos en estado 'Pendiente' con su desglose completo."""
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
                   COALESCE(pn.precio_final, 0.0) AS precio_unitario,
                   (dp.cantidad_pedida * COALESCE(pn.precio_final, 0.0)) AS subtotal,
                   COALESCE(pr.id_proveedor, 0) AS id_proveedor,
                   COALESCE(pr.nombre, 'Sin Proveedor Asignado') AS proveedor_nombre
            FROM PEDIDOS p
            JOIN USERS u ON p.id_user = u.id
            JOIN DETALLE_PEDIDOS dp ON p.id_pedido = dp.id_pedido
            JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            LEFT JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
            LEFT JOIN PROVEEDORES pr ON pn.id_proveedor = pr.id_proveedor
            WHERE p.estado = 'Pendiente'
            ORDER BY pr.nombre, a.detalle, u.nombre;
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            filas = []
            for row in cursor.fetchall():
                r = dict(row)
                if not r.get('codigo_comercial'):
                    r['codigo_comercial'] = generar_codigo_pedido(r['id_pedido'], r['fecha'])
                filas.append(r)
            return filas

    def obtener_resumen_consolidado(self, id_proveedor=None):
        """Agrupa la demanda total por artículo de los pedidos pendientes."""
        query = """
            SELECT a.id_articulo,
                   a.id_articulo_proveedor,
                   a.detalle AS articulo_detalle,
                   COALESCE(pr.id_proveedor, 0) AS id_proveedor,
                   COALESCE(pr.nombre, 'Sin Proveedor') AS proveedor_nombre,
                   SUM(dp.cantidad_pedida) AS cantidad_total,
                   COALESCE(pn.precio_final, 0.0) AS precio_unitario,
                   SUM(dp.cantidad_pedida * COALESCE(pn.precio_final, 0.0)) AS total_estimado,
                   group_concat(u.nombre || ' (' || dp.cantidad_pedida || ')', ', ') AS detalle_socios
            FROM PEDIDOS p
            JOIN USERS u ON p.id_user = u.id
            JOIN DETALLE_PEDIDOS dp ON p.id_pedido = dp.id_pedido
            JOIN ARTICULOS a ON dp.id_articulo = a.id_articulo
            LEFT JOIN PRECIOS_NEGOCIADOS pn ON a.id_articulo = pn.id_articulo
            LEFT JOIN PROVEEDORES pr ON pn.id_proveedor = pr.id_proveedor
            WHERE p.estado = 'Pendiente'
        """
        params = []
        if id_proveedor is not None:
            query += " AND pr.id_proveedor = ?"
            params.append(id_proveedor)
            
        query += " GROUP BY a.id_articulo ORDER BY pr.nombre, a.detalle;"
        
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def exportar_planilla(self, ruta_archivo):
        """Genera la planilla consolidada general (.xlsx o .csv)."""
        detalles = self.obtener_pedidos_pendientes_detalle()
        resumen = self.obtener_resumen_consolidado()

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
            cols_r_existentes = {k: v for k, v in columnas_resumen.items() if k in df_resumen.columns}
            df_resumen = df_resumen.rename(columns=cols_r_existentes)
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
            cols_d_existentes = {k: v for k, v in columnas_detalles.items() if k in df_detalles.columns}
            df_detalles = df_detalles.rename(columns=cols_d_existentes)
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

    def exportar_ordenes_por_proveedor(self, carpeta_destino):
        """Genera un archivo Excel independiente por cada proveedor con pedidos."""
        if not os.path.exists(carpeta_destino):
            return False, f"La carpeta seleccionada no existe: {carpeta_destino}"

        detalles = self.obtener_pedidos_pendientes_detalle()
        if not detalles:
            return False, "No hay pedidos pendientes para exportar por proveedor."

        try:
            por_proveedor = {}
            for item in detalles:
                prov = item.get('proveedor_nombre', 'Sin_Proveedor')
                if prov not in por_proveedor:
                    por_proveedor[prov] = []
                por_proveedor[prov].append(item)

            archivos_creados = []

            for prov_nombre, items in por_proveedor.items():
                df = pd.DataFrame(items)
                
                df_orden = df.groupby(['id_articulo', 'id_articulo_proveedor', 'articulo_detalle', 'precio_unitario']).agg(
                    cantidad_total=('cantidad_pedida', 'sum'),
                    monto_total=('subtotal', 'sum')
                ).reset_index()

                df_orden = df_orden.rename(columns={
                    'id_articulo': 'ID Art.',
                    'id_articulo_proveedor': 'Cód. Proveedor',
                    'articulo_detalle': 'Artículo / Detalle',
                    'precio_unitario': 'Precio Unitario ($)',
                    'cantidad_total': 'Cantidad Total Solicitada',
                    'monto_total': 'Monto Total ($)'
                })

                prov_limpio = re.sub(r'[^a-zA-Z0-9_-]', '_', prov_nombre)
                nombre_archivo = f"Orden_Compra_{prov_limpio}.xlsx"
                ruta_final = os.path.join(carpeta_destino, nombre_archivo)

                with pd.ExcelWriter(ruta_final, engine='openpyxl') as writer:
                    df_orden.to_excel(writer, sheet_name='Orden de Compra', index=False)

                archivos_creados.append(nombre_archivo)

            return True, f"Se generaron {len(archivos_creados)} órdenes de compra en la carpeta:\n" + "\n".join([f"• {a}" for a in archivos_creados])
        except Exception as e:
            return False, f"Error al generar órdenes por proveedor: {str(e)}"

    def marcar_pedidos_como_consolidados(self):
        """Pasa los pedidos 'Pendiente' a 'Consolidado' y notifica a cada socio involucrado."""
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id_pedido, p.codigo_comercial, p.fecha, p.id_user, u.nombre AS socio_nombre
                FROM PEDIDOS p
                JOIN USERS u ON p.id_user = u.id
                WHERE p.estado = 'Pendiente'
            """)
            pedidos_pendientes = []
            for row in cursor.fetchall():
                ped = dict(row)
                if not ped.get('codigo_comercial'):
                    ped['codigo_comercial'] = generar_codigo_pedido(ped['id_pedido'], ped['fecha'])
                pedidos_pendientes.append(ped)
            
            if not pedidos_pendientes:
                return 0

            cursor.execute("UPDATE PEDIDOS SET estado = 'Consolidado' WHERE estado = 'Pendiente'")

        try:
            notif = NotificacionModel()
            for ped in pedidos_pendientes:
                cod = ped.get('codigo_comercial', f"#{ped['id_pedido']}")
                notif.crear_notificacion(
                    mensaje=f"Tu Pedido {cod} fue consolidado y enviado formalmente al proveedor para su preparación.",
                    tipo="pedido_consolidado",
                    id_user=ped['id_user']
                )
        except Exception as e:
            print(f"Advertencia al emitir notificaciones de consolidación: {e}")

        return len(pedidos_pendientes)
