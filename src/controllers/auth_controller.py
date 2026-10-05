class AuthController:
    def __init__(self, vista, modelo, on_login_success=None):
        self.vista = vista
        self.modelo = modelo
        self.on_login_success = on_login_success
        
        # Conectar eventos de la vista
        if hasattr(self.vista, 'btn_login'):
            self.vista.btn_login.clicked.connect(self.procesar_login)
        if hasattr(self.vista, 'txt_password'):
            self.vista.txt_password.returnPressed.connect(self.procesar_login)
        if hasattr(self.vista, 'txt_email'):
            self.vista.txt_email.returnPressed.connect(self.procesar_login)

    def procesar_login(self):
        """Lee las credenciales, consulta al modelo y gestiona la transición."""
        email, password = self.vista.obtener_credenciales()
        
        usuario, error = self.modelo.autenticar_usuario(email, password)
        
        if error:
            self.vista.mostrar_error(error)
            return

        self.vista.limpiar_campos()
        
        if self.on_login_success:
            self.on_login_success(usuario)
