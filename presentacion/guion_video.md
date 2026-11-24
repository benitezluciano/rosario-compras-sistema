# Guion del video del prototipo

Video de 2:10 para la diapositiva 7. Se pasa mudo y se narra en vivo, así no depende del audio del aula y se puede ajustar el ritmo. Cada escena trae una narración de unas 45 palabras.

La historia es una sola: un proveedor (Lácteos del Litoral) y un producto (mozzarella). El socio que pide al principio es el mismo que recibe un faltante al final.

## Antes de grabar

1. Resetear la base con `python seeds/seed_db.py`. **Borra todos los datos de `database.db`**: si hace falta conservar la actual, copiarla antes.
2. Con el seed, Lácteos del Litoral ya tiene 4 pedidos pendientes (Café Central, Panadería La Rosa, Restaurante Italia y Pizzería La Popular). El video agrega un quinto: Gran Hotel Rosario.
3. Usar el botón "⚡ Autocompletar usuario de prueba" de la pantalla de login.
4. Habrá 3 inicios de sesión: socio5 (Gran Hotel), el ejecutivo y otra vez socio5.
5. Grabar a 1080p, con las notificaciones de Windows apagadas, y recortar las esperas al editar.

## Escenas

### 1. El socio pide (0:00–0:20)
- **Login:** socio5, Gran Hotel Rosario.
- **Pantalla:** "Gestión de Pedidos", pestaña inferior "Lácteos del Litoral".
- **Acción:** Mozzarella en Barra x 4kg, cantidad 4, y clic en "Enviar Pedido de esta Hoja".
- **Narración:** "Hoy el socio arma su pedido en un Excel propio y lo manda por mail. Acá entra con su usuario, ve solo las listas habilitadas con el precio final negociado, carga cantidades y envía. Un pedido por proveedor, sin planillas ni correos."

### 2. El ejecutivo ve todo consolidado (0:20–0:45)
- **Login:** ejecutivo.
- **Pantalla:** "2. Previsualización y Consolidado", proveedor Lácteos del Litoral.
- **Acción:**
  1. Mostrar la matriz con una columna por socio y el total. Señalar la fila de mozzarella, total 12.
  2. Editar la leche de Café Central de 25 a 20 y ver cómo se recalcula el total.
  3. Clic en "Guardar Modificaciones (Notificar a Socios)".
- **Narración:** "El ejecutivo recibe la consolidación ya hecha: una fila por artículo, una columna por socio y el total. El proveedor avisó que tiene cupo limitado de leche. El ejecutivo ajusta de 25 a 20 y el socio recibe el aviso. No tipea ni imprime nada."

### 3. Consolidar y enviar la orden de compra (0:45–1:00)
- **Acción:**
  1. Clic en "Consolidar y Generar Orden de Compra" y se abre el diálogo con el número RC-OC.
  2. Clic en "Abrir archivo" (mostrar 3 segundos del Excel).
  3. Clic en "Enviar al proveedor" y, en la vista previa del mail, "Enviar Correo". Queda en modo simulación.
- **Narración:** "Al consolidar se cierra la lista de ese proveedor y se genera la orden de compra en Excel, con los totales por artículo. Sale al proveedor desde el mismo sistema y los socios reciben el aviso de que su pedido fue enviado."

### 4. Recepción con doble control (1:00–1:25)
- **Pantalla:** "3. Recepción y Reparto Automático", proveedor Lácteos y el pedido consolidado.
- **Acción:**
  1. Cargar lo recibido: leche 20, manteca 5, dulce de leche 2 y mozzarella 9.
  2. Cargar el precio facturado de la mozzarella en $23.000, por encima del pactado.
  3. Mostrar las alertas de faltante y de diferencia de precio en la columna de estado.
  4. Mostrar el comprobante CMP-REC generado solo.
  5. Clic en "1. Asentar Entrada…".
- **Narración:** "Cuando llega el camión se registra la recepción con doble control: lo pedido contra lo recibido, y el precio pactado contra el facturado. El sistema marca renglón por renglón. Acá faltan 3 de mozzarella y el proveedor facturó más caro. El comprobante interno se genera solo."

### 5. Reparto automático (1:25–1:45)
- **Acción:**
  1. Clic en "2. Ejecutar Reparto Automático y Generar Remitos PDF Oficiales".
  2. Aparece el diálogo con los ajustes por prorrateo.
  3. Confirmar con "Sí" y aparece "Operación Exitosa".
- **Narración:** "Con la mercadería asentada, un clic reparte. Como faltan tres unidades, el sistema aplica una sola regla, proporcional e igual para todos. Antes de emitir, le pide confirmación al ejecutivo."
- **Resultado esperado:** Restaurante Italia 2 de 3, Pizzería La Popular 4 de 5 y Gran Hotel 3 de 4.

### 6. Remito y vista del socio (1:45–2:10)
- **Acción:**
  1. En "Historial", pestaña "Remitos Emitidos", clic en "Abrir PDF del Remito" del Gran Hotel. Mostrar la letra X, original y duplicado, y que no tiene precios.
  2. Cerrar sesión e ingresar como socio5.
  3. En "Historial de Pedidos", abrir el pedido: estado "Entregado", columna Entregado resaltada (3 contra 4 pedidos) y clic en "Ver remito".
- **Narración:** "El remito sale en PDF al instante, con original y duplicado, y el depósito ya puede armar los palets. El socio ve en su historial qué pidió, qué recibió y descarga su remito, sin llamar ni esperar."
- **Cierre:** una tarjeta de 5 segundos con "Del pedido al remito, sin planillas".

## Para verificar en el ensayo

- **Reparto:** el 2 / 4 / 3 se calculó a mano con la regla del documento 05 (RN-07: piso de stock × pedido ÷ total y las unidades restantes por mayor parte fraccionaria). Confirmar que el sistema da lo mismo.
- **Escena 4:** comprobar cómo aparece el pedido consolidado en el desplegable (por pedido o por orden).
- **Escena 6:** probar si el PDF abre rápido. Si tarda, grabar esa parte aparte.
- **Si la base no queda como se espera:** volver a correr el seed y empezar de nuevo.
