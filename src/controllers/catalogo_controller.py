class CatalogoController:
    def __init__(self, vista, modelo, on_catalogo_updated=None):
        self.vista = vista
        self.modelo = modelo
        self.on_catalogo_updated = on_catalogo_updated
        
        # Conectar señales
        if hasattr(self.vista, 'btn_seleccionar_archivo'):
            self.vista.btn_seleccionar_archivo.clicked.connect(self.seleccionar_archivo)
        if hasattr(self.vista, 'btn_importar'):
            self.vista.btn_importar.clicked.connect(self.procesar_importacion)

    def inicializar(self):
        """Carga la lista de proveedores en el combo."""
        proveedores = self.modelo.obtener_proveedores()
        self.vista.cargar_proveedores(proveedores)

    def seleccionar_archivo(self):
        """Abre el archivo seleccionado y muestra la vista previa."""
        ruta = self.vista.abrir_dialogo_archivo()
        if not ruta:
            return

        headers, filas, error = self.modelo.leer_vista_previa(ruta)
        if error:
            self.vista.mostrar_mensaje_error(error)
            self.vista.limpiar_vista()
        else:
            self.vista.cargar_tabla_previa(headers, filas)

    def procesar_importacion(self):
        """Ejecuta la importación del archivo hacia la base de datos."""
        if not self.vista.ruta_archivo_actual:
            self.vista.mostrar_mensaje_error("Debes seleccionar una planilla (.xlsx o .csv) antes de procesar.")
            return

        id_proveedor = self.vista.obtener_proveedor_seleccionado()
        if not id_proveedor:
            self.vista.mostrar_mensaje_error("Debes seleccionar un proveedor asignado.")
            return

        exito, mensaje = self.modelo.importar_lista_proveedor(id_proveedor, self.vista.ruta_archivo_actual)
        if exito:
            self.vista.mostrar_mensaje_exito(mensaje)
            self.vista.limpiar_vista()
            if self.on_catalogo_updated:
                self.on_catalogo_updated()
        else:
            self.vista.mostrar_mensaje_error(mensaje)
