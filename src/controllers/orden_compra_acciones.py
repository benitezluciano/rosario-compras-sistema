from PyQt6.QtWidgets import QDialog
from src.services.email_service import EmailService
from src.views.email_preview_dialog import EmailPreviewDialog
from src.views.orden_compra_dialog import OrdenCompraDialog, fecha_legible


class OrdenCompraAcciones:
    """
    Acciones sobre una orden de compra ya emitida, compartidas por la Consolidación
    (al emitirla) y el Historial del ejecutivo (al consultarla):
    ver la orden, abrir su archivo y enviarla por correo al proveedor.

    La vista debe ofrecer: ejecutar_dialogo(dialogo), mostrar_mensaje_exito(msg), mostrar_mensaje_error(msg).
    obtener_usuario(): devuelve el usuario conectado (para completar los datos del ejecutivo).
    """

    def __init__(self, vista, modelo_consolidacion, obtener_usuario):
        self.vista = vista
        self.modelo = modelo_consolidacion
        self.obtener_usuario = obtener_usuario
        self.email_service = EmailService.get_instance()

    def mostrar_orden(self, id_orden, titulo=None):
        """Abre la ventana de la orden (abrir archivo, abrir carpeta, enviar al proveedor)."""
        try:
            orden = self.modelo.obtener_orden_compra(id_orden)
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"No se pudo cargar la orden de compra: {e}")
            return
        dialogo = OrdenCompraDialog(
            orden,
            obtener_ruta=lambda: self.modelo.asegurar_archivo_orden(id_orden),
            enviar=self.enviar_por_email,
            titulo=titulo or f"🧾 Orden de Compra {orden.get('codigo', '')}",
            parent=self.vista
        )
        self.vista.ejecutar_dialogo(dialogo)

    def enviar_por_email(self, orden, parent=None):
        """
        Abre la vista previa del correo al proveedor con la orden adjunta.
        Devuelve la orden actualizada si el envío se realizó, o None si se canceló o falló.
        """
        id_orden = orden['id_orden_compra']
        try:
            ruta = self.modelo.asegurar_archivo_orden(id_orden)
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"No se pudo obtener el archivo de la orden: {e}")
            return None

        usuario = self.obtener_usuario() or {}
        prov = orden.get('proveedor', {})
        ejecutivo = orden.get('ejecutivo', {})
        cuerpo_html = self.email_service.generar_plantilla_orden_compra(
            nombre_proveedor=prov.get('nombre', ''),
            codigo_orden=orden.get('codigo', ''),
            fecha_orden=fecha_legible(orden.get('fecha', ''))[:10],
            cantidad_articulos=len(orden.get('items', [])),
            total=orden.get('total', 0.0),
            nombre_ejecutivo=ejecutivo.get('nombre') or usuario.get('nombre', ''),
            email_ejecutivo=ejecutivo.get('email') or usuario.get('email', ''),
        )
        dialogo = EmailPreviewDialog(
            destinatario=prov.get('email') or "",
            asunto=f"Orden de Compra {orden.get('codigo', '')} - Rosario Compras",
            cuerpo_html=cuerpo_html,
            adjuntos=[ruta],
            parent=parent or self.vista
        )
        if self.vista.ejecutar_dialogo(dialogo) != QDialog.DialogCode.Accepted:
            return None
        if not getattr(dialogo, "resultado_exito", False):
            self.vista.mostrar_mensaje_error(f"❌ {getattr(dialogo, 'resultado_mensaje', 'No se pudo enviar la orden.')}")
            return None

        destino = dialogo.txt_destinatario.text().strip()
        self.modelo.registrar_envio_orden(id_orden, destino)
        self.vista.mostrar_mensaje_exito(f"✅ {getattr(dialogo, 'resultado_mensaje', 'Orden enviada al proveedor.')}")
        return self.modelo.obtener_orden_compra(id_orden)
