from datetime import datetime
from src.database import Database

class NotificacionModel:
    def crear_notificacion(self, mensaje, tipo="info", id_user=None):
        """
        Registra una nueva notificación en la base de datos.
        Si id_user es None, es una notificación para los ejecutivos/administradores.
        """
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
            INSERT INTO NOTIFICACIONES (id_user, mensaje, tipo, fecha, leida)
            VALUES (?, ?, ?, ?, 0)
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_user, mensaje, tipo, fecha_actual))
            return cursor.lastrowid

    def notificar_a_todos_los_socios(self, mensaje, tipo="catalogo_actualizado"):
        """
        Emite una notificación masiva para todos los usuarios con rol 'socio'.
        """
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM USERS WHERE role = 'socio'")
            socios = cursor.fetchall()
            
            for socio in socios:
                cursor.execute("""
                    INSERT INTO NOTIFICACIONES (id_user, mensaje, tipo, fecha, leida)
                    VALUES (?, ?, ?, ?, 0)
                """, (socio['id'], mensaje, tipo, fecha_actual))
                
        return len(socios)

    def obtener_notificaciones_usuario(self, id_user, rol):
        """
        Obtiene las notificaciones relevantes para el usuario:
        - Si es socio: notificaciones donde id_user = su ID.
        - Si es ejecutivo o admin: notificaciones donde id_user IS NULL (avisos de nuevos pedidos).
        """
        with Database() as conn:
            cursor = conn.cursor()
            if rol == 'socio':
                cursor.execute("""
                    SELECT id_notificacion, mensaje, tipo, fecha, leida
                    FROM NOTIFICACIONES
                    WHERE id_user = ?
                    ORDER BY id_notificacion DESC
                    LIMIT 25
                """, (id_user,))
            else:
                cursor.execute("""
                    SELECT id_notificacion, mensaje, tipo, fecha, leida
                    FROM NOTIFICACIONES
                    WHERE id_user IS NULL
                    ORDER BY id_notificacion DESC
                    LIMIT 25
                """)
            return [dict(row) for row in cursor.fetchall()]

    def contar_no_leidas(self, id_user, rol):
        """Retorna el número de notificaciones no leídas."""
        with Database() as conn:
            cursor = conn.cursor()
            if rol == 'socio':
                cursor.execute("SELECT COUNT(*) FROM NOTIFICACIONES WHERE id_user = ? AND leida = 0", (id_user,))
            else:
                cursor.execute("SELECT COUNT(*) FROM NOTIFICACIONES WHERE id_user IS NULL AND leida = 0")
            return cursor.fetchone()[0]

    def marcar_todas_como_leidas(self, id_user, rol):
        """Marca como leídas las notificaciones correspondientes al rol/usuario."""
        with Database() as conn:
            cursor = conn.cursor()
            if rol == 'socio':
                cursor.execute("UPDATE NOTIFICACIONES SET leida = 1 WHERE id_user = ?", (id_user,))
            else:
                cursor.execute("UPDATE NOTIFICACIONES SET leida = 1 WHERE id_user IS NULL")
