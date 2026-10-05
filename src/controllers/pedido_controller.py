class PedidoController:
    def __init__(self, vista, modelo, on_pedido_creado=None):
        self.vista = vista
        self.modelo = modelo
        self.on_pedido_creado = on_pedido_creado
        
        # Conectar eventos de la vista
        if hasattr(self.vista, 'btn_confirmar'):
            self.vista.btn_confirmar.clicked.connect(self.confirmar_pedido)

    def inicializar(self):
        """Carga los socios disponibles y el catálogo completo de artículos organizado por proveedor."""
        socios = self.modelo.obtener_socios()
        self.vista.cargar_socios_selector(socios)
        
        articulos = self.modelo.obtener_catalogo_articulos()
        self.vista.cargar_articulos(articulos)

    def validar_entradas(self, items_pedido):
        """Valida que haya artículos seleccionados con cantidades válidas."""
        if not items_pedido:
            return False, "Debes ingresar al menos una cantidad en cualquiera de los proveedores para confirmar tu pedido."

        for item in items_pedido:
            cant = item.get('cantidad', 0)
            detalle = item.get('detalle', 'Artículo')
            if cant <= 0:
                return False, f"La cantidad para '{detalle}' debe ser mayor a cero."

        return True, None

    def confirmar_pedido(self):
        """Valida el pedido y lo registra en la base de datos."""
        id_socio = self.vista.obtener_id_socio()
        items_seleccionados = self.vista.obtener_articulos_seleccionados()

        es_valido, error_msg = self.validar_entradas(items_seleccionados)
        if not es_valido:
            self.vista.mostrar_mensaje_error(error_msg)
            return

        try:
            articulos_para_registro = [(item['id_articulo'], item['cantidad']) for item in items_seleccionados]
            id_pedido = self.modelo.registrar_pedido(id_socio, articulos_para_registro)
            
            self.vista.mostrar_mensaje_exito(
                f"¡Pedido #{id_pedido} registrado con éxito!\n\n"
                f"• {len(articulos_para_registro)} productos solicitados.\n"
                f"• El Ejecutivo de Cuentas ha sido notificado para su consolidación."
            )
            self.vista.limpiar_formulario()
            
            if self.on_pedido_creado:
                self.on_pedido_creado()
                
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"Error al registrar pedido: {str(e)}")
