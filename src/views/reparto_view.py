import os
from PyQt6.QtWidgets import QWidget, QMessageBox, QTableWidgetItem
from PyQt6.QtCore import Qt
from PyQt6 import uic

class RepartoView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Obtiene la ruta absoluta de reparto_automatico.ui en esta misma carpeta
        ui_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reparto_automatico.ui")
        
        # Carga el diseño .ui en esta instancia de QWidget
        uic.loadUi(ui_path, self)

    def cargar_pedidos(self, lista_pedidos):
        """
        Llena la tabla_pedidos con la lista de pedidos pendientes o consolidados.
        Cada pedido debe tener: socio_nombre, resumen_articulos, y estado.
        """
        self.tabla_pedidos.setRowCount(len(lista_pedidos))
        
        for row, pedido in enumerate(lista_pedidos):
            # Columna 0: Socio (Nombre del usuario)
            item_socio = QTableWidgetItem(pedido['socio_nombre'])
            item_socio.setFlags(item_socio.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_pedidos.setItem(row, 0, item_socio)
            
            # Columna 1: Artículos (Texto consolidado ej: "Café x5, Leche x10")
            resumen = pedido.get('resumen_articulos') or ""
            item_articulos = QTableWidgetItem(resumen)
            item_articulos.setFlags(item_articulos.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_pedidos.setItem(row, 1, item_articulos)
            
            # Columna 2: Estado (Pendiente, Consolidado, etc.)
            item_estado = QTableWidgetItem(pedido['estado'])
            item_estado.setFlags(item_estado.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla_pedidos.setItem(row, 2, item_estado)

        # Ajustar automáticamente el ancho de la columna de artículos que tiene textos más largos
        self.tabla_pedidos.resizeColumnToContents(1)

    def actualizar_estado_interfaz(self, estado):
        """Actualiza la etiqueta de estado de asignación en la UI."""
        self.lbl_estado_asignacion.setText(f"Estado actual: {estado}")

    def mostrar_mensaje_exito(self, mensaje):
        """Muestra una ventana emergente de éxito logístico."""
        QMessageBox.information(self, "Reparto Procesado", mensaje)

    def mostrar_mensaje_error(self, mensaje):
        """Muestra una ventana emergente de alerta/error en caso de discrepancias de stock."""
        QMessageBox.critical(self, "Error en Reparto", mensaje)

    def mostrar_alerta_ajuste(self, discrepancias):
        """
        Muestra un cuadro de diálogo con los artículos que tienen faltante y la 
        propuesta de ajuste proporcional equitativo.
        Pregunta al usuario si acepta el ajuste o cancela la operación.
        """
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle("Discrepancia de Stock - Excepción E1")
        box.setText("Se detectaron faltantes de stock en artículos de los pedidos consolidados.")
        
        detalle_texto = "Artículos con demanda superior al stock físico disponible:\n\n"
        for disc in discrepancias:
            detalle_texto += (
                f"• {disc['detalle']}:\n"
                f"  - Demandado: {disc['solicitado']} uds.\n"
                f"  - Disponible en stock: {disc['disponible']} uds.\n"
                f"  - Propuesta: Ajustar y prorratear proporcionalmente.\n\n"
            )
        detalle_texto += "¿Desea aplicar la propuesta de ajuste automático y continuar con el reparto?"
        box.setInformativeText(detalle_texto)
        
        # Añadir botones personalizados
        btn_aceptar = box.addButton("Aceptar Ajuste", QMessageBox.ButtonRole.YesRole)
        btn_cancelar = box.addButton("Cancelar", QMessageBox.ButtonRole.NoRole)
        
        box.exec()
        
        if box.clickedButton() == btn_aceptar:
            return True
        return False
