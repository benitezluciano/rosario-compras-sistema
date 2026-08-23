class RepartoController:
    def __init__(self, vista, modelo, on_reparto_completado=None):
        self.vista = vista
        self.modelo = modelo
        self.on_reparto_completado = on_reparto_completado
        
        # Conectar eventos de la vista
        if hasattr(self.vista, 'btn_actualizar_stock'):
            self.vista.btn_actualizar_stock.clicked.connect(self.guardar_ingreso_stock)
        if hasattr(self.vista, 'btn_ejecutar'):
            self.vista.btn_ejecutar.clicked.connect(self.ejecutar_reparto)

    def inicializar(self):
        """Carga los artículos a recibir y los pedidos consolidados."""
        articulos = self.modelo.obtener_articulos_recepcion()
        self.vista.cargar_articulos_recepcion(articulos)
        
        pedidos = self.modelo.obtener_pedidos_consolidados()
        self.vista.cargar_pedidos(pedidos)

    def guardar_ingreso_stock(self):
        """Guarda los valores ingresados en la tabla de recepción como nuevo stock físico."""
        stock_map = self.vista.obtener_stock_ingresado()
        if not stock_map:
            self.vista.mostrar_mensaje_error("No hay artículos para actualizar.")
            return

        self.modelo.actualizar_stock_recibido(stock_map)
        self.vista.mostrar_mensaje_exito("Stock físico actualizado correctamente según la mercadería recibida.")
        self.inicializar()

    def ejecutar_reparto(self):
        """Valida stock (con prorrateo si aplica), descuenta inventario y emite remitos."""
        # 1. Guardar primero el stock cargado en la tabla de recepción
        stock_map = self.vista.obtener_stock_ingresado()
        if stock_map:
            self.modelo.actualizar_stock_recibido(stock_map)

        pedidos = self.modelo.obtener_pedidos_consolidados()
        if not pedidos:
            self.vista.mostrar_mensaje_error("No hay pedidos en estado 'Consolidado' listos para repartir.")
            return

        # 2. Validar stock vs pedidos
        discrepancias = self.modelo.validar_stock_vs_pedidos()
        ajustes_totales = {}
        
        if discrepancias:
            confirmado = self.vista.mostrar_alerta_discrepancias(discrepancias)
            if not confirmado:
                return
                
            for disc in discrepancias:
                id_art = disc['id_articulo']
                for id_ped, cant_ajustada in disc['ajustes'].items():
                    ajustes_totales[(id_ped, id_art)] = cant_ajustada

        # 3. Ejecutar reparto transaccional
        exito = self.modelo.ejecutar_reparto_masivo(ajustes=ajustes_totales if ajustes_totales else None)
        
        if exito:
            self.vista.mostrar_mensaje_exito("¡Reparto automático completado con éxito!\nSe emitieron los remitos y se notificó a los socios.")
            self.inicializar()
            if self.on_reparto_completado:
                self.on_reparto_completado()
        else:
            self.vista.mostrar_mensaje_error("No fue posible ejecutar el proceso de reparto.")
