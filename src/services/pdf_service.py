import os
from PyQt6.QtGui import QTextDocument, QPdfWriter, QPageSize, QPageLayout
from PyQt6.QtCore import QMarginsF

class PdfService:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PdfService()
        return cls._instance

    def __init__(self):
        self.carpeta_remitos = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "remitos_pdf"
        )
        os.makedirs(self.carpeta_remitos, exist_ok=True)

    def generar_remito_pdf(self, datos_remito):
        """
        Genera un remito corporativo oficial en formato PDF usando QTextDocument y QPdfWriter.
        datos_remito = {
            'codigo_remito': str,
            'codigo_pedido': str,
            'nro_comprobante': str,
            'fecha': str,
            'socio_nombre': str,
            'socio_email': str,
            'proveedor_nombre': str,
            'items': [{'id_articulo': int, 'codigo': str, 'detalle': str, 'cantidad': int}]
        }
        Retorna la ruta absoluta del PDF generado.
        """
        cod_rem = datos_remito.get('codigo_remito', 'RC-REM-0001')
        cod_ped = datos_remito.get('codigo_pedido', 'RC-ORD-0001')
        nro_comp = datos_remito.get('nro_comprobante', 'CMP-AUTO')
        fecha = datos_remito.get('fecha', '')
        socio_nom = datos_remito.get('socio_nombre', 'Socio')
        socio_mail = datos_remito.get('socio_email', '')
        prov_nom = datos_remito.get('proveedor_nombre', 'Proveedor')
        items = datos_remito.get('items', [])

        # Sanitizar nombre de archivo
        socio_safe = "".join(c for c in socio_nom if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        prov_safe = "".join(c for c in prov_nom if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        nombre_pdf = f"Remito_{prov_safe}_{socio_safe}_{cod_rem}.pdf"
        ruta_pdf = os.path.join(self.carpeta_remitos, nombre_pdf)

        # Construir filas de la tabla HTML
        filas_html = ""
        total_unidades = 0
        for idx, item in enumerate(items, start=1):
            cant = item.get('cantidad', 0)
            total_unidades += cant
            cod = item.get('codigo') or f"ART-{item.get('id_articulo', idx)}"
            det = item.get('detalle', 'Producto')
            filas_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 8px; text-align: center;">{idx}</td>
                <td style="padding: 8px; text-align: center; font-family: monospace;">{cod}</td>
                <td style="padding: 8px;">{det}</td>
                <td style="padding: 8px; text-align: center; font-weight: bold; color: #1e3a8a;">{cant} u.</td>
                <td style="padding: 8px; text-align: center; color: #16a34a;">Conforme</td>
            </tr>
            """

        html_content = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    color: #1e293b;
                    margin: 20px;
                }}
                .header-table {{
                    width: 100%;
                    border-bottom: 2px solid #2563eb;
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }}
                .title {{
                    font-size: 22px;
                    font-weight: bold;
                    color: #1e3a8a;
                }}
                .subtitle {{
                    font-size: 11px;
                    color: #64748b;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                }}
                .box-info {{
                    border: 1px solid #cbd5e1;
                    background-color: #f8fafc;
                    padding: 12px;
                    border-radius: 6px;
                    margin-bottom: 20px;
                }}
                .products-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 25px;
                }}
                .products-table th {{
                    background-color: #1e293b;
                    color: white;
                    padding: 8px;
                    font-size: 12px;
                    text-align: left;
                }}
                .footer-signatures {{
                    width: 100%;
                    margin-top: 40px;
                }}
            </style>
        </head>
        <body>
            <table class="header-table">
                <tr>
                    <td>
                        <div class="title">ROSARIO COMPRAS</div>
                        <div class="subtitle">Red de Abastecimiento Gastronómico y Comercial</div>
                        <div style="font-size: 11px; color: #475569; margin-top: 4px;">Rosario, Santa Fe, Argentina</div>
                    </td>
                    <td style="text-align: right;">
                        <div style="font-size: 18px; font-weight: bold; color: #2563eb;">REMITO DE ENTREGA</div>
                        <div style="font-size: 14px; font-family: monospace; font-weight: bold;">{cod_rem}</div>
                        <div style="font-size: 11px; color: #64748b; margin-top: 4px;">Fecha de Emisión: {fecha}</div>
                        <div style="font-size: 11px; color: #64748b;">Ref. Pedido: {cod_ped}</div>
                        <div style="font-size: 11px; color: #64748b;">Comprobante Interno: {nro_comp}</div>
                    </td>
                </tr>
            </table>

            <table style="width: 100%; margin-bottom: 15px;">
                <tr>
                    <td style="width: 50%; vertical-align: top; padding-right: 10px;">
                        <div class="box-info">
                            <div style="font-weight: bold; color: #1e3a8a; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-bottom: 6px;">
                                🏢 PROVEEDOR DE ORIGEN
                            </div>
                            <div><b>Razón Social:</b> {prov_nom}</div>
                            <div><b>Despacho:</b> Central Logística Rosario Compras</div>
                        </div>
                    </td>
                    <td style="width: 50%; vertical-align: top; padding-left: 10px;">
                        <div class="box-info">
                            <div style="font-weight: bold; color: #1e3a8a; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-bottom: 6px;">
                                👤 SOCIO RECEPTOR
                            </div>
                            <div><b>Nombre:</b> {socio_nom}</div>
                            <div><b>Contacto:</b> {socio_mail}</div>
                        </div>
                    </td>
                </tr>
            </table>

            <table class="products-table">
                <thead>
                    <tr>
                        <th style="text-align: center; width: 40px;">#</th>
                        <th style="text-align: center; width: 100px;">Cód. Ref.</th>
                        <th>Descripción del Artículo / Producto</th>
                        <th style="text-align: center; width: 110px;">Cant. Entregada</th>
                        <th style="text-align: center; width: 90px;">Estado</th>
                    </tr>
                </thead>
                <tbody>
                    {filas_html}
                </tbody>
                <tfoot>
                    <tr style="background-color: #f1f5f9; font-weight: bold;">
                        <td colspan="3" style="padding: 10px; text-align: right;">TOTAL GENERAL ENTREGADO:</td>
                        <td style="padding: 10px; text-align: center; color: #1e3a8a;">{total_unidades} u.</td>
                        <td></td>
                    </tr>
                </tfoot>
            </table>

            <div style="font-size: 10px; color: #64748b; font-style: italic; margin-top: 10px;">
                * Documento interno de control y remisión de mercadería emitido por el sistema de gestión Rosario Compras. Mercadería recibida en perfectas condiciones higiénico-sanitarias y operativas.
            </div>

            <table class="footer-signatures">
                <tr>
                    <td style="width: 45%; text-align: center; border-top: 1px solid #94a3b8; padding-top: 8px;">
                        <div style="font-size: 11px; font-weight: bold;">Firma y Aclaración de Logística / Cadetería</div>
                        <div style="font-size: 10px; color: #64748b;">Rosario Compras</div>
                    </td>
                    <td style="width: 10%;"></td>
                    <td style="width: 45%; text-align: center; border-top: 1px solid #94a3b8; padding-top: 8px;">
                        <div style="font-size: 11px; font-weight: bold;">Firma y Aclaración del Socio Receptor</div>
                        <div style="font-size: 10px; color: #64748b;">Conformidad de Entrega</div>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        # Generar el archivo PDF usando QTextDocument y QPdfWriter
        pdf_writer = QPdfWriter(ruta_pdf)
        pdf_writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        pdf_writer.setPageMargins(QMarginsF(12, 12, 12, 12))
        
        doc = QTextDocument()
        doc.setHtml(html_content)
        doc.print(pdf_writer)

        return ruta_pdf
