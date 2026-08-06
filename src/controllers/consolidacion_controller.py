import os

class ConsolidacionController:
    def __init__(self, vista, modelo):
        self.vista = vista
        self.modelo = modelo
        
        # Conectar eventos de la vista a los métodos del controlador si están disponibles
        if hasattr(self.vista, 'btn_seleccionar_archivo'):
            self.vista.btn_seleccionar_archivo.clicked.connect(self.seleccionar_archivo)
        if hasattr(self.vista, 'btn_consolidar'):
            self.vista.btn_consolidar.clicked.connect(self.procesar_consolidacion)

    def seleccionar_archivo(self):
        """
        Abre el explorador de archivos, lee el archivo mediante pandas
        y dibuja las cabeceras y las filas en la grilla de vista previa.
        Muestra alertas si el parsing falla.
        """
        ruta_archivo = self.vista.abrir_dialogo_archivo()
        if not ruta_archivo:
            return

        # Actualizar etiqueta con el nombre del archivo seleccionado
        nombre_archivo = os.path.basename(ruta_archivo)
        self.vista.actualizar_archivo_seleccionado(nombre_archivo)

        # Leer la vista previa (primeras 10 filas) desde el modelo
        headers, filas, error = self.modelo.leer_vista_previa(ruta_archivo)

        if error:
            self.vista.mostrar_mensaje_error(error)
            # Restablecer estado de la vista
            self.vista.actualizar_archivo_seleccionado("Ningún archivo seleccionado")
            self.vista.cargar_tabla_previa([], [])
        else:
            # Cargar los datos leídos en la tabla
            self.vista.cargar_tabla_previa(headers, filas)

    def procesar_consolidacion(self):
        """
        Slot para el botón de consolidar y actualizar catálogo.
        Iniciará el parsing y la carga a la base de datos de SQLite.
        """
        pass
