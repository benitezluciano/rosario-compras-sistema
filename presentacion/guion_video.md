# Guion del video del prototipo

Video de unos 2:35 para la diapositiva 7. Se pasa mudo y se narra en vivo, así no depende del audio del aula y se puede ajustar el ritmo. Cada escena trae una narración de unas 40 a 45 palabras. Los tiempos son una estimación: se miden y se ajustan en el ensayo.

La historia es una sola: un proveedor (Lácteos del Litoral) y un producto (mozzarella). El socio que pide al principio es el mismo que recibe un faltante al final.

## Antes de grabar

1. Resetear la base con `python seeds/seed_db.py`. **Borra todos los datos de `database.db`**: si hace falta conservar la actual, copiarla antes.
2. Con el seed, Lácteos del Litoral ya tiene pedidos pendientes de otros socios (Café Central, Panadería La Rosa, Restaurante Italia y Pizzería La Popular). El video agrega uno más: Gran Hotel Rosario. **Verificar en el ensayo** que el seed actual (Eros lo modificó el 24/11) sigue dejando esos pedidos.
3. Para la escena 1 hace falta el archivo `ejemplos_listas_precios/2_lacteos_del_litoral.xlsx`. Tenerlo a mano en el selector de archivos.
4. Usar el botón "⚡ Autocompletar usuario de prueba" de la pantalla de login.
5. Habrá 4 inicios de sesión: el ejecutivo (escena 1), socio5 (escena 2), otra vez el ejecutivo (escenas 3 a 7) y socio5 al final de la escena 7. Para ahorrar cambios de sesión se puede grabar por usuario y ordenar al editar.
6. Grabar a 1080p, con las notificaciones de Windows apagadas, y recortar las esperas al editar.

## Escenas

### 1. El ejecutivo carga la lista de precios (0:00–0:25)
- **Login:** ejecutivo.
- **Pantalla:** "Gestión de Listas de Precios y Catálogo Único", proveedor Lácteos del Litoral.
- **Acción:**
  1. Clic en "Seleccionar Planilla (.xlsx / .csv)" y elegir `2_lacteos_del_litoral.xlsx`.
  2. Mostrar 3 segundos la tabla de previsualización con los precios con descuento y con IVA.
  3. Clic en "📥 Procesar e Importar al Catálogo Único (Notifica a Socios)". Aparece el mensaje de éxito.
- **Narración:** "Todo empieza con la lista de precios que negoció el ejecutivo. La carga, ve la previsualización con el precio final de cada artículo y la procesa. Al importarla, la lista queda habilitada y todos los socios reciben el aviso."
- **Nota:** importar ya habilita la lista (el botón "Habilitar Lista" solo aparece si la lista está cerrada). Si se quiere mostrar esa acción aparte, cerrar la lista antes de grabar y habilitarla con ese botón: suma unos 10 segundos.

### 2. El socio pide (0:25–0:45)
- **Login:** socio5, Gran Hotel Rosario.
- **Pantalla:** "Gestión de Pedidos", pestaña inferior "Lácteos del Litoral".
- **Acción:** Mozzarella en Barra x 4kg, cantidad 4, y clic en "Enviar Pedido de esta Hoja".
- **Narración:** "Hoy el socio arma su pedido en un Excel propio y lo manda por mail. Acá entra con su usuario, ve solo las listas habilitadas con el precio final negociado, carga cantidades y envía. Un pedido por proveedor, sin planillas ni correos."

### 3. El ejecutivo ve todo consolidado (0:45–1:10)
- **Login:** ejecutivo.
- **Pantalla:** "2. Previsualización y Consolidado", proveedor Lácteos del Litoral.
- **Acción:**
  1. Mostrar la matriz con una columna por socio y el total. Señalar la fila de mozzarella, total 12.
  2. Editar la leche de Café Central de 25 a 20 y ver cómo se recalcula el total.
  3. Clic en "Guardar Modificaciones (Notificar a Socios)".
- **Narración:** "El ejecutivo recibe la consolidación ya hecha: una fila por artículo, una columna por socio y el total. El proveedor avisó que tiene cupo limitado de leche. El ejecutivo ajusta de 25 a 20 y el socio recibe el aviso. No tipea ni imprime nada."

