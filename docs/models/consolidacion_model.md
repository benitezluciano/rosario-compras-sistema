# Modelo: `consolidacion_model.py`

## Propósito Principal
Se encarga de inyectar las capacidades de procesamiento lógico de Dataframes sobre archivos de hoja de cálculo nativos (archivos alojados en el disco local del usuario) para previsualizar y extraer tabulaciones de los nuevos catálogos de proveedores requeridos en el Caso de Uso 3.

## Dependencias e Interacciones
- **Llama a**: La poderosa librería analítica externa `pandas` y el módulo base nativo para paths del sistema operativo, `os`.
- **Es llamado por**: `ConsolidacionController`.

## Lógica Clave
- `leer_vista_previa(ruta_archivo)`: 
  - Realiza el filtrado y derivación automática con base en la extensión tipada del archivo, deduciendo si el formato pertenece a la suite de binarios de Office (`.xls`, `.xlsx`) o si se trata de un fichero de texto plano y tabulado tipo `.csv`.
  - Utiliza los métodos potentes de `pandas.read_excel()` y `pandas.read_csv()`. Para los csv, añade una serie anidada de **fallbacks escalonados o defensivos** en los separadores nativos: emplea primero una orden de auto-detección dinámica (`sep=None`, `engine=python`); si el parser automático llegara a arrojar error (por corrupciones en el sistema o formato europeo mal guardado), deriva un rescate en forma de cascada intentando forzar delimitadores clásicos con coma o de punto y coma, previniendo caídas totales.
  - Sanitiza el DataFrame transformando cualquier objeto nulo de sistema resultante de celdas vacías del Excel (tipadas matemáticamente como float `NaN`) reemplazándolos con *strings* vacíos universales vía `df.fillna("")`. Esta manipulación garantiza que la renderización de la capa PyQt6 posterior no colapse o pinte texto inválido en pantalla.
  - Extrae y estandariza los cabezales del DataFrame y entrega hacia el controlador superior únicamente un "fragmento o snapshot" tabular con las primeras 10 líneas de las hojas empleando iteradores nativos (`.head(10).iterrows()`).
