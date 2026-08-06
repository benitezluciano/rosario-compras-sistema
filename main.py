import sys
from PyQt6.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QWidget, 
    QListWidget, 
    QStackedWidget, 
    QHBoxLayout,
    QLabel,
    QVBoxLayout
)

from src.database import inicializar_db
from src.views.pedido_view import PedidoView
from src.models.pedido_model import PedidoModel
from src.controllers.pedido_controller import PedidoController
from src.views.reparto_view import RepartoView
from src.models.reparto_model import RepartoModel
from src.controllers.reparto_controller import RepartoController
from src.views.consolidacion_view import ConsolidacionView
from src.models.consolidacion_model import ConsolidacionModel
from src.controllers.consolidacion_controller import ConsolidacionController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rosario Compras - Sistema de Gestión")
        self.resize(1000, 700) # Un poco más ancho para albergar cómodamente el menú y la tabla
        
        # 1. Crear el widget central y su layout horizontal
        widget_central = QWidget()
        layout_principal = QHBoxLayout(widget_central)
        self.setCentralWidget(widget_central)
        
        # 2. Menú lateral izquierdo (QListWidget)
        self.menu_lateral = QListWidget()
        self.menu_lateral.addItem("Cargar Pedido")
        self.menu_lateral.addItem("Reparto Automático")
        self.menu_lateral.addItem("Consolidar Planillas")
        self.menu_lateral.setMaximumWidth(200)
        layout_principal.addWidget(self.menu_lateral)
        
        # 3. Contenedor de pantallas derecho (QStackedWidget)
        self.stacked_pantallas = QStackedWidget()
        layout_principal.addWidget(self.stacked_pantallas)
        
        # 4. Instanciar MVC para Caso de Uso 1 (Carga de Pedido)
        self.modelo_pedido = PedidoModel()
        self.vista_pedido = PedidoView()
        self.controlador_pedido = PedidoController(self.vista_pedido, self.modelo_pedido)
        
        # Inicializar el controlador para cargar datos de SQLite en la vista
        self.controlador_pedido.inicializar()
        
        # Añadir vista de pedidos al QStackedWidget (Índice 0)
        self.stacked_pantallas.addWidget(self.vista_pedido)
        
        # 5. Instanciar MVC para Caso de Uso 2 (Reparto Automático)
        self.modelo_reparto = RepartoModel()
        self.vista_reparto = RepartoView()
        self.controlador_reparto = RepartoController(self.vista_reparto, self.modelo_reparto)
        
        # Inicializar el controlador para cargar datos de SQLite en la vista de reparto
        self.controlador_reparto.inicializar()
        
        # Añadir vista de reparto al QStackedWidget (Índice 1)
        self.stacked_pantallas.addWidget(self.vista_reparto)
        
        # 6. Instanciar MVC para Caso de Uso 3 (Consolidación de Planillas)
        self.modelo_consolidacion = ConsolidacionModel()
        self.vista_consolidacion = ConsolidacionView()
        self.controlador_consolidacion = ConsolidacionController(self.vista_consolidacion, self.modelo_consolidacion)
        
        # Añadir vista de consolidación al QStackedWidget (Índice 2)
        self.stacked_pantallas.addWidget(self.vista_consolidacion)
        
        # 6. Conectar navegación del menú lateral con las pantallas
        self.menu_lateral.currentRowChanged.connect(self.stacked_pantallas.setCurrentIndex)
        
        # Seleccionar el primer elemento del menú por defecto al arrancar
        self.menu_lateral.setCurrentRow(0)

if __name__ == '__main__':
    # Inicializar la base de datos al arrancar la aplicación
    inicializar_db()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())