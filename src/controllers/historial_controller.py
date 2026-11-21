class HistorialController:
    """Controla la pantalla de Historial de Pedidos del socio."""

    def __init__(self, vista, modelo):
        self.vista = vista
        self.modelo = modelo
        self.id_socio = None

        if hasattr(self.vista, 'btn_refrescar_historial'):
            self.vista.btn_refrescar_historial.clicked.connect(self.inicializar)

    def set_socio(self, id_socio):
        """Define el socio cuyo historial se mostrará."""
        self.id_socio = id_socio

    def inicializar(self):
        """Consulta y muestra el historial de pedidos del socio actual."""
        if not self.id_socio:
            return
        try:
            historial = self.modelo.obtener_historial_pedidos(self.id_socio)
            self.vista.cargar_historial_pedidos(historial)
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"Error al cargar el historial: {str(e)}")
