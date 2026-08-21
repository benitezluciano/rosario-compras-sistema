# Punto de Entrada (`main.py`)

## Propósito Principal
Es el ejecutable principal y punto de arranque de la aplicación "Rosario Compras". Se encarga de instanciar la ventana global, dibujar el menú de navegación lateral, inicializar todos los componentes MVC y gestionar la transición entre pantallas.

## Dependencias e Interacciones
- **Llama a**:
  - `inicializar_db` desde `src.database`.
  - Las 3 capas de los Casos de Uso integrados: Modelos, Vistas y Controladores.
  - Elementos de la librería GUI PyQt6 (`QApplication`, `QMainWindow`, `QListWidget`, `QStackedWidget`).
- **Es llamado por**: El usuario cuando inicia el sistema ejecutando `python main.py` desde la terminal.

## Componentes y Estructura Clave
- **Clase `MainWindow`**:
  - Hereda de `QMainWindow` y define el layout principal partido en dos: a la izquierda, un menú (`QListWidget`); a la derecha, un contenedor multicapa (`QStackedWidget`).
  - Efectúa la "Inyección de Dependencias" visual: para cada caso de uso, crea una instancia del Modelo, una instancia de la Vista, y se las pasa al Constructor del Controlador. Luego inserta la Vista al contenedor y conecta el click del menú al índice correspondiente.
- **Bloque Principal (`if __name__ == '__main__':`)**: 
  - Fuerzas la inicialización estructural de la Base de Datos.
  - Instancia el ciclo principal de PyQt (`QApplication.exec()`), reteniendo el programa corriendo en pantalla.
