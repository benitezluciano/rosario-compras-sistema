from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter, QMessageBox,
    QCheckBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont

from src.config.empresa import LETRA_REMITO
from src.views.orden_compra_dialog import fecha_legible

VERDE, AMBAR, AZUL, GRIS = "#15803d", "#b45309", "#1e3a8a", "#64748b"


def _item(texto, alineacion=None, color=None, negrita=False, dato=None):
    item = QTableWidgetItem("" if texto is None else str(texto))
    if alineacion == "c":
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    elif alineacion == "d":
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    if color:
        item.setForeground(QColor(color))
    if negrita:
        fuente = QFont()
        fuente.setBold(True)
        item.setFont(fuente)
    if dato is not None:
        item.setData(Qt.ItemDataRole.UserRole, dato)
    return item


def _moneda(valor):
    return f"${(valor or 0):,.2f}"


class HistorialEjecutivoView(QWidget):
    """
    Historial del ejecutivo, con tres pestañas:
    - Órdenes de Compra (con los pedidos de la orden seleccionada y acceso a la orden).
    - Remitos Emitidos (con acceso al PDF).
    - Comprobantes de Proveedores (con el detalle del doble control).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(15, 10, 15, 10)
        raiz.setSpacing(10)

        titulo = QLabel("📜 Historial del Ejecutivo")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        raiz.addWidget(titulo)
        subtitulo = QLabel("Órdenes de compra emitidas, remitos entregados a los socios y comprobantes recibidos de los proveedores.")
        subtitulo.setStyleSheet(f"color: {GRIS};")
        raiz.addWidget(subtitulo)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._crear_tab_ordenes(), "🧾 Órdenes de Compra")
        self.tabs.addTab(self._crear_tab_remitos(), "🚚 Remitos Emitidos")
        self.tabs.addTab(self._crear_tab_comprobantes(), "📥 Comprobantes de Proveedores")
        raiz.addWidget(self.tabs)

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------

    def _tabla(self):
        tabla = QTableWidget()
        tabla.setAlternatingRowColors(True)
        tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        tabla.verticalHeader().setVisible(False)
        tabla.verticalHeader().setDefaultSectionSize(32)
        return tabla

    def _fila_filtros(self, *widgets):
        fila = QHBoxLayout()
        fila.setSpacing(8)
        for w in widgets:
            if isinstance(w, str):
                lbl = QLabel(w)
                lbl.setStyleSheet("font-weight: bold;")
                fila.addWidget(lbl)
            else:
                fila.addWidget(w)
        fila.addStretch()
        return fila

    def _crear_filtro_fechas(self):
        chk = QCheckBox("Fechas:")
        desde = QDateEdit(QDate.currentDate().addMonths(-1))
        desde.setCalendarPopup(True)
        desde.setDisplayFormat("dd/MM/yyyy")
        desde.setEnabled(False)
        hasta = QDateEdit(QDate.currentDate())
        hasta.setCalendarPopup(True)
        hasta.setDisplayFormat("dd/MM/yyyy")
        hasta.setEnabled(False)
        chk.toggled.connect(lambda activo: (desde.setEnabled(activo), hasta.setEnabled(activo)))
        return chk, desde, hasta

    @staticmethod
    def leer_rango_fechas(chk, desde, hasta):
        if not chk.isChecked():
            return None, None
        return desde.date().toString("yyyy-MM-dd"), hasta.date().toString("yyyy-MM-dd")

    def _crear_tab_ordenes(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(10, 10, 10, 10)

        self.cmb_ord_proveedor = QComboBox()
        self.cmb_ord_proveedor.setMinimumWidth(200)
        self.cmb_ord_estado = QComboBox()
        self.cmb_ord_estado.setMinimumWidth(180)
        self.chk_ord_fecha, self.date_ord_desde, self.date_ord_hasta = self._crear_filtro_fechas()
        self.btn_ord_actualizar = QPushButton("🔄 Actualizar")
        fila = self._fila_filtros(
            "Proveedor:", self.cmb_ord_proveedor,
            "Estado:", self.cmb_ord_estado,
            self.chk_ord_fecha, self.date_ord_desde, "a", self.date_ord_hasta
        )
        fila.addWidget(self.btn_ord_actualizar)
        lay.addLayout(fila)

        self.lbl_ord_info = QLabel()
        self.lbl_ord_info.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_ord_info)

        divisor = QSplitter(Qt.Orientation.Vertical)
        self.tabla_ordenes = self._tabla()
        divisor.addWidget(self.tabla_ordenes)

        panel = QWidget()
        lay_panel = QVBoxLayout(panel)
        lay_panel.setContentsMargins(0, 6, 0, 0)
        self.lbl_pedidos_orden = QLabel("Selecciona una orden para ver los pedidos que la componen.")
        self.lbl_pedidos_orden.setStyleSheet(f"font-weight: bold; color: {AZUL};")
        lay_panel.addWidget(self.lbl_pedidos_orden)
        self.tabla_pedidos_orden = self._tabla()
        self.tabla_pedidos_orden.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        lay_panel.addWidget(self.tabla_pedidos_orden)
        divisor.addWidget(panel)
        divisor.setSizes([320, 200])
        lay.addWidget(divisor)

        acciones = QHBoxLayout()
        acciones.addStretch()
        self.btn_ver_orden = QPushButton("🔍 Ver Orden (abrir · reenviar)")
        self.btn_ver_orden.setMinimumHeight(36)
        self.btn_ver_orden.setEnabled(False)
        acciones.addWidget(self.btn_ver_orden)
        lay.addLayout(acciones)
        return tab

    def _crear_tab_remitos(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(10, 10, 10, 10)

        self.cmb_rem_proveedor = QComboBox()
        self.cmb_rem_proveedor.setMinimumWidth(200)
        self.cmb_rem_socio = QComboBox()
        self.cmb_rem_socio.setMinimumWidth(200)
        self.chk_rem_fecha, self.date_rem_desde, self.date_rem_hasta = self._crear_filtro_fechas()
        self.btn_rem_actualizar = QPushButton("🔄 Actualizar")
        fila = self._fila_filtros(
            "Proveedor:", self.cmb_rem_proveedor,
            "Socio:", self.cmb_rem_socio,
            self.chk_rem_fecha, self.date_rem_desde, "a", self.date_rem_hasta
        )
        fila.addWidget(self.btn_rem_actualizar)
        lay.addLayout(fila)

        self.lbl_rem_info = QLabel()
        self.lbl_rem_info.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_rem_info)

        self.tabla_remitos = self._tabla()
        lay.addWidget(self.tabla_remitos)

        acciones = QHBoxLayout()
        acciones.addStretch()
        self.btn_abrir_remito = QPushButton("📄 Abrir PDF del Remito")
        self.btn_abrir_remito.setMinimumHeight(36)
        self.btn_abrir_remito.setEnabled(False)
        acciones.addWidget(self.btn_abrir_remito)
        lay.addLayout(acciones)
        return tab

    def _crear_tab_comprobantes(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(10, 10, 10, 10)

        self.cmb_comp_proveedor = QComboBox()
        self.cmb_comp_proveedor.setMinimumWidth(200)
        self.cmb_comp_control = QComboBox()
        self.cmb_comp_control.setMinimumWidth(180)
        self.chk_comp_fecha, self.date_comp_desde, self.date_comp_hasta = self._crear_filtro_fechas()
        self.btn_comp_actualizar = QPushButton("🔄 Actualizar")
        fila = self._fila_filtros(
            "Proveedor:", self.cmb_comp_proveedor,
            "Control:", self.cmb_comp_control,
            self.chk_comp_fecha, self.date_comp_desde, "a", self.date_comp_hasta
        )
        fila.addWidget(self.btn_comp_actualizar)
        lay.addLayout(fila)

        self.lbl_comp_info = QLabel()
        self.lbl_comp_info.setStyleSheet("font-weight: bold;")
        lay.addWidget(self.lbl_comp_info)

        divisor = QSplitter(Qt.Orientation.Vertical)
        self.tabla_comprobantes = self._tabla()
        divisor.addWidget(self.tabla_comprobantes)

        panel = QWidget()
        lay_panel = QVBoxLayout(panel)
        lay_panel.setContentsMargins(0, 6, 0, 0)
        self.lbl_detalle_comp = QLabel("Selecciona un comprobante para ver el detalle del control.")
        self.lbl_detalle_comp.setStyleSheet(f"font-weight: bold; color: {AZUL};")
        lay_panel.addWidget(self.lbl_detalle_comp)
        self.tabla_detalle_comp = self._tabla()
        self.tabla_detalle_comp.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        lay_panel.addWidget(self.tabla_detalle_comp)
        divisor.addWidget(panel)
        divisor.setSizes([300, 220])
        lay.addWidget(divisor)
        return tab

    # ------------------------------------------------------------------
    # Filtros
    # ------------------------------------------------------------------

    def _cargar_combo(self, combo, opciones):
        """opciones: [(texto, dato)]. Conserva la selección actual si sigue existiendo."""
        actual = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for texto, dato in opciones:
            combo.addItem(texto, dato)
        idx = combo.findData(actual)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)

    def cargar_filtros(self, proveedores, socios, estados_orden, controles):
        prov = [("Todos los proveedores", None)] + [(f"🏢 {p['nombre']}", p['id_proveedor']) for p in proveedores]
        for combo in (self.cmb_ord_proveedor, self.cmb_rem_proveedor, self.cmb_comp_proveedor):
            self._cargar_combo(combo, prov)
        self._cargar_combo(self.cmb_rem_socio, [("Todos los socios", None)] + [(f"👤 {s['nombre']}", s['id']) for s in socios])
        self._cargar_combo(self.cmb_ord_estado, estados_orden)
        self._cargar_combo(self.cmb_comp_control, controles)

    # ------------------------------------------------------------------
    # Órdenes de compra
    # ------------------------------------------------------------------

    def cargar_ordenes(self, ordenes):
        headers = ["N° de Orden", "Fecha", "Proveedor", "Pedidos", "Total", "Entrega", "Envío", "Emitida por"]
        t = self.tabla_ordenes
        t.clearSelection()
        t.setRowCount(0)
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setRowCount(len(ordenes))
        for fila, o in enumerate(ordenes):
            if o.get('pendientes_entrega'):
                entrega = _item(f"⏳ Pendiente ({o['pendientes_entrega']})", "c", AMBAR)
                entrega.setToolTip(f"{o['pendientes_entrega']} pedido(s) todavía sin repartir")
            else:
                entrega = _item("✅ Repartida", "c", VERDE)
            if o.get('fecha_envio_email'):
                envio = _item(f"✉️ Enviada {fecha_legible(o['fecha_envio_email'])[:10]}", "c", VERDE)
                envio.setToolTip(f"Enviada a {o.get('email_destino') or '-'} el {fecha_legible(o['fecha_envio_email'])}")
            else:
                envio = _item("⚠️ Sin enviar", "c", AMBAR, negrita=True)
            celdas = [
                _item(o.get('codigo_comercial'), "c", AZUL, True, dato=o['id_orden_compra']),
                _item(fecha_legible(o.get('fecha')), "c"),
                _item(o.get('proveedor_nombre')),
                _item(o.get('cantidad_pedidos'), "c"),
                _item(_moneda(o.get('total')), "d"),
                entrega,
                envio,
                _item(o.get('ejecutivo_nombre') or "-", None, GRIS),
            ]
            for col, celda in enumerate(celdas):
                t.setItem(fila, col, celda)
        t.resizeColumnsToContents()
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        sin_enviar = sum(1 for o in ordenes if not o.get('fecha_envio_email'))
        pendientes = sum(1 for o in ordenes if o.get('pendientes_entrega'))
        if ordenes:
            self.lbl_ord_info.setText(
                f"🧾 {len(ordenes)} orden(es) · {pendientes} pendiente(s) de entrega · {sin_enviar} sin enviar al proveedor"
            )
        else:
            self.lbl_ord_info.setText("📭 No hay órdenes de compra para los filtros seleccionados.")
        self.cargar_pedidos_orden(None, [])

    def obtener_orden_seleccionada(self):
        fila = self.tabla_ordenes.currentRow()
        if fila < 0 or not self.tabla_ordenes.selectionModel().hasSelection():
            return None
        item = self.tabla_ordenes.item(fila, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def seleccionar_orden(self, id_orden):
        for fila in range(self.tabla_ordenes.rowCount()):
            item = self.tabla_ordenes.item(fila, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == id_orden:
                self.tabla_ordenes.selectRow(fila)
                break

    def obtener_codigo_orden_seleccionada(self):
        fila = self.tabla_ordenes.currentRow()
        item = self.tabla_ordenes.item(fila, 0) if fila >= 0 else None
        return item.text() if item else ""

    def cargar_pedidos_orden(self, codigo_orden, pedidos):
        headers = ["N° de Pedido", "Socio", "Fecha", "Estado", "Unidades", "Ajustes", "Total", "Remito"]
        t = self.tabla_pedidos_orden
        t.setRowCount(0)
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setRowCount(len(pedidos))
        colores = {'Consolidado': AZUL, 'Procesado': VERDE, 'Repartido': VERDE}
        for fila, p in enumerate(pedidos):
            ajustes = p.get('ajustes_ejecutivo') or 0
            celda_ajuste = (
                _item(f"⚠️ {ajustes} ítem(s)", "c", AMBAR, True)
                if ajustes else _item("Sin ajustes", "c", GRIS)
            )
            celdas = [
                _item(p.get('codigo_comercial'), "c"),
                _item(p.get('socio_nombre')),
                _item(p.get('fecha'), "c"),
                _item(p.get('estado'), "c", colores.get(p.get('estado'))),
                _item(p.get('unidades'), "c"),
                celda_ajuste,
                _item(_moneda(p.get('total')), "d"),
                _item(p.get('remito_codigo') or "—", "c", None if p.get('remito_codigo') else GRIS),
            ]
            for col, celda in enumerate(celdas):
                t.setItem(fila, col, celda)
        t.resizeColumnsToContents()
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        if codigo_orden:
            self.lbl_pedidos_orden.setText(f"📦 Pedidos de la Orden {codigo_orden} ({len(pedidos)})")
        else:
            self.lbl_pedidos_orden.setText("Selecciona una orden para ver los pedidos que la componen.")
        self.btn_ver_orden.setEnabled(bool(codigo_orden))

    # ------------------------------------------------------------------
    # Remitos
    # ------------------------------------------------------------------

    def cargar_remitos(self, remitos):
        headers = ["N° de Remito", "Fecha", "Socio", "Proveedor", "Pedido", "Orden de Compra", "Unidades",
                   "Comprobante", "Ref. Interna", "PDF"]
        t = self.tabla_remitos
        t.clearSelection()
        t.setRowCount(0)
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setRowCount(len(remitos))
        for fila, r in enumerate(remitos):
            pdf = _item("📄 Disponible", "c", VERDE) if r.get('ruta_pdf') else _item("Se generará al abrirlo", "c", GRIS)
            celdas = [
                _item(f"{LETRA_REMITO} {r.get('numero_remito') or '-'}", "c", AZUL, True, dato=r['id_remito']),
                _item(r.get('fecha_emision'), "c"),
                _item(r.get('socio_nombre')),
                _item(r.get('proveedor_nombre') or "-"),
                _item(r.get('pedido_codigo') or "-", "c"),
                _item(r.get('orden_codigo') or "-", "c"),
                _item(r.get('unidades'), "c"),
                _item(r.get('comprobante') or "-", "c", GRIS),
                _item(r.get('codigo_comercial') or "-", "c", GRIS),
                pdf,
            ]
            for col, celda in enumerate(celdas):
                t.setItem(fila, col, celda)
        t.resizeColumnsToContents()
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        if remitos:
            self.lbl_rem_info.setText(f"🚚 {len(remitos)} remito(s) emitido(s)")
        else:
            self.lbl_rem_info.setText("📭 No hay remitos para los filtros seleccionados.")
        self.btn_abrir_remito.setEnabled(False)

    def obtener_remito_seleccionado(self):
        """Devuelve (id_remito, número visible) del remito seleccionado, o None."""
        fila = self.tabla_remitos.currentRow()
        if fila < 0 or not self.tabla_remitos.selectionModel().hasSelection():
            return None
        item = self.tabla_remitos.item(fila, 0)
        return (item.data(Qt.ItemDataRole.UserRole), item.text()) if item else None

    # ------------------------------------------------------------------
    # Comprobantes
    # ------------------------------------------------------------------

    def cargar_comprobantes(self, comprobantes):
        headers = ["Tipo", "N° Comprobante", "Proveedor", "Emisión", "Recepción", "Artículos",
                   "Resultado del Control", "Total Facturado", "Observaciones"]
        t = self.tabla_comprobantes
        t.clearSelection()
        t.setRowCount(0)
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setRowCount(len(comprobantes))
        for fila, c in enumerate(comprobantes):
            difs = []
            if c.get('faltantes'):
                difs.append(f"faltan {c['faltantes']} u.")
            if c.get('excedentes'):
                difs.append(f"sobran {c['excedentes']} u.")
            if c.get('articulos_dif_precio'):
                difs.append(f"{c['articulos_dif_precio']} precio(s) distinto(s)")
            control = _item("⚠️ " + " · ".join(difs), None, AMBAR, True) if difs else _item("✅ Sin diferencias", "c", VERDE)
            celdas = [
                _item(c.get('tipo_comprobante'), "c", dato=c['id_comprobante']),
                _item(c.get('nro_comprobante'), "c", AZUL, True),
                _item(c.get('proveedor_nombre')),
                _item(c.get('fecha_emision'), "c"),
                _item(fecha_legible(c.get('fecha_recepcion')), "c"),
                _item(c.get('articulos'), "c"),
                control,
                _item(_moneda(c.get('total_facturado')), "d"),
                _item(c.get('observaciones') or "", None, GRIS),
            ]
            for col, celda in enumerate(celdas):
                t.setItem(fila, col, celda)
        t.resizeColumnsToContents()
        t.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Stretch)

        if comprobantes:
            con_dif = sum(1 for c in comprobantes if c.get('faltantes') or c.get('excedentes') or c.get('articulos_dif_precio'))
            self.lbl_comp_info.setText(f"📥 {len(comprobantes)} comprobante(s) · {con_dif} con diferencias")
        else:
            self.lbl_comp_info.setText("📭 No hay comprobantes para los filtros seleccionados.")
        self.cargar_detalle_comprobante(None, [])

    def obtener_comprobante_seleccionado(self):
        """Devuelve (id_comprobante, nro) del comprobante seleccionado, o None."""
        fila = self.tabla_comprobantes.currentRow()
        if fila < 0 or not self.tabla_comprobantes.selectionModel().hasSelection():
            return None
        item_id = self.tabla_comprobantes.item(fila, 0)
        item_nro = self.tabla_comprobantes.item(fila, 1)
        return (item_id.data(Qt.ItemDataRole.UserRole), item_nro.text()) if item_id and item_nro else None

    def cargar_detalle_comprobante(self, nro, renglones):
        headers = ["Cód.", "Artículo", "Pedido", "Recibido", "Diferencia", "Precio Pactado", "Precio Facturado"]
        t = self.tabla_detalle_comp
        t.setRowCount(0)
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setRowCount(len(renglones))
        for fila, d in enumerate(renglones):
            dif = d.get('diferencia') or 0
            precio_distinto = abs((d.get('precio_facturado') or 0) - (d.get('precio_pactado') or 0)) > 0.009
            celdas = [
                _item(d.get('codigo') or "-", "c"),
                _item(d.get('detalle')),
                _item(d.get('cantidad_pedida'), "c"),
                _item(d.get('cantidad_recibida'), "c"),
                _item(f"{dif:+d}" if dif else "0", "c", AMBAR if dif else VERDE, bool(dif)),
                _item(_moneda(d.get('precio_pactado')), "d"),
                _item(_moneda(d.get('precio_facturado')), "d", AMBAR if precio_distinto else None, precio_distinto),
            ]
            for col, celda in enumerate(celdas):
                t.setItem(fila, col, celda)
        t.resizeColumnsToContents()
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.lbl_detalle_comp.setText(
            f"🔎 Detalle del control del comprobante {nro}" if nro
            else "Selecciona un comprobante para ver el detalle del control."
        )

    # ------------------------------------------------------------------
    # Diálogos y mensajes
    # ------------------------------------------------------------------

    def ejecutar_dialogo(self, dialogo):
        return dialogo.exec()

    def mostrar_mensaje_exito(self, mensaje):
        QMessageBox.information(self, "Operación Exitosa", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)

    def mostrar_mensaje_info(self, mensaje):
        QMessageBox.information(self, "Información", mensaje)
