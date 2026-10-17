import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QCursor

class RemitosView(QWidget):
    """
    Vista modular para la consulta, filtrado y apertura de Remitos Oficiales en PDF (RF-18).
    Disponible tanto para Socios (sus propios remitos) como para Ejecutivos/Administradores (todos los remitos).
    """
    solicitar_abrir_pdf = pyqtSignal(dict)
    solicitar_abrir_carpeta = pyqtSignal()
    filtros_modificados = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.remitos_actuales = []
        self.init_ui()

    def init_ui(self):
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(15, 12, 15, 15)
        layout_principal.setSpacing(12)

        # 1. Cabecera y Título
        frame_header = QFrame()
        frame_header.setObjectName("frame_header")
        layout_header = QVBoxLayout(frame_header)
        layout_header.setContentsMargins(4, 4, 4, 4)
        layout_header.setSpacing(4)

        lbl_titulo = QLabel("📄 Consulta y Descarga de Remitos Oficiales")
        lbl_titulo.setObjectName("lbl_titulo")
        layout_header.addWidget(lbl_titulo)

        self.lbl_subtitulo = QLabel(
            "Visualice, busque y descargue los remitos oficiales de entrega en formato PDF listos para control y recepción."
        )
        self.lbl_subtitulo.setStyleSheet("color: #64748b; font-size: 13px;")
        layout_header.addWidget(self.lbl_subtitulo)

        layout_principal.addWidget(frame_header)

        # 2. Barra de Filtros y Acciones
        frame_filtros = QFrame()
        frame_filtros.setObjectName("frame_filtros")
        frame_filtros.setStyleSheet("""
            QFrame#frame_filtros {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        layout_filtros = QHBoxLayout(frame_filtros)
        layout_filtros.setContentsMargins(10, 8, 10, 8)
        layout_filtros.setSpacing(10)

        # Buscador por texto
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar por N° remito, socio, proveedor o producto...")
        self.txt_buscar.setClearButtonEnabled(True)
        self.txt_buscar.textChanged.connect(self._emitir_filtros)
        layout_filtros.addWidget(self.txt_buscar, stretch=3)

        # Filtro por Socio (visible solo para Ejecutivo/Admin)
        self.lbl_socio = QLabel("Socio:")
        self.lbl_socio.setStyleSheet("font-weight: 600; color: #334155;")
        self.cmb_socio = QComboBox()
        self.cmb_socio.currentIndexChanged.connect(self._emitir_filtros)
        layout_filtros.addWidget(self.lbl_socio)
        layout_filtros.addWidget(self.cmb_socio, stretch=2)

        # Filtro por Proveedor
        self.lbl_proveedor = QLabel("Proveedor:")
        self.lbl_proveedor.setStyleSheet("font-weight: 600; color: #334155;")
        self.cmb_proveedor = QComboBox()
        self.cmb_proveedor.currentIndexChanged.connect(self._emitir_filtros)
        layout_filtros.addWidget(self.lbl_proveedor)
        layout_filtros.addWidget(self.cmb_proveedor, stretch=2)

        # Botón Refrescar
        self.btn_refrescar = QPushButton("🔄 Actualizar")
        self.btn_refrescar.setObjectName("btn_refrescar")
        self.btn_refrescar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        layout_filtros.addWidget(self.btn_refrescar)

        # Botón Abrir Carpeta
        self.btn_abrir_carpeta = QPushButton("📁 Carpeta de Remitos")
        self.btn_abrir_carpeta.setObjectName("btn_abrir_carpeta")
        self.btn_abrir_carpeta.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_abrir_carpeta.clicked.connect(self.solicitar_abrir_carpeta.emit)
        layout_filtros.addWidget(self.btn_abrir_carpeta)

        layout_principal.addWidget(frame_filtros)

        # 3. Tabla de Remitos Emitidos
        self.tabla_remitos = QTableWidget()
        self.tabla_remitos.setAlternatingRowColors(True)
        self.tabla_remitos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_remitos.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_remitos.verticalHeader().setDefaultSectionSize(44)
        self.tabla_remitos.cellDoubleClicked.connect(self._al_doble_click_fila)

        headers = [
            "N° Remito",
            "Fecha",
            "Socio Receptor",
            "Proveedor Origen",
            "Ref. Pedido",
            "Mercadería / Resumen",
            "Total Unid.",
            "Acción Comprobante"
        ]
        self.tabla_remitos.setColumnCount(len(headers))
        self.tabla_remitos.setHorizontalHeaderLabels(headers)

        header = self.tabla_remitos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.tabla_remitos.setColumnWidth(2, 210)
        self.tabla_remitos.setColumnWidth(3, 200)
        self.tabla_remitos.setColumnWidth(7, 130)

        layout_principal.addWidget(self.tabla_remitos, stretch=1)

        # 4. Barra Inferior de Estado / Resumen
        frame_footer = QFrame()
        layout_footer = QHBoxLayout(frame_footer)
        layout_footer.setContentsMargins(4, 4, 4, 4)

        self.lbl_resumen_info = QLabel("Cargando remitos...")
        self.lbl_resumen_info.setStyleSheet("color: #475569; font-weight: 500; font-size: 13px;")
        layout_footer.addWidget(self.lbl_resumen_info)

        layout_footer.addStretch()

        lbl_ayuda = QLabel("💡 Tip: Haga doble clic sobre cualquier fila o presione 'Ver PDF' para abrir el remito oficial.")
        lbl_ayuda.setStyleSheet("color: #64748b; font-size: 12px; font-style: italic;")
        layout_footer.addWidget(lbl_ayuda)

        layout_principal.addWidget(frame_footer)

    def _emitir_filtros(self):
        self.filtros_modificados.emit()

    def configurar_para_rol(self, rol, nombre_socio=""):
        """Configura los filtros visibles según si el usuario es Socio o Ejecutivo/Admin."""
        if rol == 'socio':
            self.lbl_socio.setVisible(False)
            self.cmb_socio.setVisible(False)
            self.lbl_subtitulo.setText(
                f"Bienvenido {nombre_socio}. Aquí puedes consultar y descargar todos los remitos de entrega de tus pedidos en formato PDF."
            )
        else:
            self.lbl_socio.setVisible(True)
            self.cmb_socio.setVisible(True)
            self.lbl_subtitulo.setText(
                "Gestión global de remitos emitidos para todos los socios de Rosario Compras. Descargue o visualice los PDFs oficiales."
            )

    def cargar_proveedores_filtro(self, proveedores):
        """Puebla el combo de proveedores para filtrado."""
        self.cmb_proveedor.blockSignals(True)
        self.cmb_proveedor.clear()
        self.cmb_proveedor.addItem("🏢 Todos los Proveedores", None)
        for p in proveedores:
            self.cmb_proveedor.addItem(f"🏢 {p['nombre']}", p['id_proveedor'])
        self.cmb_proveedor.blockSignals(False)

    def cargar_socios_filtro(self, socios):
        """Puebla el combo de socios para filtrado."""
        self.cmb_socio.blockSignals(True)
        self.cmb_socio.clear()
        self.cmb_socio.addItem("👥 Todos los Socios", None)
        for s in socios:
            self.cmb_socio.addItem(f"👤 {s['nombre']}", s['id'])
        self.cmb_socio.blockSignals(False)

    def obtener_texto_busqueda(self):
        return self.txt_buscar.text().strip().lower()

    def obtener_socio_filtro(self):
        return self.cmb_socio.currentData()

    def obtener_proveedor_filtro(self):
        return self.cmb_proveedor.currentData()

    def cargar_remitos(self, remitos):
        """Renderiza los remitos en la tabla con sus respectivos botones de acción y datos."""
        self.remitos_actuales = remitos
        self.tabla_remitos.blockSignals(True)
        self.tabla_remitos.setRowCount(len(remitos))

        font_bold = QFont()
        font_bold.setBold(True)

        total_unidades_gral = 0

        for row, r in enumerate(remitos):
            cod_remito = r.get('codigo_remito') or f"RC-REM-{r['id_remito']}"
            fecha = r.get('fecha_emision', '')
            socio = r.get('socio_nombre', 'Socio')
            proveedor = r.get('proveedor_nombre', 'Proveedor')
            cod_pedido = r.get('codigo_pedido') or f"RC-ORD-{r.get('id_pedido', '')}"
            resumen = r.get('resumen_articulos') or r.get('detalle_entrega') or "Mercadería procesada"
            total_unid = r.get('total_unidades', 0)
            total_unidades_gral += total_unid

            # Col 0: N° Remito
            item_rem = QTableWidgetItem(cod_remito)
            item_rem.setFont(font_bold)
            item_rem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_rem.setFlags(item_rem.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_remitos.setItem(row, 0, item_rem)

            # Col 1: Fecha
            item_fecha = QTableWidgetItem(fecha)
            item_fecha.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_fecha.setFlags(item_fecha.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_remitos.setItem(row, 1, item_fecha)

            # Col 2: Socio Receptor
            item_socio = QTableWidgetItem(f"👤 {socio}")
            item_socio.setFlags(item_socio.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_remitos.setItem(row, 2, item_socio)

            # Col 3: Proveedor Origen
            item_prov = QTableWidgetItem(f"🏢 {proveedor}")
            item_prov.setFlags(item_prov.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_remitos.setItem(row, 3, item_prov)

            # Col 4: Ref. Pedido
            item_ped = QTableWidgetItem(cod_pedido)
            item_ped.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_ped.setForeground(QColor("#475569"))
            item_ped.setFlags(item_ped.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_remitos.setItem(row, 4, item_ped)

            # Col 5: Mercadería / Resumen
            item_res = QTableWidgetItem(resumen)
            item_res.setToolTip(resumen)
            item_res.setFlags(item_res.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_remitos.setItem(row, 5, item_res)

            # Col 6: Total Unidades
            item_tot = QTableWidgetItem(f"{total_unid} u.")
            item_tot.setFont(font_bold)
            item_tot.setForeground(QColor("#1e40af"))
            item_tot.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_tot.setFlags(item_tot.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_remitos.setItem(row, 6, item_tot)

            # Col 7: Botón de Acción PDF
            btn_ver = QPushButton("📥 Ver PDF")
            btn_ver.setObjectName("btn_ver_pdf")
            btn_ver.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_ver.setToolTip(f"Abrir el PDF oficial del remito {cod_remito}")
            btn_ver.clicked.connect(lambda _, r_item=r: self.solicitar_abrir_pdf.emit(r_item))
            self.tabla_remitos.setCellWidget(row, 7, btn_ver)

        self.tabla_remitos.blockSignals(False)

        # Actualizar resumen
        self.lbl_resumen_info.setText(
            f"Mostrando {len(remitos)} remito(s) emitido(s)  |  Total acumulado: {total_unidades_gral} unidades entregadas"
        )

    def _al_doble_click_fila(self, row, col):
        if 0 <= row < len(self.remitos_actuales):
            self.solicitar_abrir_pdf.emit(self.remitos_actuales[row])
