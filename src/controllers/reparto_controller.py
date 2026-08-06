class RepartoController:
    def __init__(self, vista, modelo):
        self.vista = vista
        self.modelo = modelo
        
        # Conectar señales de la vista
        if hasattr(self.vista, 'btn_ejecutar'):
            self.vista.btn_ejecutar.clicked.connect(self.procesar_asignacion)

    def inicializar(self):
        """Carga los pedidos pendientes o consolidados y los despliega en la tabla."""
        try:
            pedidos = self.modelo.obtener_pedidos_consolidados()
            self.vista.cargar_pedidos(pedidos)
            self.vista.actualizar_estado_interfaz("Pendiente")
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"Error al cargar pedidos: {str(e)}")

    def procesar_asignacion(self):
        """
        Ejecuta la asignación automática. Cambia el estado visual a 'Procesando...',
        valida el stock, propone ajustes si hay discrepancia (Excepción E1),
        y ejecuta el reparto masivo en la BD si se aprueba.
        """
        # Cambiar estado en la UI
        self.vista.actualizar_estado_interfaz("Procesando...")
        
        try:
            # 1. Validar el stock vs los pedidos consolidados
            discrepancias = self.modelo.validar_stock_vs_pedidos()
            
            ajustes_para_db = None
            
            if discrepancias:
                # E1: Stock insuficiente. Mostrar propuesta de ajuste
                aceptar_ajuste = self.vista.mostrar_alerta_ajuste(discrepancias)
                if not aceptar_ajuste:
                    # Cancelar la operación
                    self.vista.actualizar_estado_interfaz("Asignación Cancelada")
                    return
                
                # Consolidar los ajustes individuales
                # Estructura: (id_pedido, id_articulo) -> cantidad_ajustada
                ajustes_para_db = {}
                for disc in discrepancias:
                    id_art = disc['id_articulo']
                    for id_ped, cant_ajustada in disc['ajustes'].items():
                        ajustes_para_db[(id_ped, id_art)] = cant_ajustada
            
            # 2. Intentar procesar asignación masiva, actualizar stock y generar remitos
            resultado = self.modelo.ejecutar_reparto_masivo(ajustes=ajustes_para_db)
            
            if resultado:
                # Notificar éxito y actualizar interfaz
                self.vista.actualizar_estado_interfaz("Completado")
                
                mensaje_exito = (
                    "Asignación automática de reparto completada con éxito.\n"
                    "Se han generado los remitos correspondientes y se ha descontado el stock de los artículos."
                )
                if ajustes_para_db:
                    mensaje_exito += "\n\nNota: Se aplicó el ajuste proporcional equitativo aceptado debido a faltantes de stock."
                
                self.vista.mostrar_mensaje_exito(mensaje_exito)
            else:
                self.vista.actualizar_estado_interfaz("Pendiente")
                self.vista.mostrar_mensaje_exito("No se encontraron pedidos en estado 'Consolidado' para procesar.")
            
            # Recargar la tabla
            self.inicializar()
            
        except Exception as e:
            # Capturar cualquier error inesperado
            self.vista.actualizar_estado_interfaz("Pendiente")
            self.vista.mostrar_mensaje_error(f"Error inesperado al ejecutar el reparto: {str(e)}")
