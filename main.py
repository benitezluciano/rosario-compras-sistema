import sys
from PyQt6.QtWidgets import QApplication, QMainWindow

def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Rosario Compras")
    window.resize(1024, 768)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()