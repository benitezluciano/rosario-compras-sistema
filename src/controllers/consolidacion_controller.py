class ConsolidacionController:
    def __init__(self, vista, modelo, on_pedidos_consolidados=None, usuario_actual=None):
        self.vista = vista
        self.modelo = modelo
        self.on_pedidos_consolidados = on_pedidos_consolidados
        self.usuario_actual = usuario_actual or {'id': 2, 'nombre': 'Ejecutivo de Cuentas', 'role': 'ejecutivo'}
        
        # Conectar eventos de la vista
        if hasattr(self.vista, 'btn_refrescar'):
            self.vista.btn_refrescar.clicked.connect(self.recargar_matriz)
        if hasattr(self.vista, 'cmb_proveedor'):
            self.vista.cmb_proveedor.currentIndexChanged.connect(self.recargar_matriz)
        if hasattr(self.vista, 'btn_guardar_ajustes'):
            self.vista.btn_guardar_ajustes.clicked.connect(self.guardar_ajustes)
        if hasattr(self.vista, 'btn_exportar'):
            self.vista.btn_exportar.clicked.connect(self.exportar_planilla_general)
        if hasattr(self.vista, 'btn_exportar_proveedores'):
            self.vista.btn_exportar_proveedores.clicked.connect(self.exportar_por_proveedor)
        if hasattr(self.vista, 'btn_consolidar'):
            self.vista.btn_consolidar.clicked.connect(self.procesar_consolidacion)

    def set_usuario_actual(self, usuario):
        """Actualiza la sesión del usuario conectado."""
        self.usuario_actual = usuario

    def inicializar(self):
        """Carga los proveedores disponibles y la matriz de pedidos para el primer proveedor."""
        proveedores = self.modelo.obtener_proveedores()
        self.vista.cargar_proveedores(proveedores)
        self.recargar_matriz()

    def recargar_matriz(self):
        """Consulta la matriz de consolidación para el proveedor seleccionado y la muestra en la vista."""
        id_proveedor = self.vista.obtener_proveedor_seleccionado()
        if not id_proveedor:
            return
        datos_matriz = self.modelo.obtener_matriz_pedidos_proveedor(id_proveedor)
        self.vista.cargar_matriz_proveedor(datos_matriz)

    def guardar_ajustes(self):
        """Guarda las modificaciones realizadas por el ejecutivo y notifica a cada socio afectado."""
        mods = self.vista.obtener_modificaciones_pendientes()
        if not mods:
            self.vista.mostrar_mensaje_error("No hay modificaciones pendientes de guardar.")
            return

        nombre_ejec = self.usuario_actual.get('nombre', 'Ejecutivo de Cuentas')
        try:
            afectados = self.modelo.guardar_modificaciones_ejecutivo(mods, nombre_ejecutivo=nombre_ejec)
            self.vista.mostrar_mensaje_exito(
                f"¡Ajustes guardados exitosamente!\n\n"
                f"• Se actualizaron {len(mods)} renglones de pedido.\n"
                f"• Se emitieron notificaciones a {afectados} socio(s) avisándoles de las modificaciones realizadas en sus pedidos."
            )
            self.recargar_matriz()
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"Error al guardar modificaciones: {str(e)}")

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
        """Consolida los pedidos del proveedor seleccionado, cierra su lista y notifica a cada socio."""
        id_proveedor = self.vista.obtener_proveedor_seleccionado()
        if not id_proveedor:
            self.vista.mostrar_mensaje_error("Debes seleccionar un proveedor.")
            return
        nombre_prov = self.vista.obtener_nombre_proveedor_seleccionado()

        if self.vista.obtener_modificaciones_pendientes():
            self.vista.mostrar_mensaje_error(
                "Tienes ajustes sin guardar en la matriz.\nGuárdalos (o actualiza la matriz para descartarlos) antes de consolidar."
            )
            return

        resumen = self.modelo.obtener_resumen_consolidado(id_proveedor)
        if not resumen:
            self.vista.mostrar_mensaje_error(f"'{nombre_prov}' no tiene pedidos pendientes para consolidar.")
            return

        total = sum(r.get('total_estimado') or 0 for r in resumen)
        confirmado = self.vista.confirmar_accion(
            "Confirmar Consolidación y Envío al Proveedor",
            f"¿Consolidar y confirmar el envío de la orden de compra a '{nombre_prov}'?\n\n"
            f"• {len(resumen)} artículos · Total estimado ${total:,.2f}\n"
            f"• Los pedidos de los socios para este proveedor pasarán a estado 'Consolidado' (precio congelado).\n"
            f"• La lista de precios de '{nombre_prov}' se cerrará (fin del ciclo de pedidos).\n"
            f"• Cada socio recibirá una notificación automática.\n"
            f"• Los pedidos de otros proveedores no se modifican."
        )
        if not confirmado:
            return

        cantidad = self.modelo.marcar_pedidos_como_consolidados(id_proveedor)
        self.vista.mostrar_mensaje_exito(
            f"¡Se consolidaron y despacharon {cantidad} pedido(s) a '{nombre_prov}'!\n"
            f"La lista quedó cerrada y los socios fueron notificados."
        )
        self.inicializar()
        
        if self.on_pedidos_consolidados:
            self.on_pedidos_consolidados()
