# Rosario Compras - Sistema de Gestión

Sistema de gestión y abastecimiento empresarial para la red **Rosario Compras**, desarrollado con arquitectura **MVC (Modelo - Vista - Controlador)** utilizando Python, PyQt6 y SQLite.

---

## 📖 Manual de Usuario y Documentación

- **Manual Interactivo (Recomendado):** Abre **[`MANUAL_DE_USUARIO.html`](MANUAL_DE_USUARIO.html)** en cualquier navegador para ver la guía completa con navegación por rol, infografías y diagramas.
- **Manual en Markdown:** Consulta **[`MANUAL_DE_USUARIO.md`](MANUAL_DE_USUARIO.md)**.
- **Walkthrough del Circuito:** Consulta **[`WALKTHROUGH.html`](WALKTHROUGH.html)**.

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
| **`socio`** | Café Central (Socio 1) | `socio1@rosariocompras.com` | `socio123` | Carga de pedidos por proveedor y remitos de entrega. |
| **`socio`** | Panadería La Rosa (Socio 2) | `socio2@rosariocompras.com` | `socio123` | Carga de pedidos por proveedor y remitos de entrega. |
| **`socio`** | Restaurante Italia (Socio 3) | `socio3@rosariocompras.com` | `socio123` | Carga de pedidos por proveedor y remitos de entrega. |

---

## 🔄 Circuito Operativo (11 Pasos)

1. **Paso 1:** Ejecutivo solicita listas de precios a los Proveedores.
2. **Paso 2:** Proveedor entrega listas de precios en formato Excel o CSV.
3. **Paso 3:** Ejecutivo importa y consolida listas en el Catálogo Único.
4. **Paso 4:** 🔔 Notificación automática a los Socios: *"Catálogo y precios actualizados"*.
5. **Paso 5:** Socio consulta catálogo por proveedor y confirma su pedido.
6. **Paso 6:** 🔔 Notificación automática al Ejecutivo con el nuevo pedido cargado.
7. **Paso 7:** Ejecutivo consolida la demanda y exporta Órdenes de Compra por Proveedor (`.xlsx`).
8. **Paso 8 y 9:** Ejecutivo envía órdenes a proveedores y 🔔 se notifica al Socio: *"Pedido enviado al proveedor"*.
9. **Paso 10:** Llega la mercadería física: Ejecutivo asienta Factura/Remito con **Doble Control** (Precios por Compras y Cantidades por Logística) y actualiza stock.
10. **Paso 11 y 12:** Ejecutivo ejecuta **Reparto Automático** (prorrateo ante faltantes), genera `REMITOS` oficiales y 🔔 notifica a cada socio.

---

## 📁 Estructura del Proyecto

```text
rosario-compras-sistema/
├── Dockerfile                    # Contenedor con entorno gráfico noVNC
├── docker-compose.yml            # Orquestación de Docker lista para usar
├── entrypoint.sh                 # Script de arranque del display virtual y la app
├── MANUAL_DE_USUARIO.html        # Manual de usuario interactivo y completo
├── MANUAL_DE_USUARIO.md          # Manual de usuario en formato Markdown
├── WALKTHROUGH.html              # Documento visual con infografía y diagramas
├── WALKTHROUGH.md                # Documentación técnica del circuito
├── circuito_operativo.jpg        # Infografía gráfica del flujo operativo
├── db/
│   └── rosario_compras.sql       # Script DDL maestro con las 12 tablas
├── migrations/                   # Scripts incrementales de migración
├── src/
│   ├── models/                   # Modelos de negocio (Auth, Catálogo, Pedidos, Consolidación, Reparto, Notificaciones)
│   ├── views/                    # Vistas y archivos .ui de Qt Designer
│   ├── controllers/              # Controladores que conectan eventos y modelos
│   ├── styles/                   # Sistema de estilos QSS (theme.py)
│   └── database.py               # Conexión SQLite transaccional
├── seeds/
│   └── seed_db.py                # Script para resetear y poblar datos iniciales
├── main.py                       # Punto de entrada principal con tema moderno
└── requirements.txt              # Dependencias del proyecto
```
