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
| Rol | Nombre | Email | Contraseña | Permisos |
| :--- | :--- | :--- | :--- | :--- |
| **`ejecutivo`** | Ejecutivo de Cuentas | `ejecutivo@rosariocompras.com` | `account123` | Acceso a los 3 módulos del circuito completo, ajuste de matriz y remitos PDF. |
| **`admin`** | Administrador General | `admin@rosariocompras.com` | `admin123` | Acceso total y auditoría de comprobantes y repartos. |
| **`socio`** | Café Central (Socio 1) | `socio1@rosariocompras.com` | `socio123` | Gestión de pedido vigente, historial y consulta de remitos. |
| **`socio`** | Panadería La Rosa (Socio 2) | `socio2@rosariocompras.com` | `socio123` | Gestión de pedido vigente, historial y consulta de remitos. |
| **`socio`** | Restaurante Italia (Socio 3) | `socio3@rosariocompras.com` | `socio123` | Gestión de pedido vigente, historial y consulta de remitos. |

---

## 🔄 Circuito Operativo y Módulos del Sistema

1. **📑 1. Listas y Proveedores:**
   - Solicitud formal de cotizaciones por email con membrete oficial.
   - Previsualización transparente de listas: **Precio Base**, **Descuento (%)**, **Precio con Descuento** y **Precio + IVA (21%)**.
   - Importación masiva al catálogo único y 🔔 notificación automática a todos los socios.

2. **🛍️ Portal del Socio (Gestión de Pedidos):**
   - **Pedido Vigente:** Carga sin restricciones de cantidad; si el pedido está sin cerrar (`Pendiente`), el socio puede reingresar y **modificar cantidades o artículos**.
   - **Historial de Pedidos:** Registro detallado de todos los pedidos anteriores con códigos comerciales seguros (`RC-ORD-XXXXXX`), fechas, estados y montos.

3. **📦 2. Previsualización y Consolidado (Por Proveedor):**
   - Unificación de la carga y consolidación para Ejecutivos y Administradores.
   - Selección central por Proveedor y visualización matricial: `Código`, `Artículo`, `Precio Unitario`, **`Total Cantidad (Suma de todos los socios)`**, y columnas individuales por socio (sin columna `Rubro`).
   - **Ajustes Ejecutivos (Regla 3a):** Modificación directa de cantidades en la matriz si el proveedor informa limitaciones externas, con notificación automática al socio afectado.
   - Exportación de órdenes de compra independientes por proveedor (`.xlsx`) y planilla general.
   - Despacho y pase a estado `Consolidado` con 🔔 notificación a cada socio.

4. **🚚 3. Recepción y Reparto Automático:**
   - **Privacidad Comercial:** Identificadores ofuscados en formato UUID/Hash para pedidos y comprobantes.
   - **Selección Multinivel:** Dropdowns por Proveedor y por Nro. de Pedido Consolidado (gestiona pedidos concurrentes a un mismo proveedor).
   - **Comprobante Interno Automático:** Nro. de Comprobante generado automáticamente (`CMP-REC-XXXXXX`) sin tipeo manual.
   - **Doble Control:** Verificación cruzada compras/logística y asentamiento de stock real.
   - **Emisión de Remitos Oficiales en PDF:** Generación automática de **un archivo PDF oficial por cada proveedor para cada socio involucrado**, guardados en `remitos_pdf/`.
   - 🔔 Notificación automática a cada socio con su remito PDF emitido y listo para entrega.

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
