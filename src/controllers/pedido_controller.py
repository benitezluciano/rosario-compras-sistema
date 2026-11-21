class PedidoController:
    """
    Portal del socio. Cada hoja (proveedor) es un pedido independiente:
    - "Enviar pedido de esta hoja": crea, modifica o anula el pedido de ese proveedor.
    - "Enviar todo": aplica los cambios de todas las hojas (un pedido por proveedor),
      previa confirmación con un resumen.
    """

    ACCIONES = {
        'nuevo': "🆕 Nuevo pedido",
        'modificar': "✏️ Modificar pedido",
        'anular': "🗑️ Anular pedido",
    }

    def __init__(self, vista, modelo, on_pedido_creado=None):
        self.vista = vista
        self.modelo = modelo
        self.on_pedido_creado = on_pedido_creado

        # Conectar eventos de la vista
        if hasattr(self.vista, 'btn_confirmar'):
            self.vista.btn_confirmar.clicked.connect(self.enviar_todo)
        if hasattr(self.vista, 'enviar_hoja_solicitado'):
            self.vista.enviar_hoja_solicitado.connect(self.enviar_hoja)
        if hasattr(self.vista, 'cmb_socio_seleccion'):
            self.vista.cmb_socio_seleccion.currentIndexChanged.connect(self.al_cambiar_socio)

    def inicializar(self):
        """Carga los socios, las listas habilitadas y los pedidos vigentes del socio actual."""
        socios = self.modelo.obtener_socios()
        self.vista.cargar_socios_selector(socios)

        articulos = self.modelo.obtener_catalogo_articulos()
        self.vista.cargar_articulos(articulos)

        self.sincronizar_estado_socio()

    def al_cambiar_socio(self):
        """Maneja el cambio de socio seleccionado por un Ejecutivo o Admin."""
        self.sincronizar_estado_socio()

    def sincronizar_estado_socio(self):
        """Carga los pedidos 'Pendiente' del socio (uno por proveedor)."""
        id_socio = self.vista.obtener_id_socio()
        if not id_socio:
            return
        vigentes = self.modelo.obtener_pedidos_vigentes(id_socio)
        self.vista.establecer_pedidos_vigentes(vigentes)

    # ------------------------------------------------------------------
    # Envío por hoja
    # ------------------------------------------------------------------

    def enviar_hoja(self, id_proveedor):
        """Crea, modifica o anula el pedido de una sola hoja (proveedor)."""
        id_socio = self.vista.obtener_id_socio()
        cambios = self.vista.obtener_cambios_por_hoja(id_proveedor)

        if id_proveedor not in cambios:
            if self.vista.hoja_tiene_pedido_vigente(id_proveedor):
                self.vista.mostrar_mensaje_info("No hay cambios para guardar en el pedido de esta hoja.")
            else:
                self.vista.mostrar_mensaje_error("Ingresa al menos una cantidad en esta hoja para emitir el pedido.")
            return

        cambio = cambios[id_proveedor]
        try:
            if cambio['accion'] == 'anular':
                if not self.vista.confirmar_accion(
                    "Anular Pedido",
                    f"Dejaste todas las cantidades en 0 en la hoja de '{cambio['nombre']}'.\n\n"
                    f"¿Confirmas que deseas ANULAR el pedido {cambio['codigo']}?\n"
                    f"Esta acción no se puede deshacer."
                ):
                    return
                codigo = self.modelo.anular_pedido_vigente(id_socio, id_proveedor)
                self.vista.mostrar_mensaje_exito(f"El pedido {codigo} para '{cambio['nombre']}' fue anulado.")
            else:
                r = self.modelo.guardar_pedido_proveedor(id_socio, id_proveedor, cambio['items'])
                if r['es_nuevo']:
                    self.vista.mostrar_mensaje_exito(
                        f"¡Pedido {r['codigo_comercial']} registrado con éxito!\n\n"
                        f"• Proveedor: {r['proveedor_nombre']}\n"
                        f"• {r['cantidad_productos']} productos · Total estimado ${cambio['total']:,.2f}\n"
                        f"• El Ejecutivo de Cuentas fue notificado."
                    )
                else:
                    self.vista.mostrar_mensaje_exito(
                        f"¡Pedido {r['codigo_comercial']} actualizado con éxito!\n\n"
                        f"• Proveedor: {r['proveedor_nombre']}\n"
                        f"• {r['cantidad_productos']} productos · Total estimado ${cambio['total']:,.2f}\n"
                        f"• Puedes seguir modificándolo mientras esté en estado 'Pendiente'."
                    )
        except ValueError as e:
            self.vista.mostrar_mensaje_error(str(e))
            return
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"Error al procesar el pedido: {str(e)}")
            return

        self._despues_de_guardar()

    # ------------------------------------------------------------------
    # Enviar todo
    # ------------------------------------------------------------------

    def enviar_todo(self):
        """Aplica los cambios de todas las hojas, previa confirmación con resumen por proveedor."""
        id_socio = self.vista.obtener_id_socio()
        cambios = self.vista.obtener_cambios_por_hoja()

        if not cambios:
            self.vista.mostrar_mensaje_info(
                "No hay cambios para enviar.\nIngresa cantidades en una o más hojas, o modifica tus pedidos vigentes."
            )
            return

        lineas = []
        for c in cambios.values():
            accion = self.ACCIONES[c['accion']]
            ref = f" {c['codigo']}" if c['codigo'] else ""
            if c['accion'] == 'anular':
                lineas.append(f"• {c['nombre']}: {accion}{ref}")
            else:
                lineas.append(f"• {c['nombre']}: {accion}{ref} — {len(c['items'])} productos · ${c['total']:,.2f}")
        total = sum(c['total'] for c in cambios.values())

        if not self.vista.confirmar_accion(
            "Confirmar Envío de Pedidos",
            "Se procesará un pedido independiente por cada proveedor:\n\n"
            + "\n".join(lineas)
            + f"\n\nTotal estimado: ${total:,.2f}\n\n¿Confirmas el envío?"
        ):
            return

        a_guardar = {p: c['items'] for p, c in cambios.items() if c['accion'] != 'anular'}
        a_anular = [p for p, c in cambios.items() if c['accion'] == 'anular']

        try:
            resultados = self.modelo.guardar_pedidos(id_socio, a_guardar) if a_guardar else []
            anulados = [self.modelo.anular_pedido_vigente(id_socio, p) for p in a_anular]
        except ValueError as e:
            self.vista.mostrar_mensaje_error(str(e))
            return
        except Exception as e:
            self.vista.mostrar_mensaje_error(f"Error al procesar los pedidos: {str(e)}")
            return

        detalle = [
            f"• {r['codigo_comercial']} — {r['proveedor_nombre']} ({'nuevo' if r['es_nuevo'] else 'actualizado'})"
            for r in resultados
        ] + [f"• {cod} — anulado" for cod in anulados if cod]
        self.vista.mostrar_mensaje_exito("¡Pedidos procesados con éxito!\n\n" + "\n".join(detalle))

        self._despues_de_guardar()

    def _despues_de_guardar(self):
        self.sincronizar_estado_socio()
        if self.on_pedido_creado:
            self.on_pedido_creado()
