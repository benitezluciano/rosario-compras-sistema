from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QAbstractItemView, QFrame
)
from PyQt6.QtCore import Qt
from src.models.proveedor_model import ProveedorModel
from src.views.proveedor_form_dialog import ProveedorFormDialog

class ProveedoresDialog(QDialog):
    def __init__(self, usuario_actual, on_proveedores_changed=None, on_solicitar_lista=None, parent=None):
        super().__init__(parent)
        self.usuario_actual = usuario_actual
        self.on_proveedores_changed = on_proveedores_changed
        self.on_solicitar_lista = on_solicitar_lista
        self.modelo = ProveedorModel()
        self.proveedores_data = []
        
        self.setWindowTitle("Gestión y Administración de Proveedores - Rosario Compras")
        self.resize(880, 520)
        
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        
        # --- Cabecera con Título y Buscador ---
        header_layout = QHBoxLayout()
        lbl_titulo = QLabel("🏢 Red de Proveedores Registrados")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e293b;")
        header_layout.addWidget(lbl_titulo)
        
        header_layout.addStretch()
        
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar por nombre, email, responsable...")
        self.txt_buscar.setFixedWidth(260)
        self.txt_buscar.textChanged.connect(self.filtrar_tabla)
        header_layout.addWidget(self.txt_buscar)
        
        layout.addLayout(header_layout)
        
        # --- Tabla de Proveedores ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Nombre / Razón Social", "Correo Electrónico", 
            "Teléfono", "Dirección", "Ejecutivo Responsable", "Artículos"
        ])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background-color: white;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                font-weight: bold;
                color: #334155;
                padding: 6px;
                border: 1px solid #e2e8f0;
            }
        """)
        
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        self.tabla.doubleClicked.connect(self.editar_proveedor)
        layout.addWidget(self.tabla)
        
        # --- Barra de Botones de Acción ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.btn_nuevo = QPushButton("➕ Nuevo Proveedor")
        self.btn_nuevo.setStyleSheet("background-color: #16a34a; color: white; padding: 7px 14px; font-weight: bold; border-radius: 4px;")
        self.btn_nuevo.clicked.connect(self.nuevo_proveedor)
        btn_layout.addWidget(self.btn_nuevo)
        
        self.btn_editar = QPushButton("✏️ Editar")
        self.btn_editar.setStyleSheet("background-color: #2563eb; color: white; padding: 7px 14px; font-weight: bold; border-radius: 4px;")
        self.btn_editar.clicked.connect(self.editar_proveedor)
        btn_layout.addWidget(self.btn_editar)
        
        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.setStyleSheet("background-color: #dc2626; color: white; padding: 7px 14px; font-weight: bold; border-radius: 4px;")
        self.btn_eliminar.clicked.connect(self.eliminar_proveedor)
        btn_layout.addWidget(self.btn_eliminar)
        
        self.btn_solicitar_lista = QPushButton("📧 Solicitar Lista")
        self.btn_solicitar_lista.setStyleSheet("background-color: #d97706; color: white; padding: 7px 14px; font-weight: bold; border-radius: 4px;")
        self.btn_solicitar_lista.clicked.connect(self.solicitar_lista)
        btn_layout.addWidget(self.btn_solicitar_lista)
        
        btn_layout.addStretch()
        
        self.btn_refrescar = QPushButton("🔄 Actualizar")
        self.btn_refrescar.setStyleSheet("padding: 7px 14px; border-radius: 4px;")
        self.btn_refrescar.clicked.connect(self.cargar_datos)
        btn_layout.addWidget(self.btn_refrescar)
        
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.setStyleSheet("padding: 7px 18px; border-radius: 4px;")
        self.btn_cerrar.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_cerrar)
        
        layout.addLayout(btn_layout)

    def cargar_datos(self):
        self.proveedores_data = self.modelo.obtener_todos()
        self.renderizar_tabla(self.proveedores_data)

    def renderizar_tabla(self, items):
        self.tabla.setRowCount(len(items))
        for row, prov in enumerate(items):
            item_id = QTableWidgetItem(str(prov["id_proveedor"]))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(row, 0, item_id)
            
            self.tabla.setItem(row, 1, QTableWidgetItem(prov["nombre"]))
            self.tabla.setItem(row, 2, QTableWidgetItem(prov.get("email") or "-"))
            self.tabla.setItem(row, 3, QTableWidgetItem(prov.get("telefono") or "-"))
            self.tabla.setItem(row, 4, QTableWidgetItem(prov.get("direccion") or "-"))
            self.tabla.setItem(row, 5, QTableWidgetItem(prov.get("ejecutivo_nombre") or "-"))
            
            total_art = prov.get("total_articulos", 0)
            item_art = QTableWidgetItem(f"{total_art} arts.")
            item_art.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(row, 6, item_art)

    def filtrar_tabla(self, texto):
        texto = texto.strip().lower()
        if not texto:
            self.renderizar_tabla(self.proveedores_data)
            return
            
        filtrados = []
        for p in self.proveedores_data:
            nombre = (p.get("nombre") or "").lower()
            email = (p.get("email") or "").lower()
            ejecutivo = (p.get("ejecutivo_nombre") or "").lower()
            direccion = (p.get("direccion") or "").lower()
            telefono = (p.get("telefono") or "").lower()
            
            if texto in nombre or texto in email or texto in ejecutivo or texto in direccion or texto in telefono:
                filtrados.append(p)
                
        self.renderizar_tabla(filtrados)

    def _obtener_proveedor_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            return None
        id_item = self.tabla.item(fila, 0)
        if not id_item:
            return None
        id_prov = int(id_item.text())
        for p in self.proveedores_data:
            if p["id_proveedor"] == id_prov:
                return p
        return None

    def nuevo_proveedor(self):
        ejecutivos = self.modelo.obtener_ejecutivos()
        dialog = ProveedorFormDialog(
            ejecutivos=ejecutivos, 
            proveedor=None, 
            id_ejecutivo_actual=self.usuario_actual.get("id"),
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos = dialog.obtener_datos()
            exito, res = self.modelo.crear_proveedor(
                nombre=datos["nombre"],
                email=datos["email"],
                telefono=datos["telefono"],
                direccion=datos["direccion"],
                id_user=datos["id_user"]
            )
            if exito:
                QMessageBox.information(self, "Éxito", f"Proveedor '{datos['nombre']}' registrado exitosamente.")
                self.cargar_datos()
                if self.on_proveedores_changed:
                    self.on_proveedores_changed()
            else:
                QMessageBox.critical(self, "Error", str(res))

    def editar_proveedor(self):
        prov = self._obtener_proveedor_seleccionado()
        if not prov:
            QMessageBox.warning(self, "Atención", "Selecciona un proveedor de la tabla para editar.")
            return

        ejecutivos = self.modelo.obtener_ejecutivos()
        dialog = ProveedorFormDialog(
            ejecutivos=ejecutivos, 
            proveedor=prov, 
            id_ejecutivo_actual=self.usuario_actual.get("id"),
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            datos = dialog.obtener_datos()
            exito, mensaje = self.modelo.actualizar_proveedor(
                id_proveedor=prov["id_proveedor"],
                nombre=datos["nombre"],
                email=datos["email"],
                telefono=datos["telefono"],
                direccion=datos["direccion"],
                id_user=datos["id_user"]
            )
            if exito:
                QMessageBox.information(self, "Éxito", mensaje)
                self.cargar_datos()
                if self.on_proveedores_changed:
                    self.on_proveedores_changed()
            else:
                QMessageBox.critical(self, "Error", mensaje)

    def eliminar_proveedor(self):
        prov = self._obtener_proveedor_seleccionado()
        if not prov:
            QMessageBox.warning(self, "Atención", "Selecciona un proveedor de la tabla para eliminar.")
            return

        resp = QMessageBox.question(
            self, 
            "Confirmar Eliminación", 
            f"¿Estás seguro de que deseas eliminar al proveedor '{prov['nombre']}'?\n"
            f"Se eliminarán también sus artículos asociados en el catálogo.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            exito, mensaje = self.modelo.eliminar_proveedor(prov["id_proveedor"])
            if exito:
                QMessageBox.information(self, "Eliminado", mensaje)
                self.cargar_datos()
                if self.on_proveedores_changed:
                    self.on_proveedores_changed()
            else:
                QMessageBox.critical(self, "No permitido", mensaje)

    def solicitar_lista(self):
        prov = self._obtener_proveedor_seleccionado()
        if not prov:
            QMessageBox.warning(self, "Atención", "Selecciona un proveedor de la tabla para solicitarle la lista.")
            return

        if self.on_solicitar_lista:
            self.on_solicitar_lista(prov["id_proveedor"])
