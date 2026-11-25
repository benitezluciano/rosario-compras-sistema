# Manual de Usuario - Rosario Compras

Bienvenido al **Sistema de Gestión y Abastecimiento de Rosario Compras**. Esta aplicación permite gestionar de manera integral el circuito de compras consolidadas por proveedor: listas de precios, pedidos de socios, consolidación con órdenes de compra, control cruzado de recepción, emisión de remitos estándar en PDF y consulta de historiales.

---

## 1. Roles y Permisos

| Rol | Nombre de Ejemplo | Email | Contraseña | Funciones |
| :--- | :--- | :--- | :--- | :--- |
| **`ejecutivo`** | Luciano Benítez (Ejecutivo Principal) | `ejecutivo@rosariocompras.com` | `account123` | Circuito completo de 3 módulos, historial de órdenes/remitos/comprobantes, ajuste de matriz y envío de órdenes por mail. |
| **`ejecutivo`** | Martina Valenzuela (Ejecutiva Zona Norte) | `ejecutivo2@rosariocompras.com` | `account123` | Gestión de compras, ajuste de cantidades en matriz y remitos PDF. |
| **`admin`** | Administrador General | `admin@rosariocompras.com` | `admin123` | Control total, auditoría comercial y seguimiento del circuito. |
| **`socio`** | Café Central (Socio 1) | `socio1@rosariocompras.com` | `socio123` | Gestión de pedidos por proveedor (hojas + Resumen), historial con Nota de Pedido PDF, remitos y datos fiscales. |
| **`socio`** | Panadería La Rosa (Socio 2) | `socio2@rosariocompras.com` | `socio123` | Gestión de pedidos por proveedor (hojas + Resumen), historial con Nota de Pedido PDF, remitos y datos fiscales. |
| **`socio`** | Restaurante Italia (Socio 3) | `socio3@rosariocompras.com` | `socio123` | Gestión de pedidos por proveedor (hojas + Resumen), historial con Nota de Pedido PDF, remitos y datos fiscales. |

---

## 2. Guía para el Socio

### Pantalla 1: 🛍️ Gestión de Pedidos
1. **Hojas por Proveedor (estilo Excel):** Cada proveedor con lista habilitada aparece en una pestaña inferior independiente. Cada pedido corresponde a **un socio y un proveedor**.
2. **Hoja `🧾 Resumen`:** La primera pestaña muestra en tiempo real todo lo cargado en todas las hojas, agrupado por proveedor con subtotales y total general.
3. **Pedido Vigente y Anulación:** Si ya enviaste un pedido para un proveedor y sigue `Pendiente`, la hoja muestra tus cantidades actuales para que puedas editarlas. Si dejas todas las cantidades en `0` y guardas, el pedido se anula previa confirmación.
4. **Envío Individual o Masivo:** Puedes enviar hoja por hoja o usar **"🛒 Enviar Todo"**, que muestra un resumen por proveedor antes de confirmar.

### Pantalla 2: 📜 Historial de Pedidos
1. **Filtros y Lista:** Filtra por proveedor, estado (*Pendiente*, *Enviado al proveedor*, *Entregado*) y rango de fechas.
2. **Detalle del Pedido:** Al seleccionar un pedido se muestran sus renglones con unidad, precio congelado, subtotal, cantidad entregada (si ya tiene remito) y, si el ejecutivo ajustó cantidades, la trazabilidad de la **cantidad original pedida**.
3. **Acciones:**
   - **"📄 Abrir Nota de Pedido (PDF)" / "💾 Guardar como…":** Genera la copia del pedido en PDF con precios.
   - **"🚚 Ver remito":** Abre (o regenera) el remito PDF oficial si ya fue entregado.
   - **"✏️ Modificar pedido":** Si sigue `Pendiente` y la lista está habilitada, te lleva directo a la hoja de ese proveedor.

### Pantalla 3: 🏢 Mis Datos Fiscales
- Permite cargar y actualizar tu **Nombre / Razón Social**, **C.U.I.T. / D.N.I.** (con validación de formato), **Condición frente al IVA** y **Domicilio de entrega**, utilizados en Notas de Pedido y Remitos.

---

## 3. Guía para el Ejecutivo de Cuentas y Administradores

### Módulo 1: 📑 Listas y Proveedores
- **Solicitud de Cotización:** Presiona **"📧 Solicitar Lista"** para enviar un email formal al proveedor.
- **Previsualización e Importación:** Carga planillas (`.xlsx` / `.csv`) desglosando `Precio Base`, `Descuento (%)`, `Precio c/ Descuento` y `Precio + IVA (21%)`. Los artículos se importan dentro del catálogo propio del proveedor.
- **Ciclo de Lista:** Usa **"Habilitar / Cerrar Lista"** para abrir o cerrar la carga de pedidos de los socios (notificándoles automáticamente).

### Módulo 2: 📦 Previsualización y Consolidado (Por Proveedor)
- **Grilla Matricial:** Selecciona un proveedor para ver sus pedidos pendientes en matriz (`Código`, `Artículo`, `Precio Unitario`, `Total Cantidad` y columnas por socio).
- **Ajustes Ejecutivos:** Puedes editar cantidades (incluso bajar a `0` o agregar ítems) conservando la cantidad original pedida por el socio. Al guardar se notifica automáticamente al socio afectado.
- **Consolidación y Orden de Compra:**
  - **"📊 Planilla Borrador del Proveedor":** Exporta un borrador interno antes de consolidar.
  - **"🚀 Consolidar y Generar Orden de Compra":** Pasa los pedidos a `Consolidado`, cierra la lista del proveedor, genera la Orden de Compra oficial en Excel (`RC-OC-XXXXXX`) en `ordenes_compra/` y permite abrirla o enviarla por correo al proveedor.

### Módulo 3: 🚚 Recepción y Reparto Automático
- **Selección Obligatoria por Proveedor y Pedido Consolidado:** Gestiona entregas por proveedor con comprobante interno (`CMP-REC-XXXXXX`).
- **Doble Control:** Verifica cantidades recibidas vs. pedidas y precio facturado vs. pactado.
- **Remitos Estándar (Letra X, `0001-00000001`):** Genera un remito PDF por pedido/proveedor (ORIGINAL y DUPLICADO) en `remitos_pdf/`, con descripción multilínea y notificación automática al socio.

### Módulo 4: 📜 Historial del Ejecutivo
- Reúne tres pestañas con filtros (incluido rango de fechas): **Órdenes de Compra** (con pedidos asociados e indicador de ajustes), **Remitos Emitidos** (con apertura/regeneración de PDF) y **Comprobantes de Proveedores** (resultado del doble control).
