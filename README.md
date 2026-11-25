# Rosario Compras - Sistema de Gestión

Sistema de gestión y abastecimiento empresarial para la red **Rosario Compras**, desarrollado con arquitectura **MVC (Modelo - Vista - Controlador)** utilizando Python, PyQt6 y SQLite.

---

## 📖 Manual de Usuario y Documentación

- **Manual Interactivo (Recomendado):** Abre **[`MANUAL_DE_USUARIO.html`](MANUAL_DE_USUARIO.html)** en cualquier navegador (o desde el botón **📖 Manual de Usuario** dentro de la app).
- **Manual en Markdown:** Consulta **[`MANUAL_DE_USUARIO.md`](MANUAL_DE_USUARIO.md)**.
- **Walkthrough del Circuito:** Consulta **[`WALKTHROUGH.md`](WALKTHROUGH.md)** y **[`WALKTHROUGH.html`](WALKTHROUGH.html)**.

---

## 🚀 Inicio Rápido con Docker (Recomendado - Zero Config)

Tus colegas **no necesitan instalar Python, ni librerías, ni herramientas adicionales**. Solo requieren tener **Docker Desktop** instalado.

```bash
git clone https://github.com/benitezluciano/rosario-compras-sistema.git
cd rosario-compras-sistema
docker compose up --build
```

Luego abre **[http://localhost:8080](http://localhost:8080)** (o [http://localhost:8080/vnc.html](http://localhost:8080/vnc.html)) en tu navegador.

---

## 🛠️ Ejecución Local con Python (Método Tradicional)

### 1. Requisitos
- Python 3.10 o superior.
- Git.

### 2. Instalación y Arranque
```powershell
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
python seeds/seed_db.py
python main.py
```

---

## 👥 Credenciales de Acceso para Pruebas

| Rol | Nombre | Email | Contraseña | Permisos |
| :--- | :--- | :--- | :--- | :--- |
| **`ejecutivo`** | Ejecutivo de Cuentas | `ejecutivo@rosariocompras.com` | `account123` | Circuito de 3 módulos, historial de órdenes/remitos/comprobantes, ajuste de matriz y envío de órdenes por correo. |
| **`admin`** | Administrador General | `admin@rosariocompras.com` | `admin123` | Acceso total y auditoría de comprobantes, órdenes y repartos. |
| **`socio`** | Café Central (Socio 1) | `socio1@rosariocompras.com` | `socio123` | Gestión de pedidos por proveedor (hojas + Resumen), historial con Nota de Pedido PDF, remitos y datos fiscales. |
| **`socio`** | Panadería La Rosa (Socio 2) | `socio2@rosariocompras.com` | `socio123` | Gestión de pedidos por proveedor (hojas + Resumen), historial con Nota de Pedido PDF, remitos y datos fiscales. |
| **`socio`** | Restaurante Italia (Socio 3) | `socio3@rosariocompras.com` | `socio123` | Gestión de pedidos por proveedor (hojas + Resumen), historial con Nota de Pedido PDF, remitos y datos fiscales. |

---

## 🔄 Circuito Operativo y Módulos del Sistema

1. **📑 1. Listas y Proveedores (Ejecutivo):**
   - Solicitud formal de cotizaciones por email con membrete oficial.
   - Previsualización transparente de listas: **Precio Base**, **Descuento (%)**, **Precio con Descuento** y **Precio + IVA (21%)**.
   - Importación al catálogo propio del proveedor y ciclo de habilitación/cierre (**Habilitar / Cerrar Lista**) con 🔔 notificación automática a los socios.

2. **🛍️ Portal del Socio (Gestión de Pedidos, Historial y Datos Fiscales):**
   - **Hojas estilo Excel + Hoja `🧾 Resumen`:** Una hoja independiente por cada lista habilitada (un pedido por socio y proveedor), una primera hoja resumen de solo lectura y botón **"Enviar Todo"** con confirmación previa.
   - **Historial de Pedidos:** Filtros por proveedor, estado y rango de fechas; detalle por renglón (incluyendo cantidad original vs. ajustada por el ejecutivo y cantidad entregada), **Nota de Pedido en PDF**, acceso al remito y botón **"Modificar pedido"** mientras siga `Pendiente`.
   - **Mis Datos Fiscales:** Pantalla propia para editar nombre/razón social, CUIT/DNI, condición frente al IVA y domicilio de entrega.

3. **📦 2. Previsualización y Consolidado (Por Proveedor):**
   - Selección por proveedor con visualización matricial: `Código`, `Artículo`, `Precio Unitario`, **`Total Cantidad`**, y columnas editables por socio.
   - **Ajustes Ejecutivos:** Modificación de cantidades en la matriz con trazabilidad de la cantidad original pedida por el socio y notificación automática.
   - **Consolidación y Orden de Compra:** Cierra la lista del proveedor, genera la **Orden de Compra en Excel (`RC-OC-XXXXXX`)** en `ordenes_compra/`, la registra en la base (`ORDENES_COMPRA`) y permite enviarla por correo al proveedor. También permite exportar la **Planilla Borrador del Proveedor**.

4. **🚚 3. Recepción y Reparto Automático:**
   - Selección obligatoria por proveedor y pedido consolidado.
   - **Doble Control:** Verificación cruzada de cantidades y precios contra comprobantes recibidos (`CMP-REC-XXXXXX`).
   - **Remitos Estándar (Letra X, `0001-00000001`):** Un remito por pedido/proveedor con ORIGINAL y DUPLICADO en `remitos_pdf/` (regenerable desde el historial) y 🔔 notificación al socio.

5. **📜 Historial del Ejecutivo:**
   - Tres pestañas con filtros por proveedor, estado/socio/control y rango de fechas: **Órdenes de Compra**, **Remitos Emitidos** y **Comprobantes de Proveedores**.

---

## 🧪 Pruebas y Verificación

```powershell
# Suite integral del circuito (base temporal, no toca database.db)
python tests/test_circuit_suite.py

# Pruebas de proveedores, importación y EmailService (base temporal)
python tests/test_proveedores_email.py

# Verificación de compilación
python -m compileall -q main.py src seeds tests
```

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
├── db/
│   └── rosario_compras.sql       # Script DDL maestro con las 13 tablas
├── gestion/                      # Estado, decisiones (DEC-001+) y bitácora de sesiones
├── migrations/                   # Scripts incrementales de migración
├── src/
│   ├── config/                   # Datos del emisor y configuración de remitos (empresa.py)
│   ├── models/                   # Modelos de negocio (MVC)
│   ├── views/                    # Vistas PyQt6 y archivos .ui
│   ├── controllers/              # Controladores MVC
│   ├── services/                 # Servicios de PDF, Excel de Órdenes de Compra y Email
│   ├── styles/                   # Sistema de estilos QSS (theme.py)
│   └── database.py               # Conexión SQLite transaccional y migrar_db
├── seeds/                        # seed_db.py y limpiar_db.py
├── tests/                        # test_circuit_suite.py y test_proveedores_email.py
├── main.py                       # Punto de entrada principal
└── requirements.txt              # Dependencias directas del proyecto
```
