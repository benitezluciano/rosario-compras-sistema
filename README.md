# Rosario Compras - Sistema de Gestión

Sistema de gestión interna para la empresa Rosario Compras, diseñado con arquitectura **MVC (Modelo - Vista - Controlador)** utilizando Python, PyQt6 y SQLite.

## Arquitectura y Estructura

El repositorio separa sus responsabilidades de forma estricta para asegurar la escalabilidad:

```text
rosario-compras-sistema/
├── db/
│   └── rosario_compras.sql       # Estructura DDL inicial de la base de datos
├── migrations/                   # Scripts SQL de alteraciones a la base
├── src/
│   ├── models/                   # Clases con reglas de negocio y lógica de BD
│   │   ├── pedido_model.py
│   │   ├── reparto_model.py
│   │   └── consolidacion_model.py
│   │
│   ├── views/                    # Diseños .ui (Qt) y clases de interfaz visual
│   │   ├── pedido_view.py
│   │   ├── reparto_view.py
│   │   └── consolidacion_view.py
│   │
│   ├── controllers/              # Orquestadores lógicos (eventos y flujos)
│   │   ├── pedido_controller.py
│   │   ├── reparto_controller.py
│   │   └── consolidacion_controller.py
│   │
│   └── database.py               # Context Manager y utilidades de SQLite
├── venv/                         # Entorno virtual de Python
├── database.db                   # Base de datos SQLite local
├── main.py                       # Punto de entrada principal (Menú y Navegación)
├── requirements.txt              # Dependencias (pandas, openpyxl, PyQt6, etc.)
├── seed_db.py                    # Script poblador de datos de prueba
└── README.md                     # Documentación del proyecto
```

## Casos de Uso Implementados

1. **Carga Digital de Pedidos (CU-001):** Interfaz para consultar listas de precios activos y cargar pedidos al carrito dinámicamente con cálculo de subtotales en tiempo real.
2. **Consolidación de Planillas (CU-002):** Generador y exportador de planillas de consolidación (`.xlsx` / `.csv`). Agrupa y totaliza el conjunto de todos los pedidos cargados por los socios, permitiendo previsualizar el volumen total demandado por artículo/proveedor y exportar la planilla oficial, pasando los pedidos a estado *Consolidado*.
3. **Reparto Automático (CU-003):** Motor logístico transaccional. Cruza pedidos consolidados con el stock físico. Aplica automáticamente un algoritmo de prorrateo equitativo si la demanda supera la existencia física (Excepción E1), requiriendo validación humana para asentar remitos.

## Guía de Configuración e Inicio

### 1. Requisitos Previos
- Python 3.10 o superior.
- Git.
- Entorno Windows (comandos optimizados para PowerShell).

### 2. Instalación
Abre una terminal PowerShell y sigue estos pasos:

```powershell
# Clonar el repositorio y entrar a la carpeta
git clone https://github.com/benitezluciano/rosario-compras-sistema.git
cd rosario-compras-sistema

# Crear y activar el entorno virtual
python -m venv venv
.\venv\Scripts\Activate

# Instalar todas las dependencias (PyQt6, pandas, etc.)
pip install -r requirements.txt
```

### 3. Preparación de la Base de Datos
El archivo `main.py` se encarga de estructurar automáticamente las tablas si no existen. Sin embargo, para inicializar los datos de prueba y poder operar, ejecuta el *seeder*:
```powershell
python seed_db.py
```

### 4. Ejecución del Sistema
Para lanzar la interfaz de la aplicación:
```powershell
python main.py
```

## Modificando las Vistas (Qt Designer)
Los archivos visuales de la carpeta `src/views/` con extensión `.ui` pueden editarse visualmente (drag & drop) mediante Qt Designer. Si instalaste los requisitos del proyecto, puedes abrir el diseñador ejecutando en tu terminal con el entorno virtual activado:
```powershell
pyqt6-tools designer
```
