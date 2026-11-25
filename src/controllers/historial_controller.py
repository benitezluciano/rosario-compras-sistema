from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices

from src.models.remito_model import RemitoModel


class HistorialController:
    """
    Historial de Pedidos del socio: lista con filtros, detalle del pedido seleccionado,
    Nota de Pedido en PDF (abrir o guardar), acceso al remito y a la modificación del
    pedido mientras está pendiente.
    """

    def __init__(self, vista, modelo, on_modificar_pedido=None, modelo_remito=None):
        self.vista = vista
        self.modelo = modelo
        self.on_modificar_pedido = on_modificar_pedido   # callback(id_proveedor)
        self.modelo_remito = modelo_remito or RemitoModel()
        self.id_socio = None
        self.pedidos = []
        self.detalle_actual = None

        self.vista.btn_refrescar_historial.clicked.connect(self.inicializar)
        self.vista.cmb_proveedor.currentIndexChanged.connect(self.aplicar_filtros)
        self.vista.cmb_estado.currentIndexChanged.connect(self.aplicar_filtros)
        self.vista.chk_fecha.toggled.connect(self.aplicar_filtros)
        self.vista.date_desde.dateChanged.connect(self.aplicar_filtros)
        self.vista.date_hasta.dateChanged.connect(self.aplicar_filtros)
        self.vista.tabla_historial.itemSelectionChanged.connect(self.al_seleccionar_pedido)
        self.vista.tabla_historial.cellDoubleClicked.connect(lambda *_: self.abrir_nota_pedido())
        self.vista.btn_abrir_nota.clicked.connect(self.abrir_nota_pedido)
        self.vista.btn_guardar_nota.clicked.connect(self.guardar_nota_pedido)
        self.vista.btn_ver_remito.clicked.connect(self.ver_remito)
        self.vista.btn_modificar_pedido.clicked.connect(self.modificar_pedido)

    def set_socio(self, id_socio):
        """Define el socio cuyo historial se mostrará."""
        self.id_socio = id_socio
        self.pedidos = []
        self.detalle_actual = None

    def inicializar(self):
        """Consulta el historial del socio y lo muestra (conserva filtros y selección)."""
        if not self.id_socio:
            return
        seleccionado = self.vista.obtener_pedido_seleccionado()
        try:
            self.pedidos = self.modelo.obtener_historial_pedidos(self.id_socio)
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"Error al cargar el historial: {e}")
            return
        proveedores = {}
        for p in self.pedidos:
            if p.get('id_proveedor') is not None:
                proveedores[p['id_proveedor']] = p.get('proveedor_nombre') or "-"
        self.vista.cargar_filtro_proveedores(sorted(((n, i) for i, n in proveedores.items()), key=lambda x: x[0]))
        self.aplicar_filtros()
        if seleccionado:
            self.vista.seleccionar_pedido(seleccionado)

    def aplicar_filtros(self):
        id_prov = self.vista.filtro_proveedor()
        estados = self.vista.filtro_estados()
        fecha_desde, fecha_hasta = self.vista.filtro_rango_fechas()
        filtrados = []
        for p in self.pedidos:
            if id_prov is not None and p.get('id_proveedor') != id_prov:
                continue
            if estados is not None and p.get('estado') not in estados:
                continue
            fecha_p = (p.get('fecha') or "")[:10]
            if fecha_desde and fecha_p < fecha_desde:
                continue
            if fecha_hasta and fecha_p > fecha_hasta:
                continue
            filtrados.append(p)
        self.detalle_actual = None
        self.vista.cargar_historial_pedidos(filtrados, total_pedidos=len(self.pedidos))

    # ------------------------------------------------------------------
    # Detalle
    # ------------------------------------------------------------------

    def al_seleccionar_pedido(self):
        id_pedido = self.vista.obtener_pedido_seleccionado()
        if not id_pedido:
            self.detalle_actual = None
            self.vista.limpiar_detalle()
            return
        try:
            self.detalle_actual = self.modelo.obtener_detalle_pedido(self.id_socio, id_pedido)
        except Exception as e:
            self.detalle_actual = None
            self.vista.limpiar_detalle()
            self.vista.mostrar_mensaje_error(f"No se pudo cargar el detalle del pedido:\n{e}")
            return
        self.vista.mostrar_detalle(self.detalle_actual)

    def _pedido_seleccionado(self):
        if not self.detalle_actual:
            self.vista.mostrar_mensaje_info("Selecciona un pedido de la lista.")
            return None
        return self.detalle_actual

    # ------------------------------------------------------------------
    # Nota de Pedido (PDF)
    # ------------------------------------------------------------------

    def abrir_nota_pedido(self):
        det = self._pedido_seleccionado()
        if not det:
            return
        try:
            ruta = self.modelo.generar_nota_pedido_pdf(self.id_socio, det['id_pedido'])
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"No se pudo generar la Nota de Pedido:\n{e}")
            return
        self.abrir_archivo(ruta)

    def guardar_nota_pedido(self):
        det = self._pedido_seleccionado()
        if not det:
            return
        try:
            nombre = self.modelo.nombre_archivo_nota_pedido(self.id_socio, det['id_pedido'])
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"No se pudo preparar la Nota de Pedido:\n{e}")
            return
        ruta = self.vista.abrir_dialogo_guardar(nombre)
        if not ruta:
            return
        try:
            ruta = self.modelo.generar_nota_pedido_pdf(self.id_socio, det['id_pedido'], ruta)
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"No se pudo guardar la Nota de Pedido:\n{e}")
            return
        self.vista.mostrar_mensaje_exito(f"✅ Nota de Pedido {det['codigo_comercial']} guardada en:\n{ruta}")

    # ------------------------------------------------------------------
    # Remito y modificación
    # ------------------------------------------------------------------

    def ver_remito(self):
        det = self._pedido_seleccionado()
        if not det:
            return
        if not det.get('id_remito'):
            self.vista.mostrar_mensaje_info("Este pedido todavía no tiene remito.")
            return
        try:
            ruta = self.modelo_remito.asegurar_pdf(det['id_remito'])
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"No se pudo generar el PDF del remito:\n{e}")
            return
        self.abrir_archivo(ruta)

    def modificar_pedido(self):
        det = self._pedido_seleccionado()
        if not det:
            return
        # Releer: el ejecutivo pudo haber consolidado o cerrado la lista mientras tanto
        try:
            det = self.modelo.obtener_detalle_pedido(self.id_socio, det['id_pedido'])
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"No se pudo verificar el pedido:\n{e}")
            return
        if det.get('estado') != 'Pendiente' or not det.get('lista_habilitada'):
            self.vista.mostrar_mensaje_info(
                f"El pedido {det['codigo_comercial']} ya no puede modificarse "
                f"(estado: {det.get('estado')}; lista {'habilitada' if det.get('lista_habilitada') else 'cerrada'})."
            )
            self.inicializar()
            return
        if self.on_modificar_pedido:
            self.on_modificar_pedido(det['id_proveedor'])

    def abrir_archivo(self, ruta):
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(ruta)):
            self.vista.mostrar_mensaje_error(f"No se pudo abrir el archivo automáticamente.\nUbicación:\n{ruta}")
