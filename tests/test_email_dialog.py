import sys
import os
import unittest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.views.email_preview_dialog import EmailPreviewDialog, EmailWorkerThread
from src.services.email_service import EmailService

# Instanciar QApplication para pruebas de widgets de PyQt
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

class TestEmailDialog(unittest.TestCase):
    def setUp(self):
        self.email_service = EmailService.get_instance()
        self.destinatario = "test@proveedormock.com"
        self.asunto = "Asunto de Prueba de Integración"
        self.cuerpo_html = "<p>Contenido de prueba</p>"

    def test_worker_thread_signal(self):
        """Prueba que EmailWorkerThread emita la señal correctamente."""
        worker = EmailWorkerThread(
            email_service=self.email_service,
            destinatario=self.destinatario,
            asunto=self.asunto,
            cuerpo_html=self.cuerpo_html
        )
        
        resultado = []
        def on_terminado(exito, mensaje):
            resultado.append((exito, mensaje))
            app.quit()

        worker.envio_terminado.connect(on_terminado)
        worker.start()
        
        # Ejecutar el loop hasta que el hilo termine
        app.exec()
        
        self.assertEqual(len(resultado), 1)
        exito, msg = resultado[0]
        self.assertTrue(exito)
        self.assertIn("MODO SIMULACION", msg)
        print("OK: EmailWorkerThread ejecutó y emitió pyqtSignal en el Main Thread con éxito.")

    def test_dialog_simulation_send(self):
        """Prueba que el diálogo ejecute el envío y cierre con Accept de forma segura."""
        dialog = EmailPreviewDialog(
            destinatario=self.destinatario,
            asunto=self.asunto,
            cuerpo_html=self.cuerpo_html
        )
        
        # Al abrir, programar el clic en enviar tras 50ms
        QTimer.singleShot(50, dialog.ejecutar_envio)
        
        # Ejecutar modal dialog
        res = dialog.exec()
        
        self.assertEqual(res, EmailPreviewDialog.DialogCode.Accepted)
        self.assertTrue(dialog.resultado_exito)
        self.assertIn("MODO SIMULACION", dialog.resultado_mensaje)
        print("OK: EmailPreviewDialog ejecutó el envío asíncrono y cerró limpiamente sin colgar la GUI.")

if __name__ == '__main__':
    unittest.main()
