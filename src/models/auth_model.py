from werkzeug.security import check_password_hash
from src.database import Database

class AuthModel:
    def autenticar_usuario(self, email, password):
        """
        Valida las credenciales ingresadas contra la tabla USERS.
        Retorna (usuario_dict, None) si es exitoso, o (None, mensaje_error) si falla.
        """
        if not email or not str(email).strip():
            return None, "El correo electrónico es obligatorio."
        if not password or not str(password).strip():
            return None, "La contraseña es obligatoria."

        email = str(email).strip().lower()

        query = "SELECT id, nombre, email, password_hash, role FROM USERS WHERE LOWER(email) = ?"
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (email,))
            row = cursor.fetchone()

        if not row:
            return None, "No existe ningún usuario registrado con ese correo electrónico."

        user = dict(row)
        password_hash = user.get('password_hash', '')

        # Validar contraseña con werkzeug
        if not check_password_hash(password_hash, password):
            return None, "La contraseña ingresada es incorrecta."

        usuario_autenticado = {
            'id': user['id'],
            'nombre': user['nombre'],
            'email': user['email'],
            'role': user['role']
        }
        return usuario_autenticado, None
