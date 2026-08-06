class PedidoController:
    def __init__(self, vista, modelo):
        self.vista = vista
        self.modelo = modelo
        
        # Conectar las señales/eventos de la vista a los métodos del controlador si están disponibles
        if hasattr(self.vista, 'btn_confirmar'):
            self.vista.btn_confirmar.clicked.connect(self.confirmar_pedido)

    def validar_entradas(self, items_pedido):
        """
        Valida que las cantidades ingresadas por el usuario sean enteros positivos.
        items_pedido: Lista de diccionarios/tuplas con estructura (id_articulo, cantidad, detalle_articulo)
        Retorna (True, None) si pasa las validaciones, o (False, mensaje_error) si falla.
        """
        if not items_pedido:
            return False, "El pedido debe contener al menos un artículo."

        for item in items_pedido:
            # Soporta formato de diccionario o tupla
            if isinstance(item, dict):
                id_art = item.get('id_articulo')
                cant = item.get('cantidad')
                detalle = item.get('detalle', f"Artículo #{id_art}")
            else:
                id_art, cant, detalle = item

            # Validar valor nulo o vacío
            if cant is None or str(cant).strip() == "":
                return False, f"La cantidad para el artículo '{detalle}' no puede estar vacía."

            # Validar tipo numérico entero
            try:
                cant_int = int(cant)
            except (ValueError, TypeError):
                return False, f"La cantidad para el artículo '{detalle}' debe ser un número entero válido."

            # Validar valor positivo
            if cant_int <= 0:
                return False, f"La cantidad para el artículo '{detalle}' debe ser un valor mayor a cero."

        return True, None

    def confirmar_pedido(self):
        """
        Extrae la información cargada en la vista, la valida y, de ser correcta, 
        la registra en la base de datos a través del modelo.
        """
        try:
            id_socio = self.vista.obtener_id_socio()
            items_seleccionados = self.vista.obtener_articulos_seleccionados()
        except AttributeError as e:
            # Salvaguarda si la vista aún no implementa completamente todos los getters
            self.vista.mostrar_mensaje_error("La vista no tiene implementados los métodos de lectura de datos.")
            return

        # 1. Validar entradas
        es_valido, error_msg = self.validar_entradas(items_seleccionados)
        if not es_valido:
            self.vista.mostrar_mensaje_error(error_msg)
            return

        # 2. Registrar en la base de datos
        try:
            # Formatear la información para pasarla al modelo
            articulos_para_registro = []
            for item in items_seleccionados:
                id_art = item['id_articulo'] if isinstance(item, dict) else item[0]
                cant = int(item['cantidad'] if isinstance(item, dict) else item[1])
                articulos_para_registro.append((id_art, cant))
            
            id_pedido = self.modelo.registrar_pedido(id_socio, articulos_para_registro)
            
            # 3. Notificar éxito a la vista y limpiar formulario
            self.vista.mostrar_mensaje_exito(f"Pedido #{id_pedido} registrado con éxito.")
            self.vista.limpiar_formulario()
            
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"Error de base de datos al registrar pedido: {str(e)}")

    def inicializar(self):
        """
        Carga el catálogo de artículos desde el modelo y lo envía a la vista.
        """
        articulos = self.modelo.obtener_catalogo_articulos()
        self.vista.cargar_articulos(articulos)
