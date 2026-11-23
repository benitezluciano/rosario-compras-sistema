import glob
import os
from src.config.empresa import EMPRESA, LETRA_REMITO, PUNTO_VENTA_REMITOS, DATOS_SIMULADOS
from src.database import Database
from src.services.pdf_service import PdfService
from src.utils.id_generator import generar_numero_remito

MAX_FALTANTES_EN_OBSERVACIONES = 3


class RemitoModel:
    """
    Arma los datos de un remito a partir de la base y genera (o regenera) su PDF.
    Se usa al emitir los remitos en el reparto y desde el historial cuando falta el archivo.
    """

    def obtener_datos_remito(self, id_remito):
        with Database() as conn:
            cab = conn.execute("""
                SELECT r.id_remito, r.codigo_comercial, r.numero_remito, r.fecha_emision,
                       u.nombre AS socio_nombre, u.cuit_dni, u.condicion_iva, u.domicilio,
                       pr.nombre AS proveedor_nombre,
                       p.codigo_comercial AS pedido_codigo,
                       o.codigo_comercial AS orden_codigo,
                       pc.archivo_consolidado AS comprobante
                FROM REMITOS r
                JOIN USERS u ON u.id = r.id_user
                LEFT JOIN PROVEEDORES pr ON pr.id_proveedor = r.id_proveedor
                LEFT JOIN PEDIDOS p ON p.id_pedido = r.id_pedido
                LEFT JOIN ORDENES_COMPRA o ON o.id_orden_compra = p.id_orden_compra
                LEFT JOIN PROCESOS_REPARTO pc ON pc.id_proceso = r.id_proceso
                WHERE r.id_remito = ?
            """, (id_remito,)).fetchone()
            if not cab:
                raise ValueError(f"No existe el remito {id_remito}.")
            cab = dict(cab)

            renglones = [dict(r) for r in conn.execute("""
                SELECT dr.cantidad_entregada, dp.cantidad_pedida,
                       a.id_articulo_proveedor AS codigo, a.detalle, a.unidad
                FROM DETALLE_REMITOS dr
                JOIN REMITOS r ON r.id_remito = dr.id_remito
                JOIN ARTICULOS a ON a.id_articulo = dr.id_articulo
                LEFT JOIN DETALLE_PEDIDOS dp ON dp.id_pedido = r.id_pedido AND dp.id_articulo = dr.id_articulo
                WHERE dr.id_remito = ?
                ORDER BY a.detalle
            """, (id_remito,)).fetchall()]

        items = [{
            'cantidad': r['cantidad_entregada'],
            'unidad': r['unidad'] or 'Unidad',
            'codigo': r['codigo'],
            'detalle': r['detalle'],
        } for r in renglones if (r['cantidad_entregada'] or 0) > 0]

        referencias = []
        if cab.get('pedido_codigo'):
            referencias.append(f"Pedido {cab['pedido_codigo']}")
        if cab.get('orden_codigo'):
            referencias.append(f"Orden de Compra {cab['orden_codigo']}")
        if cab.get('proveedor_nombre'):
            referencias.append(f"Proveedor: {cab['proveedor_nombre']}")
        if cab.get('comprobante'):
            referencias.append(f"Comprobante: {cab['comprobante']}")

        return {
            'id_remito': cab['id_remito'],
            'letra': LETRA_REMITO,
            'numero': cab.get('numero_remito') or generar_numero_remito(cab['id_remito'], PUNTO_VENTA_REMITOS),
            'codigo': cab.get('codigo_comercial') or "",
            'fecha': cab.get('fecha_emision') or "",
            'emisor': dict(EMPRESA),
            'destinatario': {
                'nombre': cab.get('socio_nombre') or "",
                'cuit_dni': cab.get('cuit_dni'),
                'condicion_iva': cab.get('condicion_iva'),
                'domicilio': cab.get('domicilio'),
            },
            'referencias': " · ".join(referencias) or "—",
            'items': items,
            'cantidad_renglones': len(items),
            'total_unidades': sum(i['cantidad'] for i in items),
            'observaciones': self._observaciones(cab, renglones),
            'datos_simulados': DATOS_SIMULADOS,
        }

    @staticmethod
    def _observaciones(cab, renglones):
        """Texto automático: pedido de origen y, si hubo prorrateo, los faltantes entregados."""
        texto = f"Entrega del pedido {cab.get('pedido_codigo') or '-'}"
        if cab.get('proveedor_nombre'):
            texto += f" de {cab['proveedor_nombre']}"
        texto += "."

        faltantes = [r for r in renglones
                     if r.get('cantidad_pedida') is not None and (r['cantidad_entregada'] or 0) < r['cantidad_pedida']]
        if faltantes:
            partes = []
            for r in faltantes[:MAX_FALTANTES_EN_OBSERVACIONES]:
                if (r['cantidad_entregada'] or 0) == 0:
                    partes.append(f"{r['detalle']}: no se entrega (pedido: {r['cantidad_pedida']})")
                else:
                    partes.append(f"{r['detalle']}: se entregan {r['cantidad_entregada']} de {r['cantidad_pedida']}")
            texto += " Por faltante del proveedor: " + "; ".join(partes)
            restantes = len(faltantes) - MAX_FALTANTES_EN_OBSERVACIONES
            if restantes > 0:
                texto += f"; y {restantes} artículo(s) más con faltante"
            texto += "."
        return texto

    def generar_pdf(self, id_remito):
        """Genera el PDF del remito (reemplaza el archivo si ya existía). Retorna la ruta."""
        return PdfService.get_instance().generar_remito_pdf(self.obtener_datos_remito(id_remito))

    def ruta_pdf_existente(self, codigo_remito):
        """
        Ruta del PDF del remito si existe en la carpeta, con el formato actual
        ('Remito_<letra>_<número>_..._<código interno>.pdf'). Los PDF del formato anterior
        se ignoran, así se regeneran con el diseño nuevo.
        """
        if not codigo_remito:
            return None
        carpeta = PdfService.get_instance().carpeta_remitos
        patron = f"Remito_{glob.escape(LETRA_REMITO)}_*_{glob.escape(codigo_remito)}.pdf"
        coincidencias = glob.glob(os.path.join(carpeta, patron))
        return max(coincidencias, key=os.path.getmtime) if coincidencias else None

    def asegurar_pdf(self, id_remito):
        """Devuelve la ruta del PDF del remito; si el archivo no existe, lo vuelve a generar desde la base."""
        with Database() as conn:
            fila = conn.execute("SELECT codigo_comercial FROM REMITOS WHERE id_remito = ?", (id_remito,)).fetchone()
        if not fila:
            raise ValueError(f"No existe el remito {id_remito}.")
        return self.ruta_pdf_existente(fila['codigo_comercial']) or self.generar_pdf(id_remito)
