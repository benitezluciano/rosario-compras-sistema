# Plan de Implementación: Adición de Rol Admin, Sistema de Autenticación y Consolidación de Pedidos

Este plan define las modificaciones estructurales y funcionales para mantener los roles existentes (**`socio`** y **`ejecutivo`**) y agregar **`admin`**, implementar la pantalla de Login con 5 socios, 1 ejecutivo y 1 admin (con credenciales reales), control de sesión/logout con vistas restringidas por rol, y la adaptación del Caso de Uso 2 (CU-002) para generar y exportar la planilla consolidada a partir de los pedidos de los socios.

---

## Decisiones de Diseño y Alcance

> [!NOTE]
> - **Roles en el sistema**: `socio`, `ejecutivo`, `admin` (restricción `CHECK(role IN ('ejecutivo', 'socio', 'admin'))`).
> - **Permisos por Rol**:
>   - **`socio`**: Solo puede acceder a **Cargar Pedido (CU-001)** y sus pedidos se asocian a su propio `id_user`.
>   - **`ejecutivo`** y **`admin`**: Tienen acceso total. Gestionan la **Consolidación y Exportación de Planillas (CU-002)** y el **Reparto Automático (CU-003)**.
> - **Seguridad de contraseñas**: Se utilizará `werkzeug.security` (`generate_password_hash` / `check_password_hash`) para almacenar hashes seguros.

---

## Tabla de Credenciales de Prueba (Seeds)

Se creará la siguiente lista de usuarios en el seeder para pruebas completas:

| Rol | Nombre | Email | Contraseña |
| :--- | :--- | :--- | :--- |
| `admin` | Administrador General | `admin@rosariocompras.com` | `admin123` |
| `ejecutivo` | Ejecutivo de Cuentas | `ejecutivo@rosariocompras.com` | `account123` |
| `socio` | Café Central (Socio 1) | `socio1@rosariocompras.com` | `socio123` |
| `socio` | Panadería La Rosa (Socio 2) | `socio2@rosariocompras.com` | `socio123` |
| `socio` | Restaurante Italia (Socio 3) | `socio3@rosariocompras.com` | `socio123` |
| `socio` | Bar Pellegrini (Socio 4) | `socio4@rosariocompras.com` | `socio123` |
| `socio` | Hotel Rosario (Socio 5) | `socio5@rosariocompras.com` | `socio123` |

---

## Propuesta de Cambios

### 1. Base de Datos y Migraciones

#### [NEW] [0003_add_admin_role.sql](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/migrations/0003_add_admin_role.sql)
- Actualiza la restricción a `CHECK(role IN ('ejecutivo', 'socio', 'admin'))`.
- Preserva todos los registros existentes sin alterar nombres de roles.

#### [MODIFY] [rosario_compras.sql](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/db/rosario_compras.sql)
- Actualiza la definición DDL base de la tabla `USERS` a `CHECK(role IN ('ejecutivo', 'socio', 'admin'))`.

#### [MODIFY] [seed_db.py](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/seeds/seed_db.py)
- Inserta los 7 usuarios (1 admin, 1 ejecutivo, 5 socios) con contraseñas hasheadas y datos de catálogo/proveedores de prueba, asegurando que apunte a `database.db` en la raíz del proyecto.

---

### 2. Módulo de Autenticación y Control de Sesión

#### [NEW] [auth_model.py](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/src/models/auth_model.py)
- Método `autenticar_usuario(email, password)`: valida existencia del usuario por email y verifica el hash de la contraseña. Retorna `{id, nombre, email, role}` si es válido o mensaje de error.

#### [NEW] [login.ui](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/src/views/login.ui) y [login_view.py](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/src/views/login_view.py)
- Interfaz gráfica de Login con campos para Email, Contraseña (enmascarada con `QLineEdit.EchoMode.Password`), botón de "Iniciar Sesión" y etiquetas de validación.

#### [NEW] [auth_controller.py](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/src/controllers/auth_controller.py)
- Orquesta la vista de Login con el `AuthModel` y gestiona el flujo de acceso.

#### [MODIFY] [main.py](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/main.py)
- Muestra la pantalla de Login al arrancar.
- Una vez autenticado, carga la ventana principal con barra superior de sesión (*"Usuario: [Nombre] | Rol: [Rol]"*) y botón *"Cerrar Sesión"*.
- Lógica de permisos en el menú lateral:
  - **`socio`**: solo visualiza la opción "Cargar Pedido".
  - **`ejecutivo`** / **`admin`**: visualiza "Cargar Pedido", "Consolidar Planillas" y "Reparto Automático".
- Al pulsar *"Cerrar Sesión"*, limpia la sesión activa y retorna a la pantalla de Login.

---

### 3. Caso de Uso 1 (Carga de Pedido) - Contexto de Usuario

#### [MODIFY] [pedido_view.py](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/src/views/pedido_view.py) y [pedido_controller.py](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/src/controllers/pedido_controller.py)
- Asigna el `id_user` dinámicamente desde el usuario logueado en la sesión para que el pedido quede registrado al socio correspondiente.

---

### 4. Caso de Uso 2 (Consolidación y Exportación de Planilla)

#### [MODIFY] [consolidacion.ui](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/src/views/consolidacion.ui) y [consolidacion_view.py](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/src/views/consolidacion_view.py)
- Tabla para previsualizar los pedidos de los socios en estado `'Pendiente'`, totalizados por artículo y con detalle de cantidades por socio.
- Botón *"Exportar Planilla (.xlsx / .csv)"* con selector de ruta de guardado (`QFileDialog.getSaveFileName`).
- Botón *"Consolidar Pedidos"* para pasar los pedidos a estado `'Consolidado'`.

#### [MODIFY] [consolidacion_model.py](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/src/models/consolidacion_model.py)
- Método `obtener_pedidos_pendientes_agrupados()`: consulta SQL agrupando por artículo, proveedor y socios solicitantes.
- Método `exportar_planilla(ruta_archivo, formato='xlsx')`: genera archivo `.xlsx` o `.csv` utilizando `pandas` y `openpyxl`.
- Método `marcar_pedidos_como_consolidados()`: actualiza los pedidos en estado `'Pendiente'` a `'Consolidado'`.

#### [MODIFY] [consolidacion_controller.py](file:///c:/Users/Eros%20David/OneDrive/Documentos/projects/rosario-compras-sistema/src/controllers/consolidacion_controller.py)
- Conecta la vista con el modelo para previsualizar, exportar y asentar la consolidación en SQLite.

---

## Plan de Verificación

### 1. Verificación Automatizada
- Ejecutar la migración SQL y el script de seeders.
- Test de autenticación en Python verificando login correcto y rechazo de contraseñas incorrectas.
- Test de generación de archivo `.xlsx` / `.csv` desde el modelo de consolidación.

### 2. Verificación Manual en la Interfaz (UI)
1. **Prueba con Socio:**
   - Login con `socio1@rosariocompras.com` / `socio123`.
   - Verificar que solo ve "Cargar Pedido". Cargar un pedido de prueba y cerrar sesión.
2. **Prueba con Ejecutivo / Admin:**
   - Login con `ejecutivo@rosariocompras.com` / `account123`.
   - Ir a "Consolidar Planillas", previsualizar la tabla, exportar el archivo Excel y consolidar los pedidos.
   - Ir a "Reparto Automático" y verificar que los pedidos ahora consolidados pueden ser procesados.
