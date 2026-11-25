import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QSplitter, QMessageBox, QFileDialog,
    QCheckBox, QDateEdit
)
from PyQt6.QtCore import Qt, QStandardPaths, QDate
from PyQt6.QtGui import QColor, QFont

from src.config.empresa import LETRA_REMITO
from src.views.orden_compra_dialog import fecha_legible

VERDE, AMBAR, AZUL, GRIS = "#15803d", "#b45309", "#1e3a8a", "#64748b"

# Cómo ve el socio cada estado del pedido: (texto, color, fondo del recuadro de estado)
ESTADOS_SOCIO = {
    'Pendiente': ("⏳ Pendiente", AMBAR, "#fef3c7"),
    'Consolidado': ("📨 Enviado al proveedor", AZUL, "#dbeafe"),
    'Procesado': ("✅ Entregado", VERDE, "#dcfce7"),
    'Repartido': ("✅ Entregado", VERDE, "#dcfce7"),
}

# Opciones del filtro de estado: (texto, estados incluidos)
FILTRO_ESTADOS = [
    ("Todos los estados", None),
    ("⏳ Pendientes", ('Pendiente',)),
    ("📨 Enviados al proveedor", ('Consolidado',)),
    ("✅ Entregados", ('Procesado', 'Repartido')),
]


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


