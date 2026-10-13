class PedidoController:
    def __init__(self, vista, modelo, on_pedido_creado=None):
        self.vista = vista
        self.modelo = modelo
        self.on_pedido_creado = on_pedido_creado
        
        # Conectar eventos de la vista
        if hasattr(self.vista, 'btn_confirmar'):
            self.vista.btn_confirmar.clicked.connect(self.confirmar_pedido)
        if hasattr(self.vista, 'cmb_socio_seleccion'):
            self.vista.cmb_socio_seleccion.currentIndexChanged.connect(self.al_cambiar_socio)
        if hasattr(self.vista, 'btn_refrescar_historial'):
            self.vista.btn_refrescar_historial.clicked.connect(self.refrescar_historial)

    def inicializar(self):
        """Carga los socios disponibles, el catálogo y sincroniza el estado activo del socio."""
        socios = self.modelo.obtener_socios()
        self.vista.cargar_socios_selector(socios)
        
        articulos = self.modelo.obtener_catalogo_articulos()
        self.vista.cargar_articulos(articulos)
        
        self.sincronizar_estado_socio()

    def al_cambiar_socio(self):
        """Maneja el cambio de socio seleccionado por un Ejecutivo o Admin."""
        self.sincronizar_estado_socio()

    def sincronizar_estado_socio(self):
        """Carga el pedido vigente (sin cerrar) y el historial de pedidos para el socio actual."""
        id_socio = self.vista.obtener_id_socio()
        if not id_socio:
            return

        # 1. Cargar o actualizar pedido vigente
        pedido_vigente = self.modelo.obtener_pedido_vigente(id_socio)
        self.vista.establecer_pedido_vigente(pedido_vigente)

        # 2. Cargar historial de pedidos
        self.refrescar_historial()

    def refrescar_historial(self):
        """Refresca la tabla de historial de pedidos."""
        id_socio = self.vista.obtener_id_socio()
        if id_socio:
            historial = self.modelo.obtener_historial_pedidos(id_socio)
            self.vista.cargar_historial_pedidos(historial)

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
        """Valida el pedido y lo registra o actualiza según corresponda."""
        id_socio = self.vista.obtener_id_socio()
        items_seleccionados = self.vista.obtener_articulos_seleccionados()

        es_valido, error_msg = self.validar_entradas(items_seleccionados)
        if not es_valido:
            self.vista.mostrar_mensaje_error(error_msg)
            return

        try:
            articulos_para_registro = [(item['id_articulo'], item['cantidad']) for item in items_seleccionados]
            
            if self.vista.id_pedido_vigente:
                # Modificar pedido vigente existente
                id_ped = self.vista.id_pedido_vigente
                cod = self.vista.codigo_pedido_vigente or f"#{id_ped}"
                self.modelo.actualizar_pedido_vigente(id_ped, articulos_para_registro)
                
                self.vista.mostrar_mensaje_exito(
                    f"¡Pedido {cod} actualizado con éxito!\n\n"
                    f"• {len(articulos_para_registro)} productos registrados en tu pedido vigente.\n"
                    f"• Puedes seguir realizando ajustes mientras continúe en estado 'Pendiente'."
                )
            else:
                # Registrar nuevo pedido
                id_pedido = self.modelo.registrar_pedido(id_socio, articulos_para_registro)
                self.vista.mostrar_mensaje_exito(
                    f"¡Pedido registrado con éxito!\n\n"
                    f"• {len(articulos_para_registro)} productos solicitados.\n"
                    f"• El Ejecutivo de Cuentas ha sido notificado para su consolidación."
                )

            self.sincronizar_estado_socio()
            
            if self.on_pedido_creado:
                self.on_pedido_creado()
                
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"Error al procesar el pedido: {str(e)}")
