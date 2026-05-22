# rosario-compras-sistema
Repositorioa creado para almacenar todos los datos correspondientes a este proyecto de la empresa Rosario Compras
## Estructura recomendada para este stack
Con Python + PyQt6 + SQLite, la arquitectura que mejor escala es MVC (Modelo - Vista - Controlador). Básicamente separás responsabilidades en tres capas:
rosario-compras/
│
├── db/
│   ├── rosario_compras.sql       ← script de creación
│   └── rosario_compras.db        ← ignorado por Git
│
├── src/
│   ├── models/                   ← capa de datos (habla con SQLite)
│   │   ├── __init__.py
│   │   ├── ejecutivo.py
│   │   ├── proveedor.py
│   │   ├── articulo.py
│   │   └── ...
│   │
│   ├── views/                    ← capa visual (ventanas PyQt6)
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── pedidos_view.py
│   │   └── ...
│   │
│   ├── controllers/              ← capa lógica (conecta modelo y vista)
│   │   ├── __init__.py
│   │   ├── pedido_controller.py
│   │   └── ...
│   │
│   └── database.py               ← conexión central a SQLite
│
├── main.py                       ← punto de entrada, arranca la app
├── .gitignore
├── README.md
└── requirements.txt
