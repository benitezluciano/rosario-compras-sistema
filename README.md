# Rosario Compras - Sistema de Gestión

Sistema de gestión y abastecimiento empresarial para la red **Rosario Compras**, desarrollado con arquitectura **MVC (Modelo - Vista - Controlador)** utilizando Python, PyQt6 y SQLite.

---

## 🚀 Inicio Rápido con Docker (Recomendado - Zero Config)

Tus colegas **no necesitan instalar Python, ni librerías, ni herramientas adicionales**. Solo requieren tener **Docker Desktop** instalado.

### 1. Clonar el repositorio y entrar a la carpeta:
```bash
git clone https://github.com/benitezluciano/rosario-compras-sistema.git
cd rosario-compras-sistema
```

### 2. Levantar el contenedor:
```bash
docker compose up --build
```

### 3. Abrir la aplicación:
Abre cualquier navegador web (Chrome, Edge, Firefox, Safari) en:
👉 **[http://localhost:8080](http://localhost:8080)** (o [http://localhost:8080/vnc.html](http://localhost:8080/vnc.html))

¡Y listo! La aplicación se ejecutará con su interfaz gráfica interactiva dentro del navegador, con la base de datos y todas sus dependencias configuradas automáticamente.

---

## 🛠️ Ejecución Local con Python (Método Tradicional)

Si prefieres ejecutar la aplicación de forma nativa en tu máquina:

### 1. Requisitos
- Python 3.10 o superior.
- Git.

### 2. Instalación
```powershell
# Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\Activate

# Instalar dependencias
pip install -r requirements.txt

# Poblar base de datos inicial
python seeds/seed_db.py

# Iniciar aplicación
python main.py
```

---

## 👥 Credenciales de Acceso para Pruebas

El sistema cuenta con autenticación segura y permisos diferenciados por rol:

| Rol | Nombre | Email | Contraseña | Permisos |
| :--- | :--- | :--- | :--- | :--- |
| **`ejecutivo`** | Ejecutivo de Cuentas | `ejecutivo@rosariocompras.com` | `account123` | Acceso a los 4 módulos del circuito completo y notificaciones. |
| **`admin`** | Administrador General | `admin@rosariocompras.com` | `admin123` | Acceso total y auditoría. |
| **`socio`** | Café Central (Socio 1) | `socio1@rosariocompras.com` | `socio123` | Carga de pedidos con filtro por proveedor y remitos de entrega. |
| **`socio`** | Panadería La Rosa (Socio 2) | `socio2@rosariocompras.com` | `socio123` | Carga de pedidos con filtro por proveedor y remitos de entrega. |
| **`socio`** | Restaurante Italia (Socio 3) | `socio3@rosariocompras.com` | `socio123` | Carga de pedidos con filtro por proveedor y remitos de entrega. |

---

## 🔄 Circuito Operativo (8 Pasos)

1. **Paso 1:** Proveedor entrega listas de precios en formato Excel o CSV.
2. **Paso 2:** Ejecutivo importa y unifica listas de precios en el Catálogo Único.
3. **Paso 3:** Socio consulta catálogo (filtra por proveedor) y confirma su pedido.
4. **Paso 4:** 🔔 Notificación automática al Ejecutivo con el nuevo pedido cargado.
5. **Paso 5:** Ejecutivo consolida la demanda y exporta Órdenes de Compra por Proveedor (`.xlsx`).
6. **Paso 6:** 🔔 Notificación automática al Socio: *"Pedido consolidado y enviado al proveedor"*.
7. **Paso 7:** Proveedor entrega mercadería: Ejecutivo asienta Factura/Remito con **Doble Control** (Precios por Compras y Cantidades por Logística) y actualiza stock.
8. **Paso 8:** Ejecutivo ejecuta **Reparto Automático** (aplica prorrateo equitativo ante faltantes), genera `REMITOS` oficiales y 🔔 notifica a cada socio.

> 📖 **Para ver la infografía y diagrama de secuencia completo**, abre el archivo `WALKTHROUGH.html` en tu navegador.

---

## 📁 Estructura del Proyecto

```text
rosario-compras-sistema/
├── Dockerfile                    # Configuración de contenedor con entorno gráfico noVNC
├── docker-compose.yml            # Orquestación de Docker lista para producción/desarrollo
├── entrypoint.sh                 # Script de arranque del display virtual y la app
├── WALKTHROUGH.html              # Documento visual con infografía y diagramas
├── WALKTHROUGH.md                # Documentación markdown del circuito
├── circuito_operativo.jpg        # Infografía gráfica del flujo de 8 pasos
├── db/
│   └── rosario_compras.sql       # Script DDL maestro con las 12 tablas
├── migrations/                   # Scripts incrementales de migración
├── src/
│   ├── models/                   # Modelos de negocio (Auth, Catálogo, Pedidos, Consolidación, Reparto, Notificaciones)
│   ├── views/                    # Vistas y archivos .ui de Qt Designer
│   ├── controllers/              # Controladores que conectan eventos y modelos
│   └── database.py               # Conexión SQLite transaccional
├── seeds/
│   └── seed_db.py                # Script para resetear y poblar datos iniciales
├── main.py                       # Punto de entrada principal
└── requirements.txt              # Dependencias del proyecto
```
