# Manual de Usuario - Rosario Compras

Bienvenido al **Sistema de Gestión y Abastecimiento de Rosario Compras**. Esta aplicación permite gestionar de manera integral el circuito de compras consolidadas, centralizando las listas de proveedores, la toma y ajuste de pedidos de socios, el control cruzado de recepción y la emisión automática de remitos en PDF oficiales.

---

## 1. Roles y Permisos

| Rol | Nombre de Ejemplo | Email | Contraseña | Funciones |
| :--- | :--- | :--- | :--- | :--- |
| **`ejecutivo`** | Luciano Benítez (Ejecutivo Principal) | `ejecutivo@rosariocompras.com` | `account123` | Circuito completo de 3 módulos: Listas, Previsualización y Consolidado, y Recepción y Reparto con Remitos PDF. |
| **`ejecutivo`** | Martina Valenzuela (Ejecutiva Zona Norte) | `ejecutivo2@rosariocompras.com` | `account123` | Gestión de compras, ajuste de cantidades en matriz y remitos PDF. |
| **`admin`** | Administrador General | `admin@rosariocompras.com` | `admin123` | Control total, auditoría comercial y configuración de usuarios. |
| **`socio`** | Café Central (Socio 1) | `socio1@rosariocompras.com` | `socio123` | Gestión de pedidos: carga de pedido vigente, modificación interactiva e historial de pedidos. |
| **`socio`** | Panadería La Rosa (Socio 2) | `socio2@rosariocompras.com` | `socio123` | Gestión de pedidos: carga de pedido vigente, modificación interactiva e historial de pedidos. |
| **`socio`** | Restaurante Italia (Socio 3) | `socio3@rosariocompras.com` | `socio123` | Gestión de pedidos: carga de pedido vigente, modificación interactiva e historial de pedidos. |

---

## 2. Guía para el Socio (Business Partner)

### Pestaña 1: 🛍️ Pedido Vigente / Carga de Pedido
1. **Sin límites artificiales de cantidad:** Ingresa la cantidad deseada para cada producto.
2. **Pedido sin cerrar (Vigente):** Si ya confirmaste un pedido en el ciclo actual y continúa en estado *Pendiente*, el sistema lo cargará automáticamente indicando: *"Modificando Pedido Vigente #RC-ORD-XXXXXX"*.
3. **Modificación de Pedido:** Puedes alterar cualquier cantidad, agregar nuevos artículos o poner en 0 los que no desees, y presionar **"💾 Guardar Modificaciones del Pedido"**.
4. **Subtotales y Total General:** Se calculan en tiempo real a medida que editas cada fila.

### Pestaña 2: 📜 Historial de Mis Pedidos
1. **Monitoreo Completo:** Consulta tus pedidos pasados con su Nro. de Pedido seguro (`RC-ORD-XXXXXX`), fecha de registro, estado (`Pendiente`, `Consolidado`, `Procesado`), cantidad de productos y monto total estimado.
2. **Notificaciones y Remitos:** Recibirás alertas automáticas en la campana `🔔` ante modificaciones realizadas por el Ejecutivo, confirmación de consolidación y cuando tu **Remito oficial en PDF** esté generado.

---

## 3. Guía para el Ejecutivo de Cuentas y Administradores

El flujo operativo se organiza en **3 Módulos Principales**:

### Módulo 1: 📑 Listas y Proveedores
- **Solicitud de Cotización:** Presiona **"📧 Solicitar Lista"** para generar un email formal con membrete corporativo hacia el proveedor.
- **Previsualización Transparente con IVA:** Al cargar una planilla (.xlsx / .csv), la grilla desglosa:
  `Código` | `Detalle / Producto` | `Rubro` | **`Precio Base`** | **`Descuento (%)`** | **`Precio c/ Descuento`** | **`Precio + IVA (21%)`**.
- **Importación:** Presiona **"📥 Procesar e Importar al Catálogo Único"** para actualizar la base de datos y emitir un aviso automático masivo a todos los socios.

### Módulo 2: 📦 Previsualización y Consolidado (Por Proveedor)
- **Selección por Proveedor:** Selecciona el proveedor en el desplegable superior.
- **Grilla Matricial por Socio:**
  - Muestra: `Código`, `Artículo / Producto`, `Precio Unitario`, **`Total Cantidad (Suma de todos los socios)`**, y una columna individual para cada socio (sin columna `Rubro`).
- **Ajustes Ejecutivos por Disponibilidad (Regla 3a):**
  - Si el proveedor te informa limitaciones externas de stock, puedes editar directamente las cantidades de cualquier socio en la matriz.
  - La columna *Total Cantidad* se actualiza en tiempo real.
  - Al presionar **"💾 Guardar Modificaciones"**, se asientan los cambios y se notifica automáticamente al socio afectado explicando el ajuste.
- **Exportación y Despacho:**
  - **"📥 Órdenes por Proveedor (.xlsx)":** Genera un Excel independiente por cada proveedor con pedidos.
  - **"📊 Planilla Consolidada General (.xlsx)":** Planilla global multi-hoja.
  - **"🚀 Confirmar Consolidación y Despacho a Proveedores":** Pasa los pedidos a estado *Consolidado* y notifica a los socios.

### Módulo 3: 🚚 Recepción y Reparto Automático
- **Privacidad Comercial:** Todos los pedidos y comprobantes emplean identificadores seguros y ofuscados tipo UUID/Hash (`RC-ORD-XXXXXX`, `CMP-REC-XXXXXX`, `RC-REM-XXXXXX`).
- **Selección Multinivel:**
  - Selector de Proveedor.
  - Selector de **Nro. de Pedido Consolidado** (para gestionar entregas simultáneas de un mismo proveedor).
- **Comprobante Interno Automático:** El sistema autogenera el Nro. de Comprobante con formato UUID/Hash, sin requerir tipeo manual.
- **Doble Control:**
  - *Logística:* Cantidad Recibida física vs Cantidad Pedida.
  - *Compras:* Precio Facturado vs Precio Pactado.
- **Asentar Entrada:** Presiona **"💾 1. Asentar Entrada por Nro. de Comprobante y Registrar Stock Físico"**.
- **Reparto y Remitos PDF:** Presiona **"🚚 2. Ejecutar Reparto Automático y Generar Remitos PDF Oficiales"**:
  - Aplica prorrateo proporcional equitativo si hubo faltantes.
  - Emite **un Remito PDF oficial por cada proveedor para cada socio**, guardado en `remitos_pdf/`.
  - Notifica formalmente a cada socio con su remito emitido.
  - Botón **"📂 Ver Carpeta de Remitos PDF"** para abrir el directorio de documentos.

---

## 4. Preguntas Frecuentes (FAQ)

- **¿Dónde se guardan los Remitos PDF generados?** En la carpeta `remitos_pdf/` ubicada en la raíz del proyecto.
- **¿Por qué los números de pedido y remito tienen letras y números como RC-ORD-A7F9D2?** Son identificadores ofuscados basados en hash/UUID diseñados para preservar el secreto comercial de la empresa.
- **¿Cómo abrir el Manual Interactivo HTML?** Haz clic en el botón superior **"📖 Manual de Usuario"** dentro del sistema o abre `MANUAL_DE_USUARIO.html` en tu navegador.
