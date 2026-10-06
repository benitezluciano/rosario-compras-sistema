from src.database import Database

class ProveedorModel:
    def obtener_todos(self, id_user=None, role="admin"):
        """
        Retorna la lista de todos los proveedores registrados,
        incluyendo el nombre del ejecutivo responsable.
        """
        query = """
            SELECT 
                p.id_proveedor,
                p.id_user,
                p.nombre,
                p.email,
                p.telefono,
                p.direccion,
                u.nombre AS ejecutivo_nombre,
                (SELECT COUNT(*) FROM PRECIOS_NEGOCIADOS pn WHERE pn.id_proveedor = p.id_proveedor) AS total_articulos
            FROM PROVEEDORES p
            JOIN USERS u ON p.id_user = u.id
            ORDER BY p.nombre ASC
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def obtener_por_id(self, id_proveedor):
        """Obtiene el detalle completo de un proveedor específico."""
        query = """
            SELECT 
                p.id_proveedor,
                p.id_user,
                p.nombre,
                p.email,
                p.telefono,
                p.direccion,
                u.nombre AS ejecutivo_nombre
            FROM PROVEEDORES p
            JOIN USERS u ON p.id_user = u.id
            WHERE p.id_proveedor = ?
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_proveedor,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def obtener_ejecutivos(self):
        """Retorna los usuarios con rol 'ejecutivo' o 'admin' para asignación."""
        query = """
            SELECT id, nombre, email, role 
            FROM USERS 
            WHERE role IN ('ejecutivo', 'admin')
            ORDER BY nombre ASC
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def crear_proveedor(self, nombre, email, telefono, direccion, id_user):
        """Registra un nuevo proveedor en la base de datos."""
        nombre = nombre.strip() if nombre else ""
        if not nombre:
            return False, "El nombre del proveedor es obligatorio."

        query = """
            INSERT INTO PROVEEDORES (id_user, nombre, email, telefono, direccion)
            VALUES (?, ?, ?, ?, ?)
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_user, nombre, email.strip() if email else None, 
                                   telefono.strip() if telefono else None, 
                                   direccion.strip() if direccion else None))
            return True, cursor.lastrowid

    def actualizar_proveedor(self, id_proveedor, nombre, email, telefono, direccion, id_user):
        """Actualiza los datos de un proveedor existente."""
        nombre = nombre.strip() if nombre else ""
        if not nombre:
            return False, "El nombre del proveedor es obligatorio."

        query = """
            UPDATE PROVEEDORES
            SET nombre = ?, email = ?, telefono = ?, direccion = ?, id_user = ?
            WHERE id_proveedor = ?
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (nombre, email.strip() if email else None, 
                                   telefono.strip() if telefono else None, 
                                   direccion.strip() if direccion else None, 
                                   id_user, id_proveedor))
            return True, "Proveedor actualizado correctamente."

    def eliminar_proveedor(self, id_proveedor):
        """
        Elimina un proveedor y sus listas de precios asociadas.
        Valida que no tenga comprobantes registrados.
        """
        with Database() as conn:
            cursor = conn.cursor()
            
            # 1. Validar comprobantes
            cursor.execute("SELECT COUNT(*) FROM COMPROBANTES_PROVEEDOR WHERE id_proveedor = ?", (id_proveedor,))
            if cursor.fetchone()[0] > 0:
                return False, "No se puede eliminar el proveedor porque posee comprobantes de entrega o facturas históricas registradas."

            # 2. Eliminar precios negociados vinculados
            cursor.execute("DELETE FROM PRECIOS_NEGOCIADOS WHERE id_proveedor = ?", (id_proveedor,))

            # 3. Eliminar proveedor
            cursor.execute("DELETE FROM PROVEEDORES WHERE id_proveedor = ?", (id_proveedor,))
            return True, "Proveedor y su catálogo asociado eliminados con éxito."
