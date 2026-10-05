import os
import pandas as pd
from src.database import Database
from src.models.notificacion_model import NotificacionModel

class CatalogoModel:
    def obtener_proveedores(self):
        """Devuelve la lista de proveedores registrados en la base de datos."""
        query = "SELECT id_proveedor, nombre, direccion FROM PROVEEDORES ORDER BY nombre ASC"
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def solicitar_lista_proveedor(self, id_proveedor):
        """
        Registra la emisión de la solicitud formal de lista de precios a un proveedor.
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, direccion FROM PROVEEDORES WHERE id_proveedor = ?", (id_proveedor,))
            row = cursor.fetchone()
            if not row:
                return False, "Proveedor no encontrado."
            
            nombre_prov = row['nombre']
            return True, f"Se ha generado y registrado la solicitud de lista de precios actualizada al proveedor '{nombre_prov}'."

    def leer_vista_previa(self, ruta_archivo):
        """
        Lee el archivo de lista de precios (.xlsx, .xls o .csv) con pandas
        y retorna (headers, filas, None) o (None, None, error).
        """
        if not os.path.exists(ruta_archivo):
            return None, None, f"No existe el archivo en la ruta: {ruta_archivo}"

        ext = os.path.splitext(ruta_archivo)[1].lower()
        try:
            if ext in ['.xlsx', '.xls']:
                df = pd.read_excel(ruta_archivo)
            elif ext == '.csv':
                try:
                    df = pd.read_csv(ruta_archivo, sep=None, engine='python')
                except Exception:
                    df = pd.read_csv(ruta_archivo, sep=';')
            else:
                df = pd.read_csv(ruta_archivo, sep=None, engine='python')

            df = df.fillna("")
            headers = [str(c) for c in df.columns]
            filas = []
            for _, row in df.head(15).iterrows():
                filas.append([str(v) for v in row.values])

            return headers, filas, None
        except Exception as e:
            return None, None, f"Error al leer la planilla del proveedor: {str(e)}"

    def importar_lista_proveedor(self, id_proveedor, ruta_archivo):
        """
        Interpreta la planilla del proveedor y actualiza o inserta los artículos
        y sus precios negociados en SQLite.
        Emite automáticamente una notificación a todos los socios informando la disponibilidad.
        """
        if not os.path.exists(ruta_archivo):
            return False, f"No se encontró el archivo: {ruta_archivo}"

        ext = os.path.splitext(ruta_archivo)[1].lower()
        try:
            if ext in ['.xlsx', '.xls']:
                df = pd.read_excel(ruta_archivo)
            else:
                try:
                    df = pd.read_csv(ruta_archivo, sep=None, engine='python')
                except Exception:
                    df = pd.read_csv(ruta_archivo, sep=';')

            df = df.fillna("")
            
            # Normalizar nombres de columnas a minúsculas
            cols_map = {str(col).strip().lower(): col for col in df.columns}
            
            def find_col(posibles):
                for p in posibles:
                    for c_low, orig in cols_map.items():
                        if p in c_low:
                            return orig
                return None

            col_cod = find_col(['codigo', 'cod', 'id_articulo_proveedor', 'referencia', 'sku'])
            col_det = find_col(['detalle', 'descripcion', 'articulo', 'producto', 'nombre'])
            col_rub = find_col(['rubro', 'categoria', 'tipo', 'linea'])
            col_pre = find_col(['precio_final', 'precio', 'importe', 'costo', 'valor'])
            col_des = find_col(['descuento', 'desc', 'bonificacion'])

            if not col_det or not col_pre:
                return False, "La planilla debe contener al menos una columna de 'Detalle/Artículo' y una de 'Precio'."

            articulos_insertados = 0
            nombre_prov = "Proveedor"
            
            with Database() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nombre FROM PROVEEDORES WHERE id_proveedor = ?", (id_proveedor,))
                prov_row = cursor.fetchone()
                if prov_row:
                    nombre_prov = prov_row['nombre']
                
                for _, row in df.iterrows():
                    detalle = str(row[col_det]).strip()
                    if not detalle:
                        continue

                    cod_prov = str(row[col_cod]).strip() if col_cod else ""
                    rubro = str(row[col_rub]).strip() if col_rub else "General"
                    
                    try:
                        raw_precio = str(row[col_pre]).replace('$', '').replace(' ', '').replace(',', '.')
                        precio = float(raw_precio)
                    except ValueError:
                        precio = 0.0

                    descuento = 0.0
                    if col_des:
                        try:
                            raw_desc = str(row[col_des]).replace('%', '').replace(' ', '').replace(',', '.')
                            descuento = float(raw_desc)
                            if descuento > 1.0:
                                descuento = descuento / 100.0
                        except ValueError:
                            descuento = 0.0

                    # 1. Verificar si el artículo ya existe por detalle o código
                    cursor.execute("SELECT id_articulo FROM ARTICULOS WHERE LOWER(detalle) = LOWER(?)", (detalle,))
                    art_row = cursor.fetchone()
                    
                    if art_row:
                        id_articulo = art_row['id_articulo']
                        cursor.execute("""
                            UPDATE ARTICULOS 
                            SET id_articulo_proveedor = COALESCE(NULLIF(?, ''), id_articulo_proveedor),
                                rubro = COALESCE(NULLIF(?, ''), rubro)
                            WHERE id_articulo = ?
                        """, (cod_prov, rubro, id_articulo))
                    else:
                        cursor.execute("""
                            INSERT INTO ARTICULOS (id_articulo_proveedor, detalle, rubro, cantidad_stock)
                            VALUES (?, ?, ?, 0)
                        """, (cod_prov, detalle, rubro))
                        id_articulo = cursor.lastrowid

                    # 2. Insertar o actualizar el precio negociado con el proveedor
                    cursor.execute("""
                        INSERT OR REPLACE INTO PRECIOS_NEGOCIADOS (id_proveedor, id_articulo, precio_final, descuento)
                        VALUES (?, ?, ?, ?)
                    """, (id_proveedor, id_articulo, precio, descuento))
                    
                    articulos_insertados += 1

            # 3. Notificación masiva automática a los socios
            try:
                notif = NotificacionModel()
                notif.notificar_a_todos_los_socios(
                    mensaje=f"El Ejecutivo actualizó el catálogo con {articulos_insertados} productos de '{nombre_prov}'. Ya puedes consultar precios y cargar tu pedido.",
                    tipo="catalogo_actualizado"
                )
            except Exception as e:
                print(f"Advertencia al notificar actualización de catálogo: {e}")

            return True, f"Se importaron y actualizaron con éxito {articulos_insertados} artículos en el catálogo único.\nSe notificó a los socios sobre la disponibilidad."

        except Exception as e:
            return False, f"Error durante el procesamiento de la planilla: {str(e)}"
