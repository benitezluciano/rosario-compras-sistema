import sys
from PyQt6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget, 
    QListWidget, 
    QStackedWidget, 
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFrame
)
from PyQt6.QtCore import Qt

from src.database import inicializar_db

# Modelos
from src.models.auth_model import AuthModel
from src.models.catalogo_model import CatalogoModel
from src.models.pedido_model import PedidoModel
from src.models.consolidacion_model import ConsolidacionModel
from src.models.reparto_model import RepartoModel
from src.models.notificacion_model import NotificacionModel

# Vistas
from src.views.login_view import LoginView
from src.views.catalogo_view import CatalogoView
from src.views.pedido_view import PedidoView
from src.views.consolidacion_view import ConsolidacionView
from src.views.reparto_view import RepartoView
from src.views.notificaciones_dialog import NotificacionesDialog

# Controladores
from src.controllers.auth_controller import AuthController
from src.controllers.catalogo_controller import CatalogoController
from src.controllers.pedido_controller import PedidoController
from src.controllers.consolidacion_controller import ConsolidacionController
from src.controllers.reparto_controller import RepartoController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rosario Compras - Sistema de Gestión")
        self.resize(1100, 750)
        
        self.usuario_actual = None
        self.modelo_notif = NotificacionModel()
        
        # Contenedor raíz con QStackedWidget para alternar entre Login y Dashboard
        self.root_stack = QStackedWidget()
        self.setCentralWidget(self.root_stack)
        
        # 1. PANTALLA DE LOGIN
        self.modelo_auth = AuthModel()
        self.vista_login = LoginView()
        self.controlador_auth = AuthController(
            self.vista_login, 
            self.modelo_auth, 
            on_login_success=self.al_iniciar_sesion
        )
        
        login_container = QWidget()
        login_layout = QHBoxLayout(login_container)
        login_layout.addStretch()
        login_layout.addWidget(self.vista_login)
        login_layout.addStretch()
        self.root_stack.addWidget(login_container) # Índice 0: Login
        
        # 2. PANTALLA PRINCIPAL (DASHBOARD)
        self.crear_pantalla_dashboard()
        self.root_stack.addWidget(self.widget_dashboard) # Índice 1: Dashboard
        
        self.root_stack.setCurrentIndex(0)

    def crear_pantalla_dashboard(self):
        """Construye la interfaz principal con barra superior y navegación modular."""
        self.widget_dashboard = QWidget()
        dashboard_layout = QVBoxLayout(self.widget_dashboard)
        dashboard_layout.setContentsMargins(15, 15, 15, 15)
        dashboard_layout.setSpacing(10)
        
        # --- Barra superior de Sesión y Notificaciones ---
        barra_sesion = QFrame()
        barra_sesion.setFrameShape(QFrame.Shape.StyledPanel)
        barra_sesion.setStyleSheet("background-color: #f5f5f5; border-radius: 6px; padding: 6px;")
        layout_sesion = QHBoxLayout(barra_sesion)
        layout_sesion.setContentsMargins(10, 5, 10, 5)
        
        self.lbl_usuario_info = QLabel("Conectado como: -")
        self.lbl_usuario_info.setStyleSheet("font-weight: bold; font-size: 13px; color: #333;")
        layout_sesion.addWidget(self.lbl_usuario_info)
        
        layout_sesion.addStretch()
        
        # Botón de Notificaciones con Badge
        self.btn_notificaciones = QPushButton("🔔 Notificaciones (0)")
        self.btn_notificaciones.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_notificaciones.clicked.connect(self.abrir_notificaciones)
        layout_sesion.addWidget(self.btn_notificaciones)
        
        # Botón Cerrar Sesión
        self.btn_logout = QPushButton("Cerrar Sesión")
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; 
                color: white; 
                font-weight: bold; 
                border-radius: 4px; 
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.btn_logout.clicked.connect(self.cerrar_sesion)
        layout_sesion.addWidget(self.btn_logout)
        
        dashboard_layout.addWidget(barra_sesion)
        
        # --- Contenedor Principal (Menú Lateral + Pantallas) ---
        contenedor_cuerpo = QWidget()
        layout_cuerpo = QHBoxLayout(contenedor_cuerpo)
        layout_cuerpo.setContentsMargins(0, 0, 0, 0)
        
        self.menu_lateral = QListWidget()
        self.menu_lateral.setMaximumWidth(240)
        self.menu_lateral.setStyleSheet("""
            QListWidget {
                font-size: 13px;
                border: 1px solid #ddd;
                border-radius: 6px;
            }
            QListWidget::item {
                padding: 12px 10px;
            }
            QListWidget::item:selected {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
            }
        """)
        layout_cuerpo.addWidget(self.menu_lateral)
        
        self.stacked_pantallas = QStackedWidget()
        layout_cuerpo.addWidget(self.stacked_pantallas)
        dashboard_layout.addWidget(contenedor_cuerpo)
        
        # --- Instanciar Modelos, Vistas y Controladores ---
        # Paso 1 y 2: Catálogo y Listas de Proveedores
        self.modelo_catalogo = CatalogoModel()
        self.vista_catalogo = CatalogoView()
        self.controlador_catalogo = CatalogoController(
            self.vista_catalogo, 
            self.modelo_catalogo,
            on_catalogo_updated=self.al_actualizar_catalogo
        )
        self.stacked_pantallas.addWidget(self.vista_catalogo) # Índice 0
        
        # Paso 3: Carga Digital de Pedidos
        self.modelo_pedido = PedidoModel()
        self.vista_pedido = PedidoView()
        self.controlador_pedido = PedidoController(
            self.vista_pedido, 
            self.modelo_pedido,
            on_pedido_creado=self.al_crear_pedido
        )
        self.stacked_pantallas.addWidget(self.vista_pedido) # Índice 1
        
        # Paso 4: Consolidación y Pedidos a Proveedor
        self.modelo_consolidacion = ConsolidacionModel()
        self.vista_consolidacion = ConsolidacionView()
        self.controlador_consolidacion = ConsolidacionController(
            self.vista_consolidacion, 
            self.modelo_consolidacion,
            on_pedidos_consolidados=self.al_consolidar_pedidos
        )
        self.stacked_pantallas.addWidget(self.vista_consolidacion) # Índice 2
        
        # Paso 5: Recepción y Reparto Automático
        self.modelo_reparto = RepartoModel()
        self.vista_reparto = RepartoView()
        self.controlador_reparto = RepartoController(
            self.vista_reparto, 
            self.modelo_reparto,
            on_reparto_completado=self.al_completar_reparto
        )
        self.stacked_pantallas.addWidget(self.vista_reparto) # Índice 3
        
        self.menu_lateral.currentRowChanged.connect(self.navegar_pantalla)

    def al_iniciar_sesion(self, usuario):
        """Configura el entorno de trabajo según el rol del usuario autenticado."""
        self.usuario_actual = usuario
        rol = usuario.get('role', 'socio')
        nombre = usuario.get('nombre', '')
        
        rol_display = "Socio" if rol == "socio" else ("Ejecutivo de Cuentas" if rol == "ejecutivo" else "Administrador")
        self.lbl_usuario_info.setText(f"👤 {nombre} | Rol: {rol_display}")
        
        self.vista_pedido.establecer_socio_actual(usuario['id'], nombre)
        self.actualizar_badge_notificaciones()
        
        self.menu_lateral.blockSignals(True)
        self.menu_lateral.clear()
        
        if rol == 'socio':
            # Socio: Solo Cargar Pedido
            self.menu_lateral.addItem("🛍️ Cargar Pedido")
            self.controlador_pedido.inicializar()
            self.menu_lateral.blockSignals(False)
            self.menu_lateral.setCurrentRow(0)
            self.stacked_pantallas.setCurrentIndex(1) # Vista Pedido
        else:
            # Ejecutivo y Admin: Circuito Completo
            self.menu_lateral.addItem("📑 1. Listas de Proveedores")
            self.menu_lateral.addItem("🛍️ 2. Cargar Pedido")
            self.menu_lateral.addItem("📦 3. Consolidar y Enviar a Proveedores")
            self.menu_lateral.addItem("🚚 4. Recepción y Reparto Automático")
            
            self.controlador_catalogo.inicializar()
            self.controlador_pedido.inicializar()
            self.controlador_consolidacion.inicializar()
            self.controlador_reparto.inicializar()
            
            self.menu_lateral.blockSignals(False)
            self.menu_lateral.setCurrentRow(0)
            self.stacked_pantallas.setCurrentIndex(0) # Vista Catálogo
            
        self.root_stack.setCurrentIndex(1)

    def navegar_pantalla(self, row):
        """Controla el cambio de pantallas según la selección del menú."""
        if row < 0 or not self.usuario_actual:
            return
            
        rol = self.usuario_actual.get('role', 'socio')
        if rol == 'socio':
            self.stacked_pantallas.setCurrentIndex(1) # Vista Pedido
            self.controlador_pedido.inicializar()
        else:
            # Ejecutivo/Admin: mapa de filas a índices del stack
            self.stacked_pantallas.setCurrentIndex(row)
            if row == 0:
                self.controlador_catalogo.inicializar()
            elif row == 1:
                self.controlador_pedido.inicializar()
            elif row == 2:
                self.controlador_consolidacion.inicializar()
            elif row == 3:
                self.controlador_reparto.inicializar()

    def actualizar_badge_notificaciones(self):
        """Actualiza el contador visual de notificaciones pendientes."""
        if not self.usuario_actual:
            return
        pendientes = self.modelo_notif.contar_no_leidas(self.usuario_actual['id'], self.usuario_actual['role'])
        self.btn_notificaciones.setText(f"🔔 Notificaciones ({pendientes})")

    def abrir_notificaciones(self):
        """Abre el diálogo modal de notificaciones."""
        if not self.usuario_actual:
            return
        dialog = NotificacionesDialog(self.usuario_actual, self)
        dialog.exec()
        self.actualizar_badge_notificaciones()

    def al_actualizar_catalogo(self):
        self.controlador_pedido.inicializar()

    def al_crear_pedido(self):
        self.actualizar_badge_notificaciones()
        if self.usuario_actual and self.usuario_actual['role'] in ['ejecutivo', 'admin']:
            self.controlador_consolidacion.inicializar()

    def al_consolidar_pedidos(self):
        self.actualizar_badge_notificaciones()
        self.controlador_reparto.inicializar()

    def al_completar_reparto(self):
        self.actualizar_badge_notificaciones()

    def cerrar_sesion(self):
        self.usuario_actual = None
        self.vista_login.limpiar_campos()
        self.root_stack.setCurrentIndex(0)

if __name__ == '__main__':
    inicializar_db()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())