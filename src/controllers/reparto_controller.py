from src.utils.id_generator import generar_codigo_comprobante

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
            self.vista.cmb_proveedor_recepcion.currentIndexChanged.connect(self.al_cambiar_proveedor)
        if hasattr(self.vista, 'cmb_pedido_consolidado'):
            self.vista.cmb_pedido_consolidado.currentIndexChanged.connect(self.al_cambiar_pedido_consolidado)

    def inicializar(self):
        """Carga los proveedores, pedidos consolidados y artículos de control."""
        proveedores = self.modelo.obtener_proveedores_con_pedidos()
        self.vista.cargar_proveedores(proveedores)
        
        self.al_cambiar_proveedor()

    def al_cambiar_proveedor(self):
        """Al cambiar de proveedor, actualiza el combo de pedidos consolidados y la grilla."""
        id_proveedor = self.vista.obtener_proveedor_seleccionado()
        pedidos = self.modelo.obtener_pedidos_consolidados_por_proveedor(id_proveedor)
        self.vista.cargar_pedidos_consolidados_selector(pedidos)
        self.vista.cargar_pedidos(pedidos)
        
        self.al_cambiar_pedido_consolidado()

    def al_cambiar_pedido_consolidado(self):
        """Filtra la grilla de control de recepción según el proveedor y pedido consolidado."""
        id_proveedor = self.vista.obtener_proveedor_seleccionado()
        id_pedido = self.vista.obtener_pedido_seleccionado()
        articulos = self.modelo.obtener_articulos_control_recepcion(id_proveedor, id_pedido)
        self.vista.cargar_articulos_control(articulos)

    def asentar_comprobante(self):
        """Valida y asienta el comprobante interno automático del proveedor con control y stock."""
        nro_comprobante = self.vista.txt_nro_comprobante.text().strip()
        if not nro_comprobante:
            nro_comprobante = generar_codigo_comprobante()
            self.vista.txt_nro_comprobante.setText(nro_comprobante)

        id_proveedor = self.vista.obtener_proveedor_seleccionado()
        items = self.vista.obtener_items_para_asentar()
        
        if not items:
            self.vista.mostrar_mensaje_error("No hay artículos en la lista para asentar.")
            return

        if not id_proveedor:
            id_proveedor = 1 # Proveedor por defecto si está en 'Todos'
            
        tipo_comprobante = self.vista.cmb_tipo_comprobante.currentText()

        try:
            id_comp = self.modelo.registrar_comprobante_y_stock(
                id_proveedor=id_proveedor,
                tipo_comprobante=tipo_comprobante,
                nro_comprobante=nro_comprobante,
                fecha_emision="",
                observaciones=f"Recepción interna asentada bajo código {nro_comprobante}",
                items_detalle=items
            )
            
            self.vista.mostrar_mensaje_exito(
                f"¡Entrada asentada con éxito!\n\n"
                f"• Comprobante Interno: {nro_comprobante} ({tipo_comprobante})\n"
                f"• Precios y cantidades registrados en auditoría de Compras y Logística.\n"
                f"• Stock físico ingresado al depósito central.\n"
                f"• Ya puedes ejecutar el reparto automático para emitir los Remitos PDF."
            )
            self.vista.generar_nuevo_comprobante_id()
            self.inicializar()
            
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"Error al asentar comprobante: {str(e)}")

    def ejecutar_reparto(self):
        """Valida el stock físico registrado, aplica prorrateo si hubo faltantes y emite remitos PDF oficiales."""
        id_proveedor = self.vista.obtener_proveedor_seleccionado()
        id_pedido_sel = self.vista.obtener_pedido_seleccionado()

        pedidos = self.modelo.obtener_pedidos_consolidados_por_proveedor(id_proveedor)
        if not pedidos:
            self.vista.mostrar_mensaje_error("No hay pedidos en estado 'Consolidado' listos para repartir.")
            return

        # 1. Validar demanda vs stock físico real
        discrepancias = self.modelo.validar_stock_vs_pedidos(id_proveedor, id_pedido_sel)
        ajustes_totales = {}
        
        if discrepancias:
            confirmado = self.vista.mostrar_alerta_discrepancias(discrepancias)
            if not confirmado:
                return
                
            for disc in discrepancias:
                id_art = disc['id_articulo']
                for id_ped, cant_ajustada in disc['ajustes'].items():
                    ajustes_totales[(id_ped, id_art)] = cant_ajustada

        # 2. Ejecutar reparto y generación de PDFs oficiales
        nro_comp = self.vista.txt_nro_comprobante.text().strip() or generar_codigo_comprobante()
        exito, lista_pdfs = self.modelo.ejecutar_reparto_masivo(
            id_proveedor=id_proveedor,
            id_pedido_sel=id_pedido_sel,
            ajustes=ajustes_totales if ajustes_totales else None,
            nro_comprobante=nro_comp
        )
        
        if exito:
            total_pdfs = len(lista_pdfs)
            self.vista.mostrar_mensaje_exito(
                f"¡Reparto automático completado con éxito!\n\n"
                f"• Se generaron {total_pdfs} Remitos Oficiales en formato PDF (uno por cada proveedor para cada socio).\n"
                f"• Los remitos quedaron guardados en la carpeta 'remitos_pdf/'.\n"
                f"• Cada socio ha recibido una notificación con su remito emitido.\n\n"
                f"Puedes abrir la carpeta de remitos con el botón 'Ver Carpeta de Remitos PDF'."
            )
            self.inicializar()
            if self.on_reparto_completado:
                self.on_reparto_completado()
        else:
            self.vista.mostrar_mensaje_error("No fue posible ejecutar el proceso de reparto para la selección.")
