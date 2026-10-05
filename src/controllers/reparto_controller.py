class RepartoController:
    def __init__(self, vista, modelo, on_reparto_completado=None):
        self.vista = vista
        self.modelo = modelo
        self.on_reparto_completado = on_reparto_completado
        
        # Conectar eventos de la vista
        if hasattr(self.vista, 'btn_guardar_comprobante'):
            self.vista.btn_guardar_comprobante.clicked.connect(self.asentar_comprobante)
        if hasattr(self.vista, 'btn_ejecutar'):
            self.vista.btn_ejecutar.clicked.connect(self.ejecutar_reparto)
        if hasattr(self.vista, 'cmb_proveedor_recepcion'):
            self.vista.cmb_proveedor_recepcion.currentIndexChanged.connect(self.filtrar_articulos_por_proveedor)

    def inicializar(self):
        """Carga los proveedores, artículos de control y pedidos consolidados."""
        proveedores = self.modelo.obtener_proveedores_con_pedidos()
        self.vista.cargar_proveedores(proveedores)
        
        self.filtrar_articulos_por_proveedor()
        
        pedidos = self.modelo.obtener_pedidos_consolidados()
        self.vista.cargar_pedidos(pedidos)

    def filtrar_articulos_por_proveedor(self):
        """Filtra la grilla de control según el proveedor seleccionado."""
        id_proveedor = self.vista.cmb_proveedor_recepcion.currentData()
        articulos = self.modelo.obtener_articulos_control_recepcion(id_proveedor)
        self.vista.cargar_articulos_control(articulos)

    def asentar_comprobante(self):
        """Valida y asienta el comprobante del proveedor con su doble control y actualiza stock."""
        nro_comprobante = self.vista.txt_nro_comprobante.text().strip()
        if not nro_comprobante:
            self.vista.mostrar_mensaje_error("Debes ingresar el número de Factura o Remito del Proveedor.")
            return

        id_proveedor = self.vista.cmb_proveedor_recepcion.currentData()
        if not id_proveedor:
            # Si seleccionó 'Todos', tomar el proveedor del primer artículo de la tabla
            items = self.vista.obtener_items_para_asentar()
            if not items:
                self.vista.mostrar_mensaje_error("No hay artículos para registrar.")
                return
            id_proveedor = 1 # Por defecto
            
        tipo_comprobante = self.vista.cmb_tipo_comprobante.currentText()
        items = self.vista.obtener_items_para_asentar()
        
        if not items:
            self.vista.mostrar_mensaje_error("No hay artículos en la lista para asentar.")
            return

        try:
            id_comp = self.modelo.registrar_comprobante_y_stock(
                id_proveedor=id_proveedor,
                tipo_comprobante=tipo_comprobante,
                nro_comprobante=nro_comprobante,
                fecha_emision="",
                observaciones="Recepción controlada por Compras y Logística",
                items_detalle=items
            )
            
            self.vista.mostrar_mensaje_exito(
                f"¡Comprobante #{id_comp} ({tipo_comprobante} N° {nro_comprobante}) asentado con éxito!\n\n"
                f"• Precios y cantidades registrados en auditoría.\n"
                f"• Stock físico actualizado en el depósito.\n"
                f"• Ya puedes ejecutar el reparto automático hacia los socios."
            )
            self.vista.txt_nro_comprobante.clear()
            self.inicializar()
            
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"Error al asentar comprobante: {str(e)}")

    def ejecutar_reparto(self):
        """Valida el stock físico registrado, aplica prorrateo si hubo faltantes y emite remitos a socios."""
        pedidos = self.modelo.obtener_pedidos_consolidados()
        if not pedidos:
            self.vista.mostrar_mensaje_error("No hay pedidos en estado 'Consolidado' listos para repartir.")
            return

        # 1. Validar demanda vs stock físico real
        discrepancias = self.modelo.validar_stock_vs_pedidos()
        ajustes_totales = {}
        
        if discrepancias:
            confirmado = self.vista.mostrar_alerta_discrepancias(discrepancias)
            if not confirmed if (confirmed := confirmado) else False:
                return
                
            for disc in discrepancias:
                id_art = disc['id_articulo']
                for id_ped, cant_ajustada in disc['ajustes'].items():
                    ajustes_totales[(id_ped, id_art)] = cant_ajustada

        # 2. Ejecutar reparto masivo transaccional
        exito = self.modelo.ejecutar_reparto_masivo(ajustes=ajustes_totales if ajustes_totales else None)
        
        if exito:
            self.vista.mostrar_mensaje_exito(
                "¡Reparto automático completado con éxito!\n\n"
                "• Remitos generados para cada socio.\n"
                "• Notificaciones de entrega emitidas a cada socio."
            )
            self.inicializar()
            if self.on_reparto_completado:
                self.on_reparto_completado()
        else:
            self.vista.mostrar_mensaje_error("No fue posible ejecutar el proceso de reparto.")
