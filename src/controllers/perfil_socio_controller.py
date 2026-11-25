class PerfilSocioController:
    """Controlador de la pantalla de datos fiscales y domicilio del socio."""

    def __init__(self, vista, modelo, on_perfil_actualizado=None):
        self.vista = vista
        self.modelo = modelo
        self.on_perfil_actualizado = on_perfil_actualizado
        self.id_socio = None

        self.vista.btn_guardar.clicked.connect(self.guardar_datos)

    def set_socio(self, id_socio):
        self.id_socio = id_socio

    def inicializar(self):
        if self.id_socio is None:
            return
        perfil = self.modelo.obtener_perfil(self.id_socio)
        self.vista.cargar_datos(perfil)

    def guardar_datos(self):
        if self.id_socio is None:
            return
        datos = self.vista.obtener_datos_formulario()
        ok, res = self.modelo.actualizar_datos_fiscales(
            self.id_socio,
            datos["nombre"],
            datos["cuit_dni"],
            datos["condicion_iva"],
            datos["domicilio"],
        )
        if not ok:
            self.vista.mostrar_error(res)
            return

        self.vista.cargar_datos(res)
        self.vista.mostrar_exito("Tus datos fiscales y domicilio se guardaron correctamente.")
        if self.on_perfil_actualizado:
            self.on_perfil_actualizado(res)