### 4. Consolidar y enviar la orden de compra (1:10–1:25)
- **Acción:**
  1. Clic en "Consolidar y Generar Orden de Compra" y se abre el diálogo con el número RC-OC.
  2. Clic en "Abrir archivo" (mostrar 3 segundos del Excel).
  3. Clic en "Enviar al proveedor" y, en la vista previa del mail, "Enviar Correo". Queda en modo simulación.
- **Narración:** "Al consolidar se cierra la lista de ese proveedor y se genera la orden de compra en Excel, con los totales por artículo. El ejecutivo la envía al proveedor desde el mismo sistema y los socios reciben el aviso de que su pedido fue enviado."

### 5. Recepción con doble control (1:25–1:50)
- **Pantalla:** "3. Recepción y Reparto Automático", proveedor Lácteos y el pedido consolidado.
- **Acción:**
  1. Cargar lo recibido: leche 20, manteca 5, dulce de leche 2 y mozzarella 9.
  2. Cargar el precio facturado de la mozzarella en $23.000, por encima del pactado.
  3. Mostrar las alertas de faltante y de diferencia de precio en la columna de estado.
  4. Mostrar el comprobante CMP-REC generado solo.
  5. Clic en "1. Asentar Entrada…".
- **Narración:** "Cuando llega el camión se registra la recepción con doble control: lo pedido contra lo recibido, y el precio pactado contra el facturado. El sistema marca renglón por renglón. Acá faltan 3 de mozzarella y el proveedor facturó más caro. El comprobante interno se genera solo."

### 6. Reparto automático (1:50–2:10)
- **Acción:**
  1. Clic en "2. Ejecutar Reparto Automático y Generar Remitos PDF Oficiales".
  2. Aparece el diálogo con los ajustes por prorrateo.
  3. Confirmar con "Sí" y aparece "Operación Exitosa".
- **Narración:** "Con la mercadería asentada, un clic reparte. Como faltan tres unidades, el sistema aplica una sola regla, proporcional e igual para todos. Antes de emitir, le pide confirmación al ejecutivo."
- **Resultado esperado:** Restaurante Italia 2 de 3, Pizzería La Popular 4 de 5 y Gran Hotel 3 de 4.

### 7. Remito y vista del socio (2:10–2:35)
- **Acción:**
  1. En "Historial", pestaña "Remitos Emitidos", clic en "Abrir PDF del Remito" del Gran Hotel. Mostrar la letra X, original y duplicado, y que no tiene precios.
  2. Cerrar sesión e ingresar como socio5.
  3. En "Historial de Pedidos", abrir el pedido: estado "Entregado", columna Entregado resaltada (3 contra 4 pedidos) y clic en "Ver remito".
- **Narración:** "El remito sale en PDF al instante, con original y duplicado, y el depósito ya puede armar los palets. El socio ve en su historial qué pidió, qué recibió y descarga su remito, sin llamar ni esperar."
- **Cierre:** una tarjeta de 5 segundos con "Del pedido al remito, sin planillas".

## Para verificar en el ensayo

- **Escena 1:** que el archivo de ejemplo de Lácteos importe sin errores sobre la base del seed, que los precios no cambien lo que se espera en la escena 5 (precio pactado de la mozzarella) y que las columnas de la previsualización se vean legibles en pantalla. Al importar, los pedidos pendientes toman los precios de la lista (DEC-011).
- **Reparto:** el 2 / 4 / 3 se calculó a mano con la regla del documento 05 (RN-07: piso de stock × pedido ÷ total y las unidades restantes por mayor parte fraccionaria). Confirmar que el sistema da lo mismo.
- **Escena 5:** comprobar cómo aparece el pedido consolidado en el desplegable (por pedido o por orden).
- **Escena 7:** probar si el PDF abre rápido. Si tarda, grabar esa parte aparte.
- **Duración total:** medir y recortar. Las escenas 2 y 7 son las que más se pueden resumir.
- **Si la base no queda como se espera:** volver a correr el seed y empezar de nuevo.
