from PyQt6.QtWidgets import QMessageBox, QDialog
from src.views.proveedores_dialog import ProveedoresDialog
from src.views.email_preview_dialog import EmailPreviewDialog
from src.services.email_service import EmailService

class CatalogoController:
    def __init__(self, vista, modelo, on_catalogo_updated=None, usuario_actual=None):
        self.vista = vista
        self.modelo = modelo
        self.on_catalogo_updated = on_catalogo_updated
        self.usuario_actual = usuario_actual or {"id": 2, "nombre": "Ejecutivo", "email": "ejecutivo@rosariocompras.com", "role": "ejecutivo"}
        self.email_service = EmailService.get_instance()
        
        # Conectar señales
        if hasattr(self.vista, 'btn_solicitar_lista'):
            self.vista.btn_solicitar_lista.clicked.connect(self.solicitar_lista_proveedor)
        if hasattr(self.vista, 'btn_gestionar_proveedores'):
            self.vista.btn_gestionar_proveedores.clicked.connect(self.abrir_gestion_proveedores)
        if hasattr(self.vista, 'btn_seleccionar_archivo'):
            self.vista.btn_seleccionar_archivo.clicked.connect(self.seleccionar_archivo)
        if hasattr(self.vista, 'btn_importar'):
            self.vista.btn_importar.clicked.connect(self.procesar_importacion)

    def set_usuario_actual(self, usuario):
        """Actualiza la sesión del usuario conectado."""
        self.usuario_actual = usuario

    def inicializar(self):
        """Carga la lista de proveedores en el combo."""
        proveedores = self.modelo.obtener_proveedores()
        self.vista.cargar_proveedores(proveedores)

    def abrir_gestion_proveedores(self):
        """Abre el diálogo modal de administración y CRUD de proveedores."""
        dialog = ProveedoresDialog(
            usuario_actual=self.usuario_actual,
            on_proveedores_changed=self.inicializar,
            on_solicitar_lista=self.solicitar_lista_proveedor,
            parent=self.vista
        )
        dialog.exec()
        self.inicializar()

    def solicitar_lista_proveedor(self, id_proveedor=None):
        """Prepara y envía la solicitud formal de lista de precios por correo electrónico."""
        if not id_proveedor or not isinstance(id_proveedor, int):
            id_proveedor = self.vista.obtener_proveedor_seleccionado()

        if not id_proveedor:
            self.vista.mostrar_mensaje_error("Debes seleccionar un proveedor asignado.")
            return

        exito, mensaje, prov = self.modelo.solicitar_lista_proveedor(id_proveedor)
        if not exito or not prov:
            self.vista.mostrar_mensaje_error(mensaje)
            return

        nombre_prov = prov.get("nombre", "Proveedor")
        email_prov = prov.get("email") or ""
        nombre_ejec = self.usuario_actual.get("nombre", "Ejecutivo de Cuentas")
        email_ejec = self.usuario_actual.get("email", "ejecutivo@rosariocompras.com")

        # Generar cuerpo HTML con el membrete y formato oficial
        cuerpo_html = self.email_service.generar_plantilla_solicitud_lista(
            nombre_proveedor=nombre_prov,
            nombre_ejecutivo=nombre_ejec,
            email_ejecutivo=email_ejec
        )

        asunto = f"Solicitud de Lista de Precios Actualizada - {nombre_prov} [Rosario Compras]"

        # Abrir el diálogo de vista previa y confirmación
        dialog = EmailPreviewDialog(
            destinatario=email_prov,
            asunto=asunto,
            cuerpo_html=cuerpo_html,
            parent=self.vista
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            msg_res = getattr(dialog, "resultado_mensaje", "Solicitud de lista de precios emitida exitosamente.")
            self.vista.mostrar_mensaje_exito(f"✅ {msg_res}")

    def seleccionar_archivo(self):
        """Abre el archivo seleccionado y muestra la vista previa."""
        ruta = self.vista.abrir_dialogo_archivo()
        if not ruta:
            return

        headers, filas, error = self.modelo.leer_vista_previa(ruta)
        if error:
            self.vista.mostrar_mensaje_error(error)
            self.vista.limpiar_vista()
        else:
            self.vista.cargar_tabla_previa(headers, filas)

    def procesar_importacion(self):
        """Ejecuta la importación del archivo hacia la base de datos y notifica a los socios."""
        if not self.vista.ruta_archivo_actual:
            self.vista.mostrar_mensaje_error("Debes seleccionar una planilla (.xlsx o .csv) antes de procesar.")
            return

        id_proveedor = self.vista.obtener_proveedor_seleccionado()
        if not id_proveedor:
            self.vista.mostrar_mensaje_error("Debes seleccionar un proveedor asignado.")
            return

        exito, mensaje = self.modelo.importar_lista_proveedor(id_proveedor, self.vista.ruta_archivo_actual)
        if exito:
            self.vista.mostrar_mensaje_exito(mensaje)
            self.vista.limpiar_vista()
            if self.on_catalogo_updated:
                self.on_catalogo_updated()
        else:
            self.vista.mostrar_mensaje_error(mensaje)
