import pandas as pd
import os

class ConsolidacionModel:
    def __init__(self):
        pass

    def leer_vista_previa(self, ruta_archivo):
        """
        Lee el archivo de planilla (.xlsx, .xls o .csv) y extrae las columnas 
        y las primeras 10 filas para mostrarlas como vista previa.
        Maneja errores de lectura y retorna la tupla: (headers, filas_previa, error)
        """
        if not os.path.exists(ruta_archivo):
            return None, None, f"El archivo especificado no existe en la ruta: {ruta_archivo}"

        ext = os.path.splitext(ruta_archivo)[1].lower()

        try:
            if ext in ['.xlsx', '.xls']:
                # Lectura de planilla Excel
                df = pd.read_excel(ruta_archivo)
            elif ext == '.csv':
                # Lectura de archivo CSV
                try:
                    # Detectar separador automáticamente usando el motor de Python
                    df = pd.read_csv(ruta_archivo, sep=None, engine='python')
                except Exception:
                    # Fallbacks seguros en caso de fallo del motor automático
                    try:
                        df = pd.read_csv(ruta_archivo, sep=';')
                    except Exception:
                        df = pd.read_csv(ruta_archivo, sep=',')
            else:
                # Intentar leer cualquier otra extensión como CSV/delimitado
                df = pd.read_csv(ruta_archivo, sep=None, engine='python')

            # Reemplazar valores nulos (NaN) por strings vacíos para evitar problemas en PyQt6
            df = df.fillna("")

            # Extraer headers y primeras 10 filas convertidas a strings
            headers = [str(col) for col in df.columns]
            filas_previa = []
            
            for _, row in df.head(10).iterrows():
                filas_previa.append([str(val) for val in row.values])

            return headers, filas_previa, None

        except Exception as e:
            return None, None, f"Error al abrir o interpretar la planilla: {str(e)}"
