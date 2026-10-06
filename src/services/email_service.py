import os
import smtplib
import ssl
import threading
from email.message import EmailMessage
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class EmailService:
    _instancia = None

    @classmethod
    def get_instance(cls):
        if cls._instancia is None:
            cls._instancia = EmailService()
        return cls._instancia

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "True").lower() in ("true", "1", "yes")
        self.from_name = os.getenv("EMAIL_FROM_NAME", "Rosario Compras - Sistema de Gestión")
        self.from_address = os.getenv("EMAIL_FROM_ADDRESS", self.smtp_user or "notificaciones@rosariocompras.com")
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        os.makedirs(self.log_dir, exist_ok=True)

    def esta_configurado(self):
        """Retorna True si las credenciales SMTP están completas."""
        return bool(self.smtp_host and self.smtp_user and self.smtp_password)

    def enviar_correo_async(self, destinatario, asunto, cuerpo_html, cuerpo_texto="", adjuntos=None, callback=None):
        """
        Envía un correo de forma asíncrona en un hilo secundario
        para evitar congelar la interfaz gráfica de PyQt6.
        callback(exito: bool, mensaje: str) es llamado al finalizar.
        """
        hilo = threading.Thread(
            target=self._enviar_correo_sync,
            args=(destinatario, asunto, cuerpo_html, cuerpo_texto, adjuntos, callback),
            daemon=True
        )
        hilo.start()

    def _enviar_correo_sync(self, destinatario, asunto, cuerpo_html, cuerpo_texto="", adjuntos=None, callback=None):
        """Lógica síncrona interna de envío de correo."""
        if not destinatario:
            if callback:
                callback(False, "No se especificó dirección de correo destinataria.")
            return

        # Si no hay credenciales SMTP configuradas, usamos el MODO SIMULACIÓN SEGURO
        if not self.esta_configurado():
            exito, msg = self._registrar_simulacion(destinatario, asunto, cuerpo_html, adjuntos)
            if callback:
                callback(exito, msg)
            return

        try:
            msg = EmailMessage()
            msg["Subject"] = asunto
            msg["From"] = f"{self.from_name} <{self.from_address}>"
            msg["To"] = destinatario

            if cuerpo_texto:
                msg.set_content(cuerpo_texto)
            else:
                msg.set_content("Este es un correo interactivo. Por favor, visualízalo en un cliente compatible con HTML.")

            msg.add_alternative(cuerpo_html, subtype="html")

            # Procesar archivos adjuntos si existen
            if adjuntos:
                for ruta_adjunto in adjuntos:
                    if os.path.exists(ruta_adjunto):
                        with open(ruta_adjunto, "rb") as f:
                            contenido = f.read()
                            nombre_archivo = os.path.basename(ruta_adjunto)
                        msg.add_attachment(contenido, maintype="application", subtype="octet-stream", filename=nombre_archivo)

            # Enviar mediante SMTP
            if self.smtp_port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=context, timeout=10) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                    if self.smtp_use_tls:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)

            log_msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Correo enviado exitosamente a {destinatario} | Asunto: {asunto}"
            print(log_msg)
            if callback:
                callback(True, f"Correo electrónico enviado exitosamente a {destinatario}.")

        except Exception as e:
            error_msg = f"Error al enviar correo vía SMTP ({self.smtp_host}): {str(e)}"
            print(error_msg)
            # Fallback a log de simulación para no perder la traza
            self._registrar_simulacion(destinatario, asunto, cuerpo_html, adjuntos, fallo_smtp=error_msg)
            if callback:
                callback(False, error_msg)

    def _registrar_simulacion(self, destinatario, asunto, cuerpo_html, adjuntos=None, fallo_smtp=None):
        """Registra el email en un archivo de log para pruebas sin SMTP real."""
        log_file = os.path.join(self.log_dir, "email_simulados.log")
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        texto_log = f"""
================================================================================
📅 FECHA: {fecha}
📤 DE: {self.from_name} <{self.from_address}>
📥 PARA: {destinatario}
🏷️ ASUNTO: {asunto}
📎 ADJUNTOS: {', '.join(adjuntos) if adjuntos else 'Ninguno'}
⚠️ ESTADO: {'SIMULACIÓN (Configura .env para SMTP real)' if not fallo_smtp else f'FALLO SMTP ({fallo_smtp})'}
--------------------------------------------------------------------------------
CUERPO HTML:
{cuerpo_html}
================================================================================
"""
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(texto_log)
            
        return True, f"[OK] Correo registrado en MODO SIMULACION para {destinatario}.\n(Ver en logs/email_simulados.log)"

    # --- Plantillas HTML Profesionales ---

    def generar_plantilla_solicitud_lista(self, nombre_proveedor, nombre_ejecutivo, email_ejecutivo):
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }}
                .header {{ background-color: #1e3a8a; color: #ffffff; padding: 24px; text-align: center; }}
                .content {{ padding: 24px; line-height: 1.6; font-size: 14px; }}
                .highlight-box {{ background-color: #f1f5f9; border-left: 4px solid #2563eb; padding: 12px 16px; margin: 18px 0; border-radius: 4px; }}
                .footer {{ background-color: #f1f5f9; padding: 16px; text-align: center; font-size: 12px; color: #64748b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">Rosario Compras</h2>
                    <p style="margin: 4px 0 0 0; font-size: 14px; opacity: 0.9;">Red de Abastecimiento Gastronómico y Hotelero</p>
                </div>
                <div class="content">
                    <p>Estimado equipo de <strong>{nombre_proveedor}</strong>,</p>
                    <p>Nos ponemos en contacto desde la administración de <strong>Rosario Compras</strong> para solicitarles su <strong>lista de precios y disponibilidad de stock actualizada</strong>.</p>
                    
                    <div class="highlight-box">
                        <strong>📌 Formato sugerido para la importación en el catálogo:</strong><br>
                        Planilla en formato <strong>Excel (.xlsx)</strong> o <strong>CSV</strong> con las columnas: <em>Código, Detalle/Producto, Rubro, Precio y Descuento pactado</em>.
                    </div>
                    
                    <p>Una vez recibida, unificaremos sus artículos en nuestro Catálogo Único para que los socios de la red puedan emitir sus pedidos consolidados.</p>
                    <p>Agradecemos enviar la planilla respondiendo a este correo o contactando directamente a:</p>
                    <ul>
                        <li><strong>Ejecutivo a cargo:</strong> {nombre_ejecutivo}</li>
                        <li><strong>Email de contacto:</strong> <a href="mailto:{email_ejecutivo}">{email_ejecutivo}</a></li>
                        <li><strong>Fecha de emisión:</strong> {fecha_actual}</li>
                    </ul>
                </div>
                <div class="footer">
                    © {datetime.now().year} Rosario Compras S.A. - Rosario, Santa Fe, Argentina.
                </div>
            </div>
        </body>
        </html>
        """

    def generar_plantilla_catalogo_actualizado(self, nombre_socio, total_articulos, nombre_proveedor):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }}
                .header {{ background-color: #0d9488; color: #ffffff; padding: 24px; text-align: center; }}
                .content {{ padding: 24px; line-height: 1.6; font-size: 14px; }}
                .footer {{ background-color: #f1f5f9; padding: 16px; text-align: center; font-size: 12px; color: #64748b; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2 style="margin: 0;">🔔 Catálogo Actualizado</h2>
                    <p style="margin: 4px 0 0 0; font-size: 14px;">Rosario Compras</p>
                </div>
                <div class="content">
                    <p>Hola <strong>{nombre_socio}</strong>,</p>
                    <p>Te informamos que se acaban de actualizar <strong>{total_articulos} artículos</strong> en el catálogo correspondientes al proveedor <strong>{nombre_proveedor}</strong>.</p>
                    <p>Ya puedes ingresar a la plataforma de Rosario Compras para consultar los precios negociados y confeccionar tu pedido semanal.</p>
                </div>
                <div class="footer">
                    © {datetime.now().year} Rosario Compras - Sistema de Gestión
                </div>
            </div>
        </body>
        </html>
        """
