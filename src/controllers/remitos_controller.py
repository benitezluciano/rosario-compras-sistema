import os
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QMessageBox
from src.services.pdf_service import PdfService
from src.database import Database

class RemitosController:
    """
    Controlador para la gestión y consulta de Remitos Oficiales (RF-18).
    Maneja la carga reactiva, filtrado en memoria y apertura segura de archivos PDF.
    """
    def __init__(self, vista, modelo_reparto, modelo_catalogo=None):
        self.vista = vista
        self.modelo_reparto = modelo_reparto
        self.modelo_catalogo = modelo_catalogo
        self.usuario_actual = None
        self.todos_los_remitos = []

        # Conexión de eventos de la vista
        self.vista.btn_refrescar.clicked.connect(self.inicializar)
        self.vista.solicitar_abrir_pdf.connect(self.abrir_remito_pdf)
        self.vista.solicitar_abrir_carpeta.connect(self.abrir_carpeta_remitos)
        self.vista.filtros_modificados.connect(self.aplicar_filtros)

    def set_usuario_actual(self, usuario):
        """Establece el usuario activo y adapta la vista según su rol."""
        self.usuario_actual = usuario
        rol = usuario.get('role', 'socio')
        nombre = usuario.get('nombre', '')
        self.vista.configurar_para_rol(rol, nombre)

    def inicializar(self):
        """Carga los combos de filtrado y los remitos disponibles para el usuario."""
        if not self.usuario_actual:
            return

        rol = self.usuario_actual.get('role', 'socio')
        user_id = self.usuario_actual['id']

        # 1. Cargar combo de proveedores
        try:
            if self.modelo_catalogo:
                proveedores = self.modelo_catalogo.obtener_proveedores()
            else:
                with Database() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id_proveedor, nombre FROM PROVEEDORES ORDER BY nombre ASC;")
                    proveedores = [dict(row) for row in cursor.fetchall()]
            self.vista.cargar_proveedores_filtro(proveedores)
        except Exception as e:
            print(f"Error al cargar proveedores en filtro de remitos: {e}")

        # 2. Si es Ejecutivo o Admin, cargar combo de socios
        if rol in ['admin', 'ejecutivo']:
            try:
                socios = self.modelo_reparto.obtener_socios_con_remitos()
                self.vista.cargar_socios_filtro(socios)
            except Exception as e:
                print(f"Error al cargar socios en filtro de remitos: {e}")

        # 3. Consultar remitos de la base de datos
        try:
            id_filtro_usuario = user_id if rol == 'socio' else None
            self.todos_los_remitos = self.modelo_reparto.obtener_remitos(
                id_user=id_filtro_usuario,
                rol=rol
            )
            self.aplicar_filtros()
        except Exception as e:
            QMessageBox.critical(self.vista, "Error", f"No se pudieron cargar los remitos: {str(e)}")

    def aplicar_filtros(self):
        """Aplica el texto de búsqueda y los combos de selección sobre la lista de remitos."""
        texto = self.vista.obtener_texto_busqueda()
        id_socio_filtro = self.vista.obtener_socio_filtro()
        id_prov_filtro = self.vista.obtener_proveedor_filtro()

        filtrados = []
        for r in self.todos_los_remitos:
            # Filtro por Socio (si aplica)
            if id_socio_filtro is not None and r.get('id_user') != id_socio_filtro:
                continue

            # Filtro por Proveedor (si aplica)
            if id_prov_filtro is not None and r.get('id_proveedor') != id_prov_filtro:
                continue

            # Filtro por texto libre
            if texto:
                campos_busqueda = [
                    str(r.get('codigo_remito', '')),
                    str(r.get('socio_nombre', '')),
                    str(r.get('proveedor_nombre', '')),
                    str(r.get('codigo_pedido', '')),
                    str(r.get('resumen_articulos', '')),
                    str(r.get('fecha_emision', ''))
                ]
                cadena_unificada = " ".join(campos_busqueda).lower()
                if texto not in cadena_unificada:
                    continue

            filtrados.append(r)

        self.vista.cargar_remitos(filtrados)

    def abrir_remito_pdf(self, remito_dict):
        """
        Abre el archivo PDF del remito seleccionado utilizando la aplicación predeterminada del sistema.
        Si el archivo no existe físicamente en disco, lo regenera automáticamente al instante.
        """
        if not remito_dict:
            return

        ruta_pdf = remito_dict.get('archivo_pdf')

        # Si el archivo no existe o la ruta está vacía, regenerarlo dinámicamente
        if not ruta_pdf or not os.path.exists(ruta_pdf):
            try:
                id_remito = remito_dict['id_remito']
                items = self.modelo_reparto.obtener_detalle_remito(id_remito)

                datos_remito = {
                    'codigo_remito': remito_dict.get('codigo_remito', f"RC-REM-{id_remito}"),
                    'codigo_pedido': remito_dict.get('codigo_pedido', f"RC-ORD-{remito_dict.get('id_pedido', '')}"),
                    'nro_comprobante': remito_dict.get('detalle_entrega', 'CMP-AUTO'),
                    'fecha': remito_dict.get('fecha_emision', ''),
                    'socio_nombre': remito_dict.get('socio_nombre', 'Socio'),
                    'socio_email': remito_dict.get('socio_email', ''),
                    'proveedor_nombre': remito_dict.get('proveedor_nombre', 'Proveedor General'),
                    'items': [
                        {
                            'id_articulo': it['id_articulo'],
                            'codigo': it.get('codigo') or f"ART-{it['id_articulo']}",
                            'detalle': it['detalle'],
                            'cantidad': it['cantidad_entregada']
                        } for it in items
                    ]
                }

                pdf_service = PdfService.get_instance()
                ruta_pdf = pdf_service.generar_remito_pdf(datos_remito)

                # Persistir la nueva ruta en la base de datos
                with Database() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE REMITOS SET archivo_pdf = ? WHERE id_remito = ?", (ruta_pdf, id_remito))

                remito_dict['archivo_pdf'] = ruta_pdf

            except Exception as e:
                QMessageBox.critical(
                    self.vista,
                    "Error al Generar PDF",
                    f"No se pudo generar el comprobante oficial en PDF:\n{str(e)}"
                )
                return

        # Abrir el PDF con la aplicación nativa del sistema operativo
        try:
            ruta_absoluta = os.path.abspath(ruta_pdf)
            QDesktopServices.openUrl(QUrl.fromLocalFile(ruta_absoluta))
        except Exception as e:
            QMessageBox.critical(
                self.vista,
                "Error al Abrir Archivo",
                f"No se pudo abrir el archivo PDF:\n{str(e)}"
            )

    def abrir_carpeta_remitos(self):
        """Abre la carpeta local del sistema donde se almacenan todos los PDFs de remitos emitidos."""
        try:
            pdf_service = PdfService.get_instance()
            carpeta = pdf_service.carpeta_remitos
            os.makedirs(carpeta, exist_ok=True)
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.abspath(carpeta)))
        except Exception as e:
            QMessageBox.critical(
                self.vista,
                "Error al Abrir Carpeta",
                f"No se pudo abrir la carpeta de remitos:\n{str(e)}"
            )
