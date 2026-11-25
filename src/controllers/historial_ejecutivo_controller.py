from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices

from src.controllers.orden_compra_acciones import OrdenCompraAcciones


class HistorialEjecutivoController:
    """Historial del ejecutivo: órdenes de compra, remitos emitidos y comprobantes de proveedores."""

    def __init__(self, vista, modelo, modelo_consolidacion, usuario_actual=None):
        self.vista = vista
        self.modelo = modelo
        self.usuario_actual = usuario_actual
        self.acciones_orden = OrdenCompraAcciones(vista, modelo_consolidacion, lambda: self.usuario_actual)

        # Órdenes de compra
        self.vista.cmb_ord_proveedor.currentIndexChanged.connect(self.cargar_ordenes)
        self.vista.cmb_ord_estado.currentIndexChanged.connect(self.cargar_ordenes)
        self.vista.chk_ord_fecha.toggled.connect(self.cargar_ordenes)
        self.vista.date_ord_desde.dateChanged.connect(self.cargar_ordenes)
        self.vista.date_ord_hasta.dateChanged.connect(self.cargar_ordenes)
        self.vista.btn_ord_actualizar.clicked.connect(self.cargar_ordenes)
        self.vista.tabla_ordenes.itemSelectionChanged.connect(self.al_seleccionar_orden)
        self.vista.tabla_ordenes.cellDoubleClicked.connect(lambda *_: self.ver_orden())
        self.vista.btn_ver_orden.clicked.connect(self.ver_orden)

        # Remitos
        self.vista.cmb_rem_proveedor.currentIndexChanged.connect(self.cargar_remitos)
        self.vista.cmb_rem_socio.currentIndexChanged.connect(self.cargar_remitos)
        self.vista.chk_rem_fecha.toggled.connect(self.cargar_remitos)
        self.vista.date_rem_desde.dateChanged.connect(self.cargar_remitos)
        self.vista.date_rem_hasta.dateChanged.connect(self.cargar_remitos)
        self.vista.btn_rem_actualizar.clicked.connect(self.cargar_remitos)
        self.vista.tabla_remitos.itemSelectionChanged.connect(self.al_seleccionar_remito)
        self.vista.tabla_remitos.cellDoubleClicked.connect(lambda *_: self.abrir_remito())
        self.vista.btn_abrir_remito.clicked.connect(self.abrir_remito)

        # Comprobantes
        self.vista.cmb_comp_proveedor.currentIndexChanged.connect(self.cargar_comprobantes)
        self.vista.cmb_comp_control.currentIndexChanged.connect(self.cargar_comprobantes)
        self.vista.chk_comp_fecha.toggled.connect(self.cargar_comprobantes)
        self.vista.date_comp_desde.dateChanged.connect(self.cargar_comprobantes)
        self.vista.date_comp_hasta.dateChanged.connect(self.cargar_comprobantes)
        self.vista.btn_comp_actualizar.clicked.connect(self.cargar_comprobantes)
        self.vista.tabla_comprobantes.itemSelectionChanged.connect(self.al_seleccionar_comprobante)

    def set_usuario_actual(self, usuario):
        self.usuario_actual = usuario

    def inicializar(self):
        """Recarga filtros y las tres pestañas (se llama al entrar a la pantalla)."""
        m = self.modelo
        self.vista.cargar_filtros(
            m.obtener_proveedores(),
            m.obtener_socios(),
            estados_orden=[
                ("Todas", None),
                ("⏳ Pendientes de entrega", m.ESTADO_PENDIENTE_ENTREGA),
                ("✅ Repartidas", m.ESTADO_REPARTIDA),
                ("⚠️ Sin enviar al proveedor", m.ESTADO_SIN_ENVIAR),
            ],
            controles=[
                ("Todos", None),
                ("⚠️ Con diferencias", m.CONTROL_CON_DIFERENCIAS),
                ("✅ Sin diferencias", m.CONTROL_SIN_DIFERENCIAS),
            ],
        )
        self.cargar_ordenes()
        self.cargar_remitos()
        self.cargar_comprobantes()

    # ------------------------------------------------------------------
    # Órdenes de compra
    # ------------------------------------------------------------------

    def cargar_ordenes(self):
        desde, hasta = self.vista.leer_rango_fechas(
            self.vista.chk_ord_fecha, self.vista.date_ord_desde, self.vista.date_ord_hasta
        )
        ordenes = self.modelo.obtener_ordenes(
            self.vista.cmb_ord_proveedor.currentData(),
            self.vista.cmb_ord_estado.currentData(),
            fecha_desde=desde,
            fecha_hasta=hasta,
        )
        self.vista.cargar_ordenes(ordenes)

    def al_seleccionar_orden(self):
        id_orden = self.vista.obtener_orden_seleccionada()
        if not id_orden:
            self.vista.cargar_pedidos_orden(None, [])
            return
        self.vista.cargar_pedidos_orden(
            self.vista.obtener_codigo_orden_seleccionada(),
            self.modelo.obtener_pedidos_de_orden(id_orden)
        )

    def ver_orden(self):
        id_orden = self.vista.obtener_orden_seleccionada()
        if not id_orden:
            self.vista.mostrar_mensaje_info("Selecciona una orden de compra de la lista.")
            return
        self.acciones_orden.mostrar_orden(id_orden)
        # Puede haberse reenviado: refrescar la lista conservando la orden seleccionada
        self.cargar_ordenes()
        self.vista.seleccionar_orden(id_orden)

    # ------------------------------------------------------------------
    # Remitos
    # ------------------------------------------------------------------

    def cargar_remitos(self):
        desde, hasta = self.vista.leer_rango_fechas(
            self.vista.chk_rem_fecha, self.vista.date_rem_desde, self.vista.date_rem_hasta
        )
        remitos = self.modelo.obtener_remitos(
            self.vista.cmb_rem_proveedor.currentData(),
            self.vista.cmb_rem_socio.currentData(),
            fecha_desde=desde,
            fecha_hasta=hasta,
        )
        self.vista.cargar_remitos(remitos)

    def al_seleccionar_remito(self):
        self.vista.btn_abrir_remito.setEnabled(bool(self.vista.obtener_remito_seleccionado()))

    def abrir_remito(self):
        seleccionado = self.vista.obtener_remito_seleccionado()
        if not seleccionado:
            self.vista.mostrar_mensaje_info("Selecciona un remito de la lista.")
            return
        id_remito, numero = seleccionado
        try:
            ruta = self.modelo.asegurar_pdf_remito(id_remito)
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"No se pudo generar el PDF del remito {numero}:\n{e}")
            return
        self.cargar_remitos()   # el estado del PDF puede haber cambiado (regenerado)
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(ruta)):
            self.vista.mostrar_mensaje_error(f"No se pudo abrir el PDF automáticamente.\nUbicación:\n{ruta}")

    # ------------------------------------------------------------------
    # Comprobantes
    # ------------------------------------------------------------------

    def cargar_comprobantes(self):
        desde, hasta = self.vista.leer_rango_fechas(
            self.vista.chk_comp_fecha, self.vista.date_comp_desde, self.vista.date_comp_hasta
        )
        comprobantes = self.modelo.obtener_comprobantes(
            self.vista.cmb_comp_proveedor.currentData(),
            self.vista.cmb_comp_control.currentData(),
            fecha_desde=desde,
            fecha_hasta=hasta,
        )
        self.vista.cargar_comprobantes(comprobantes)

    def al_seleccionar_comprobante(self):
        seleccionado = self.vista.obtener_comprobante_seleccionado()
        if not seleccionado:
            self.vista.cargar_detalle_comprobante(None, [])
            return
        id_comp, nro = seleccionado
        self.vista.cargar_detalle_comprobante(nro, self.modelo.obtener_detalle_comprobante(id_comp))
