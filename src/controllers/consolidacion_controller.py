class ConsolidacionController:
    def __init__(self, vista, modelo, on_pedidos_consolidados=None):
        self.vista = vista
        self.modelo = modelo
        self.on_pedidos_consolidados = on_pedidos_consolidados
        
        # Conectar eventos de la vista
        if hasattr(self.vista, 'btn_refrescar'):
            self.vista.btn_refrescar.clicked.connect(self.inicializar)
        if hasattr(self.vista, 'btn_exportar'):
            self.vista.btn_exportar.clicked.connect(self.exportar_planilla_general)
        if hasattr(self.vista, 'btn_exportar_proveedores'):
            self.vista.btn_exportar_proveedores.clicked.connect(self.exportar_por_proveedor)
        if hasattr(self.vista, 'btn_consolidar'):
            self.vista.btn_consolidar.clicked.connect(self.procesar_consolidacion)

    def inicializar(self):
        """Consulta los pedidos pendientes desde el modelo y los envía a la vista."""
        resumen = self.modelo.obtener_resumen_consolidado()
        self.vista.cargar_tabla_consolidado(resumen)

    def exportar_planilla_general(self):
        """Exporta la planilla global multi-hoja a Excel."""
        ruta_archivo = self.vista.abrir_dialogo_guardar()
        if not ruta_archivo:
            return

        exito, error = self.modelo.exportar_planilla(ruta_archivo)
        if not exito:
            self.vista.mostrar_mensaje_error(error)
        else:
            self.vista.mostrar_mensaje_exito(f"Planilla general exportada exitosamente en:\n{ruta_archivo}")

    def exportar_por_proveedor(self):
        """Exporta una orden de compra en Excel por cada proveedor."""
        carpeta = self.vista.abrir_dialogo_carpeta()
        if not carpeta:
            return

        exito, mensaje = self.modelo.exportar_ordenes_por_proveedor(carpeta)
        if not exito:
            self.vista.mostrar_mensaje_error(mensaje)
        else:
            self.vista.mostrar_mensaje_exito(mensaje)

    def procesar_consolidacion(self):
        """Consolida los pedidos y notifica a cada socio."""
        resumen = self.modelo.obtener_resumen_consolidado()
        if not resumen:
            self.vista.mostrar_mensaje_error("No hay pedidos pendientes para consolidar.")
            return

        confirmado = self.vista.confirmar_accion(
            "Confirmar Consolidación",
            "¿Estás seguro de consolidar todos los pedidos pendientes?\n\n"
            "• Pasarán a estado 'Consolidado'.\n"
            "• Cada socio recibirá una notificación en su panel.\n"
            "• Quedarán listos para la recepción de mercadería y reparto."
        )
        if not confirmado:
            return

        cantidad = self.modelo.marcar_pedidos_como_consolidados()
        self.vista.mostrar_mensaje_exito(f"¡Se consolidaron con éxito {cantidad} pedidos!\nLos socios han sido notificados.")
        self.inicializar()
        
        if self.on_pedidos_consolidados:
            self.on_pedidos_consolidados()
