import os
import pandas as pd
from src.database import Database
from src.models.notificacion_model import NotificacionModel

class CatalogoModel:
    def obtener_proveedores(self):
        """Devuelve la lista de proveedores registrados en la base de datos."""
        query = "SELECT id_proveedor, nombre, email, telefono, direccion FROM PROVEEDORES ORDER BY nombre ASC"
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]

    def obtener_proveedor_por_id(self, id_proveedor):
        """Obtiene la información completa del proveedor junto con su ejecutivo."""
        query = """
            SELECT p.id_proveedor, p.id_user, p.nombre, p.email, p.telefono, p.direccion,
                   u.nombre AS ejecutivo_nombre, u.email AS ejecutivo_email
            FROM PROVEEDORES p
            JOIN USERS u ON p.id_user = u.id
            WHERE p.id_proveedor = ?
        """
        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (id_proveedor,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def solicitar_lista_proveedor(self, id_proveedor):
        """
        Registra la emisión de la solicitud formal de lista de precios a un proveedor.
        """
        prov = self.obtener_proveedor_por_id(id_proveedor)
        if not prov:
            return False, "Proveedor no encontrado.", None
        
        return True, f"Solicitud preparada para '{prov['nombre']}'.", prov

    def leer_vista_previa(self, ruta_archivo):
        """
        Lee el archivo de lista de precios (.xlsx, .xls o .csv) con pandas
        y retorna columnas enriquecidas:
        Código | Detalle | Rubro | Precio Base | Descuento | Precio c/ Descuento | Precio + IVA (21%)
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
            
            # Normalizar columnas
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

            headers = ["Código", "Detalle / Producto", "Rubro", "Precio Base", "Descuento", "Precio c/ Desc.", "Precio + IVA (21%)"]
            filas = []

            for _, row in df.head(50).iterrows():
                cod = str(row[col_cod]).strip() if col_cod else "-"
                det = str(row[col_det]).strip() if col_det else ""
                rub = str(row[col_rub]).strip() if col_rub else "General"
                
                if not det and not cod:
                    continue

                # Parsear precio
                precio_base = 0.0
                if col_pre:
                    try:
                        raw_p = str(row[col_pre]).replace('$', '').replace(' ', '').replace(',', '.')
                        precio_base = float(raw_p) if raw_p else 0.0
                    except ValueError:
                        precio_base = 0.0

                # Parsear descuento
                desc_pct = 0.0
                if col_des:
                    try:
                        raw_d = str(row[col_des]).replace('%', '').replace(' ', '').replace(',', '.')
                        desc_pct = float(raw_d) if raw_d else 0.0
                        if desc_pct > 1.0:
                            desc_pct = desc_pct / 100.0
                    except ValueError:
                        desc_pct = 0.0

                precio_con_desc = precio_base * (1.0 - desc_pct)
                precio_con_iva = precio_con_desc * 1.21

                filas.append([
                    cod,
                    det,
                    rub,
                    f"${precio_base:,.2f}",
                    f"{desc_pct * 100:.1f}%",
                    f"${precio_con_desc:,.2f}",
                    f"${precio_con_iva:,.2f}"
                ])

            return headers, filas, None
        except Exception as e:
            return None, None, f"Error al leer la planilla del proveedor: {str(e)}"

    def importar_lista_proveedor(self, id_proveedor, ruta_archivo):
        """
        Interpreta la planilla del proveedor y actualiza o inserta los artículos
        y sus precios negociados en SQLite, guardando precio base, descuento y precio con descuento.
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
                        precio_base = float(raw_precio) if raw_precio else 0.0
                    except ValueError:
                        precio_base = 0.0

                    descuento = 0.0
                    if col_des:
                        try:
                            raw_desc = str(row[col_des]).replace('%', '').replace(' ', '').replace(',', '.')
                            descuento = float(raw_desc) if raw_desc else 0.0
                            if descuento > 1.0:
                                descuento = descuento / 100.0
                        except ValueError:
                            descuento = 0.0

                    precio_final = precio_base * (1.0 - descuento)

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
                        INSERT OR REPLACE INTO PRECIOS_NEGOCIADOS (id_proveedor, id_articulo, precio_base, precio_final, descuento)
                        VALUES (?, ?, ?, ?, ?)
                    """, (id_proveedor, id_articulo, precio_base, precio_final, descuento))
                    
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