class HistorialView(QWidget):
    """
    Historial de pedidos del socio: lista con filtros y, debajo, el detalle del pedido
    seleccionado (renglones, precios, lo entregado) con acceso a la Nota de Pedido en PDF,
    al remito y a la modificación del pedido mientras está pendiente.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(15, 10, 15, 10)
        raiz.setSpacing(8)

        titulo = QLabel("📜 Historial de Pedidos")
        titulo.setStyleSheet("font-size: 18px; font-weight: bold;")
        raiz.addWidget(titulo)
        subtitulo = QLabel("Todos los pedidos que enviaste. Selecciona uno para ver su detalle o descargar la Nota de Pedido.")
        subtitulo.setStyleSheet(f"color: {GRIS};")
        raiz.addWidget(subtitulo)

        # --- Filtros ---
        self.cmb_proveedor = QComboBox()
        self.cmb_proveedor.setMinimumWidth(240)
        self.cmb_estado = QComboBox()
        self.cmb_estado.setMinimumWidth(200)
        for texto, estados in FILTRO_ESTADOS:
            self.cmb_estado.addItem(texto, estados)
        self.chk_fecha = QCheckBox("Fechas:")
        self.date_desde = QDateEdit(QDate.currentDate().addMonths(-1))
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDisplayFormat("dd/MM/yyyy")
        self.date_desde.setEnabled(False)
        self.date_hasta = QDateEdit(QDate.currentDate())
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDisplayFormat("dd/MM/yyyy")
        self.date_hasta.setEnabled(False)
        self.chk_fecha.toggled.connect(self._toggle_fechas)
        self.btn_refrescar_historial = QPushButton("🔄 Actualizar")
        fila = QHBoxLayout()
        for w in ("Proveedor:", self.cmb_proveedor, "Estado:", self.cmb_estado,
                  self.chk_fecha, self.date_desde, "a", self.date_hasta):
            if isinstance(w, str):
                lbl = QLabel(w)
                lbl.setStyleSheet("font-weight: bold;")
                fila.addWidget(lbl)
            else:
                fila.addWidget(w)
        fila.addStretch()
        fila.addWidget(self.btn_refrescar_historial)
        raiz.addLayout(fila)

        self.lbl_info_historial = QLabel()
        self.lbl_info_historial.setStyleSheet("font-weight: bold;")
        raiz.addWidget(self.lbl_info_historial)

        # --- Lista (arriba) y detalle (abajo) ---
        divisor = QSplitter(Qt.Orientation.Vertical)
        self.tabla_historial = self._tabla()
        divisor.addWidget(self.tabla_historial)
        divisor.addWidget(self._crear_panel_detalle())
        divisor.setSizes([260, 320])
        raiz.addWidget(divisor)

        self.limpiar_detalle()

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

    def _crear_panel_detalle(self):
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.setSpacing(6)

        self.lbl_detalle_titulo = QLabel()
        self.lbl_detalle_titulo.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {AZUL};")
        lay.addWidget(self.lbl_detalle_titulo)

        self.lbl_detalle_estado = QLabel()
        self.lbl_detalle_estado.setWordWrap(True)
        lay.addWidget(self.lbl_detalle_estado)

        self.tabla_detalle = self._tabla()
        self.tabla_detalle.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        lay.addWidget(self.tabla_detalle)

        self.lbl_detalle_total = QLabel()
        self.lbl_detalle_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_detalle_total.setStyleSheet("font-weight: bold; font-size: 13px;")
        lay.addWidget(self.lbl_detalle_total)

        acciones = QHBoxLayout()
        self.btn_modificar_pedido = QPushButton("✏️ Modificar pedido")
        self.btn_ver_remito = QPushButton("🚚 Ver remito")
        self.btn_abrir_nota = QPushButton("📄 Abrir Nota de Pedido (PDF)")
        self.btn_guardar_nota = QPushButton("💾 Guardar como…")
        self.btn_guardar_nota.setToolTip("Guarda la Nota de Pedido en PDF en la carpeta que elijas.")
        for b in (self.btn_modificar_pedido, self.btn_ver_remito, self.btn_abrir_nota, self.btn_guardar_nota):
            b.setMinimumHeight(34)
        acciones.addWidget(self.btn_modificar_pedido)
        acciones.addWidget(self.btn_ver_remito)
        acciones.addStretch()
        acciones.addWidget(self.btn_abrir_nota)
        acciones.addWidget(self.btn_guardar_nota)
        lay.addLayout(acciones)
        return panel

    # ------------------------------------------------------------------
    # Filtros
    # ------------------------------------------------------------------

    def cargar_filtro_proveedores(self, proveedores):
        """proveedores: [(nombre, id_proveedor)]. Conserva la selección si sigue existiendo."""
        actual = self.cmb_proveedor.currentData()
        self.cmb_proveedor.blockSignals(True)
        self.cmb_proveedor.clear()
        self.cmb_proveedor.addItem("Todos los proveedores", None)
        for nombre, id_prov in proveedores:
            self.cmb_proveedor.addItem(f"🏢 {nombre}", id_prov)
        idx = self.cmb_proveedor.findData(actual)
        self.cmb_proveedor.setCurrentIndex(idx if idx >= 0 else 0)
        self.cmb_proveedor.blockSignals(False)

    def filtro_proveedor(self):
        return self.cmb_proveedor.currentData()

    def filtro_estados(self):
        return self.cmb_estado.currentData()

    def _toggle_fechas(self, activo):
        self.date_desde.setEnabled(activo)
        self.date_hasta.setEnabled(activo)

    def filtro_rango_fechas(self):
        if not self.chk_fecha.isChecked():
            return None, None
        return (
            self.date_desde.date().toString("yyyy-MM-dd"),
            self.date_hasta.date().toString("yyyy-MM-dd"),
        )

    # ------------------------------------------------------------------
    # Lista de pedidos
    # ------------------------------------------------------------------

    def cargar_historial_pedidos(self, pedidos, total_pedidos=None):
        """Puebla la lista. total_pedidos: cantidad sin filtrar (para el resumen)."""
        headers = ["N° de Pedido", "Fecha", "Proveedor", "Estado", "Productos", "Unidades", "Total", "Remito"]
        t = self.tabla_historial
        t.blockSignals(True)
        t.clearSelection()
        t.setRowCount(0)
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setRowCount(len(pedidos))
        for fila, ped in enumerate(pedidos):
            texto_est, color_est, _ = ESTADOS_SOCIO.get(ped.get('estado'), (ped.get('estado'), None, None))
            remito = ped.get('numero_remito')
            celdas = [
                _item(ped.get('codigo_comercial'), "c", AZUL, True, dato=ped['id_pedido']),
                _item(fecha_legible(ped.get('fecha')), "c"),
                _item(ped.get('proveedor_nombre') or "-"),
                _item(texto_est, "c", color_est, True),
                _item(ped.get('cantidad_articulos', 0), "c"),
                _item(ped.get('total_unidades', 0), "c"),
                _item(_moneda(ped.get('total_estimado')), "d"),
                _item(f"{LETRA_REMITO} {remito}" if remito else "—", "c", None if remito else GRIS),
            ]
            for col, celda in enumerate(celdas):
                t.setItem(fila, col, celda)
        t.resizeColumnsToContents()
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        t.blockSignals(False)

        total = len(pedidos) if total_pedidos is None else total_pedidos
        if total == 0:
            self.lbl_info_historial.setText("📋 Aún no tienes pedidos registrados.")
        elif not pedidos:
            self.lbl_info_historial.setText("📭 No hay pedidos para los filtros seleccionados.")
        elif len(pedidos) == total:
            self.lbl_info_historial.setText(f"📋 {total} pedido(s) en tu historial")
        else:
            self.lbl_info_historial.setText(f"📋 Mostrando {len(pedidos)} de {total} pedido(s)")
        self.limpiar_detalle()

    def obtener_pedido_seleccionado(self):
        fila = self.tabla_historial.currentRow()
        if fila < 0 or not self.tabla_historial.selectionModel().hasSelection():
            return None
        item = self.tabla_historial.item(fila, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def seleccionar_pedido(self, id_pedido):
        for fila in range(self.tabla_historial.rowCount()):
            item = self.tabla_historial.item(fila, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == id_pedido:
                self.tabla_historial.selectRow(fila)
                return True
        return False

    # ------------------------------------------------------------------
    # Detalle del pedido
    # ------------------------------------------------------------------

    def limpiar_detalle(self):
        self.lbl_detalle_titulo.setText("Selecciona un pedido para ver su detalle.")
        self.lbl_detalle_estado.setText("")
        self.lbl_detalle_estado.setStyleSheet("")
        self.lbl_detalle_estado.setVisible(False)
        self.tabla_detalle.setRowCount(0)
        self.tabla_detalle.setColumnCount(0)
        self.lbl_detalle_total.setText("")
        for b in (self.btn_modificar_pedido, self.btn_abrir_nota, self.btn_guardar_nota):
            b.setEnabled(False)
        self.btn_modificar_pedido.setVisible(False)
        self.btn_ver_remito.setVisible(False)

    def mostrar_detalle(self, det):
        """det: resultado de PedidoModel.obtener_detalle_pedido."""
        estado = det.get('estado')
        texto_est, color_est, fondo = ESTADOS_SOCIO.get(estado, (estado, GRIS, "#f1f5f9"))
        self.lbl_detalle_titulo.setText(
            f"📦 Pedido {det['codigo_comercial']} · {det.get('proveedor_nombre') or '-'} · {fecha_legible(det.get('fecha'))}"
        )
        self.lbl_detalle_estado.setText(f"<b>{texto_est}</b> — {det.get('leyenda_estado', '')}")
        self.lbl_detalle_estado.setStyleSheet(
            f"background: {fondo}; color: {color_est}; border-radius: 6px; padding: 6px 10px;"
        )
        self.lbl_detalle_estado.setVisible(True)

        entregado = det.get('entregado')
        headers = ["Código", "Artículo", "Unidad", "Cantidad"]
        if entregado:
            headers.append("Entregado")
        headers += ["Precio Unitario", "Subtotal"]
        t = self.tabla_detalle
        t.setRowCount(0)
        t.setColumnCount(len(headers))
        t.setHorizontalHeaderLabels(headers)
        renglones = det.get('renglones', [])
        t.setRowCount(len(renglones))
        for fila, r in enumerate(renglones):
            cant_ped = r.get('cantidad_pedida') or 0
            cant_orig = r.get('cantidad_original')
            if cant_orig is None:
                cant_orig = cant_ped
            ajustado = cant_orig != cant_ped
            if ajustado:
                txt_cant = f"{cant_ped} (pediste {cant_orig})"
                celda_cant = _item(txt_cant, "c", AMBAR, True)
                celda_cant.setBackground(QColor("#fef3c7"))
                celda_cant.setToolTip(f"Pediste originalmente {cant_orig} unidad(es); el ejecutivo ajustó a {cant_ped}.")
            else:
                celda_cant = _item(cant_ped, "c", None, True)

            celdas = [
                _item(r.get('codigo') or "-", "c", GRIS),
                _item(r.get('detalle')),
                _item(r.get('unidad') or "Unidad", "c"),
                celda_cant,
            ]
            if entregado:
                ent = r.get('cantidad_entregada') or 0
                faltante = ent < cant_ped
                celda = _item(ent, "c", AMBAR if faltante else VERDE, True)
                if faltante:
                    celda.setBackground(QColor("#fef3c7"))
                    celda.setToolTip(f"Se entregaron {ent} de {cant_ped} (faltante del proveedor)")
                celdas.append(celda)
            celdas += [
                _item(_moneda(r.get('precio_unitario')), "d"),
                _item(_moneda(r.get('subtotal')), "d"),
            ]
            for col, celda in enumerate(celdas):
                t.setItem(fila, col, celda)
        t.resizeColumnsToContents()
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.lbl_detalle_total.setText(
            f"{len(renglones)} producto(s) · {det.get('total_unidades', 0)} unidad(es) · Total: {_moneda(det.get('total'))}"
        )

        # Botones según el estado
        self.btn_abrir_nota.setEnabled(True)
        self.btn_guardar_nota.setEnabled(True)
        pendiente = estado == 'Pendiente'
        self.btn_modificar_pedido.setVisible(pendiente)
        if pendiente:
            habilitada = bool(det.get('lista_habilitada'))
            self.btn_modificar_pedido.setEnabled(habilitada)
            self.btn_modificar_pedido.setToolTip(
                "Abre la hoja de este proveedor en Gestión de Pedidos." if habilitada
                else "La lista de este proveedor está cerrada: el pedido ya no puede modificarse."
            )
        self.btn_ver_remito.setVisible(bool(det.get('id_remito')))
        if det.get('remito_visible'):
            self.btn_ver_remito.setText(f"🚚 Ver remito {det['remito_visible']}")

    # ------------------------------------------------------------------
    # Diálogos y mensajes
    # ------------------------------------------------------------------

    def abrir_dialogo_guardar(self, nombre_sugerido):
        carpeta = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar Nota de Pedido", os.path.join(carpeta, nombre_sugerido), "Archivos PDF (*.pdf)"
        )
        if ruta and not ruta.lower().endswith(".pdf"):
            ruta += ".pdf"
        return ruta

    def mostrar_mensaje_exito(self, mensaje):
        QMessageBox.information(self, "Operación Exitosa", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        QMessageBox.critical(self, "Error", mensaje)

    def mostrar_mensaje_info(self, mensaje):
        QMessageBox.information(self, "Información", mensaje)
