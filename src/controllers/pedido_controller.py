class PedidoController:
    def __init__(self, vista, modelo, on_pedido_creado=None):
        self.vista = vista
        self.modelo = modelo
        self.on_pedido_creado = on_pedido_creado
        
        # Conectar eventos de la vista
        if hasattr(self.vista, 'btn_confirmar'):
            self.vista.btn_confirmar.clicked.connect(self.confirmar_pedido)
        if hasattr(self.vista, 'cmb_filtro_proveedor'):
            self.vista.cmb_filtro_proveedor.currentIndexChanged.connect(self.filtrar_catalogo)

    def inicializar(self):
        """Carga los proveedores en el filtro y el catálogo completo de artículos."""
        proveedores = self.modelo.obtener_proveedores()
        self.vista.cargar_proveedores_filtro(proveedores)
        
        articulos = self.modelo.obtener_catalogo_articulos()
        self.vista.cargar_articulos(articulos)

    def filtrar_catalogo(self):
        """Filtra el catálogo según el proveedor seleccionado en el combo."""
        id_proveedor = self.vista.cmb_filtro_proveedor.currentData()
        articulos = self.modelo.obtener_catalogo_articulos(id_proveedor)
        self.vista.renderizar_tabla(articulos)

    def validar_entradas(self, items_pedido):
        """Valida que haya artículos seleccionados con cantidades válidas."""
        if not items_pedido:
            return False, "Debes ingresar al menos una cantidad para confirmar tu pedido."

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
            
            self.vista.mostrar_mensaje_exito(f"¡Tu Pedido #{id_pedido} fue registrado con éxito!\nEl ejecutivo de cuentas ha sido notificado.")
            self.vista.limpiar_formulario()
            
            if self.on_pedido_creado:
                self.on_pedido_creado()
                
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"Error al registrar pedido: {str(e)}")
