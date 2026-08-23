from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton
from PyQt6.QtCore import Qt
from src.models.notificacion_model import NotificacionModel

class NotificacionesDialog(QDialog):
    def __init__(self, usuario, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.modelo_notif = NotificacionModel()
        
        self.setWindowTitle("Centro de Notificaciones")
        self.resize(550, 420)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        # Título
        lbl_titulo = QLabel("🔔 Centro de Notificaciones y Avisos")
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(lbl_titulo)
        
        # Lista de notificaciones
        self.lista_notificaciones = QListWidget()
        self.lista_notificaciones.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: white;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
        """)
        layout.addWidget(self.lista_notificaciones)
        
        # Botones inferiores
        layout_btn = QHBoxLayout()
        
        self.btn_marcar_leidas = QPushButton("Marcar todas como leídas")
        self.btn_marcar_leidas.setStyleSheet("background-color: #3498db; color: white; padding: 6px 12px; font-weight: bold; border-radius: 4px;")
        self.btn_marcar_leidas.clicked.connect(self.marcar_leidas)
        layout_btn.addWidget(self.btn_marcar_leidas)
        
        layout_btn.addStretch()
        
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.setStyleSheet("padding: 6px 16px; border-radius: 4px;")
        self.btn_cerrar.clicked.connect(self.accept)
        layout_btn.addWidget(self.btn_cerrar)
        
        layout.addLayout(layout_btn)
        
        self.cargar_notificaciones()

    def cargar_notificaciones(self):
        self.lista_notificaciones.clear()
        notifs = self.modelo_notif.obtener_notificaciones_usuario(
            self.usuario['id'], 
            self.usuario['role']
        )
        
        if not notifs:
            item = QListWidgetItem("No tienes notificaciones recientes.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.lista_notificaciones.addItem(item)
            return

        for n in notifs:
            icono = "🛒" if n['tipo'] == 'nuevo_pedido' else ("📦" if n['tipo'] == 'pedido_consolidado' else "🚚")
            estado = " [NUEVA]" if n['leida'] == 0 else ""
            texto = f"{icono} {n['mensaje']}{estado}\n    🕒 {n['fecha']}"
            
            item = QListWidgetItem(texto)
            if n['leida'] == 0:
                item.setBackground(Qt.GlobalColor.lightGray)
            self.lista_notificaciones.addItem(item)

    def marcar_leidas(self):
        self.modelo_notif.marcar_todas_como_leidas(self.usuario['id'], self.usuario['role'])
        self.cargar_notificaciones()
