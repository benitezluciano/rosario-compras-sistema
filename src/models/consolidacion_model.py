import os
import re
import pandas as pd
from src.database import Database
from src.models.notificacion_model import NotificacionModel

class ConsolidacionModel:
    def obtener_pedidos_pendientes_detalle(self):
        """
        Consulta todos los pedidos en estado 'Pendiente' con su desglose completo.
        """
        query = """
            SELECT p.id_pedido, 
                   u.id AS id_user,
                   u.nombre AS socio_nombre, 
                   u.email AS socio_email,
                   p.fecha, 
                   a.id_articulo,
                   a.id_articulo_proveedor,
                   a.detalle AS articulo_detalle, 
                   a.rubro, 
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
            return [dict(row) for row in cursor.fetchall()]

    def obtener_resumen_consolidado(self, id_proveedor=None):
        """
        Agrupa la demanda total por artículo de los pedidos pendientes.
        Opcionalmente filtra por proveedor.
        """
        query = """
            SELECT a.id_articulo,
                   a.id_articulo_proveedor,
                   a.detalle AS articulo_detalle,
                   a.rubro,
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
        """
        Genera la planilla consolidada general (.xlsx o .csv).
        """
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
                'rubro': 'Rubro',
                'proveedor_nombre': 'Proveedor',
                'cantidad_total': 'Cantidad Total Pedida',
                'precio_unitario': 'Precio Unitario ($)',
                'total_estimado': 'Total Estimado ($)',
                'detalle_socios': 'Desglose por Socio'
            }
            cols_r_existentes = {k: v for k, v in columnas_resumen.items() if k in df_resumen.columns}
            df_resumen = df_resumen.rename(columns=cols_r_existentes)
            # Eliminar columnas internas
            df_resumen = df_resumen.drop(columns=['id_proveedor'], errors='ignore')

            columnas_detalles = {
                'id_pedido': 'Nro Pedido',
                'socio_nombre': 'Socio',
                'socio_email': 'Email Socio',
                'fecha': 'Fecha Pedido',
                'id_articulo': 'ID Art.',
                'id_articulo_proveedor': 'Cód. Proveedor',
                'articulo_detalle': 'Artículo / Detalle',
                'rubro': 'Rubro',
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
        """
        Genera un archivo Excel independiente por cada proveedor con pedidos.
        """
        if not os.path.exists(carpeta_destino):
            return False, f"La carpeta seleccionada no existe: {carpeta_destino}"

        detalles = self.obtener_pedidos_pendientes_detalle()
        if not detalles:
            return False, "No hay pedidos pendientes para exportar por proveedor."

        try:
            # Agrupar pedidos por proveedor
            por_proveedor = {}
            for item in detalles:
                prov = item.get('proveedor_nombre', 'Sin_Proveedor')
                if prov not in por_proveedor:
                    por_proveedor[prov] = []
                por_proveedor[prov].append(item)

            archivos_creados = []

            for prov_nombre, items in por_proveedor.items():
                df = pd.DataFrame(items)
                
                # Agrupar por artículo para la orden de compra a este proveedor
                df_orden = df.groupby(['id_articulo', 'id_articulo_proveedor', 'articulo_detalle', 'rubro', 'precio_unitario']).agg(
                    cantidad_total=('cantidad_pedida', 'sum'),
                    monto_total=('subtotal', 'sum')
                ).reset_index()

                df_orden = df_orden.rename(columns={
                    'id_articulo': 'ID Art.',
                    'id_articulo_proveedor': 'Cód. Proveedor',
                    'articulo_detalle': 'Artículo / Detalle',
                    'rubro': 'Rubro',
                    'precio_unitario': 'Precio Unitario ($)',
                    'cantidad_total': 'Cantidad Total Solicitada',
                    'monto_total': 'Monto Total ($)'
                })

                # Nombre de archivo seguro
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
        """
        Pasa los pedidos 'Pendiente' a 'Consolidado' y notifica a cada socio involucrado.
        """
        with Database() as conn:
            cursor = conn.cursor()
            
            # Obtener los pedidos y socios afectados
            cursor.execute("""
                SELECT p.id_pedido, p.id_user, u.nombre AS socio_nombre
                FROM PEDIDOS p
                JOIN USERS u ON p.id_user = u.id
                WHERE p.estado = 'Pendiente'
            """)
            pedidos_pendientes = [dict(row) for row in cursor.fetchall()]
            
            if not pedidos_pendientes:
                return 0

            # Actualizar estado a 'Consolidado'
            cursor.execute("UPDATE PEDIDOS SET estado = 'Consolidado' WHERE estado = 'Pendiente'")

        # Emitir notificaciones a cada socio
        try:
            notif = NotificacionModel()
            for ped in pedidos_pendientes:
                notif.crear_notificacion(
                    mensaje=f"Tu Pedido #{ped['id_pedido']} fue consolidado por el ejecutivo y enviado a los proveedores.",
                    tipo="pedido_consolidado",
                    id_user=ped['id_user']
                )
        except Exception as e:
            print(f"Advertencia al emitir notificaciones de consolidación: {e}")

        return len(pedidos_pendientes)
