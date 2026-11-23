import os
import re
import unicodedata
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


def nombre_para_archivo(texto):
    """'Lácteos del Litoral' → 'Lacteos_del_Litoral' (sin acentos ni caracteres especiales)."""
    sin_acentos = unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^A-Za-z0-9]+', '_', sin_acentos).strip('_') or "Proveedor"


class OrdenCompraService:
    """
    Genera el archivo Excel (.xlsx) de la orden de compra que el ejecutivo envía al proveedor.
    Contiene un encabezado formal y los totales por artículo (sin desglose por socio).
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = OrdenCompraService()
        return cls._instance

    def __init__(self):
        self.carpeta_ordenes = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "ordenes_compra"
        )

    def nombre_archivo(self, codigo, proveedor_nombre, fecha):
        """Nombre del archivo: Orden_Compra_<codigo>_<proveedor>_<AAAA-MM-DD>.xlsx"""
        return f"Orden_Compra_{codigo}_{nombre_para_archivo(proveedor_nombre)}_{fecha[:10]}.xlsx"

    def ruta_archivo(self, nombre_archivo):
        return os.path.join(self.carpeta_ordenes, nombre_archivo)

    def generar_excel(self, datos, nombre_archivo):
        """
        datos = {
            'codigo', 'fecha' (AAAA-MM-DD HH:MM:SS), 'cantidad_pedidos',
            'proveedor': {'nombre', 'email', 'telefono', 'direccion'},
            'ejecutivo': {'nombre', 'email'},
            'items': [{'codigo_proveedor', 'detalle', 'cantidad', 'precio_unitario', 'subtotal'}],
            'total'
        }
        Retorna la ruta absoluta del archivo generado.
        """
        os.makedirs(self.carpeta_ordenes, exist_ok=True)
        ruta = self.ruta_archivo(nombre_archivo)

        wb = Workbook()
        ws = wb.active
        ws.title = "Orden de Compra"
        ws.sheet_view.showGridLines = False

        azul = "1E3A8A"
        gris_claro = "F1F5F9"
        borde_fino = Side(style="thin", color="CBD5E1")
        borde = Border(left=borde_fino, right=borde_fino, top=borde_fino, bottom=borde_fino)
        fmt_moneda = '"$"#,##0.00'
        ultima_col = 6  # A..F

        def fila_combinada(fila, texto, font=None, fill=None, align="left", alto=None):
            ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=ultima_col)
            celda = ws.cell(row=fila, column=1, value=texto)
            if font:
                celda.font = font
            if fill:
                for c in range(1, ultima_col + 1):
                    ws.cell(row=fila, column=c).fill = fill
            celda.alignment = Alignment(horizontal=align, vertical="center")
            if alto:
                ws.row_dimensions[fila].height = alto

        # --- Membrete ---
        relleno_azul = PatternFill("solid", fgColor=azul)
        fila_combinada(1, "ROSARIO COMPRAS", Font(size=18, bold=True, color="FFFFFF"), relleno_azul, "center", 30)
        fila_combinada(2, "Red de Abastecimiento Gastronómico y Hotelero · Rosario, Santa Fe",
                       Font(size=10, color="FFFFFF"), relleno_azul, "center", 18)
        fila_combinada(4, "ORDEN DE COMPRA", Font(size=14, bold=True, color=azul), None, "left", 24)

        # --- Datos de la orden y del proveedor (dos columnas de etiquetas/valores) ---
        prov = datos.get('proveedor', {})
        ejec = datos.get('ejecutivo', {})
        fecha = datos.get('fecha', '')
        fecha_legible = f"{fecha[8:10]}/{fecha[5:7]}/{fecha[0:4]}" if len(fecha) >= 10 else fecha

        izquierda = [
            ("Proveedor:", prov.get('nombre', '')),
            ("Email:", prov.get('email') or '-'),
            ("Teléfono:", prov.get('telefono') or '-'),
            ("Dirección:", prov.get('direccion') or '-'),
        ]
        derecha = [
            ("N° de Orden:", datos.get('codigo', '')),
            ("Fecha de emisión:", fecha_legible),
            ("Emitida por:", ejec.get('nombre', '')),
            ("Contacto:", ejec.get('email', '')),
        ]
        fila = 6
        for (et_i, val_i), (et_d, val_d) in zip(izquierda, derecha):
            ws.cell(row=fila, column=1, value=et_i).font = Font(bold=True, color="475569")
            ws.merge_cells(start_row=fila, start_column=2, end_row=fila, end_column=3)
            ws.cell(row=fila, column=2, value=val_i)
            ws.cell(row=fila, column=4, value=et_d).font = Font(bold=True, color="475569")
            ws.merge_cells(start_row=fila, start_column=5, end_row=fila, end_column=6)
            ws.cell(row=fila, column=5, value=val_d)
            fila += 1
        ws.cell(row=6, column=5).font = Font(bold=True, color=azul)  # Resaltar el N° de orden

        # --- Tabla de artículos ---
        fila = 11
        encabezados = ["N°", "Cód. Proveedor", "Artículo / Detalle", "Cantidad", "Precio Unitario", "Subtotal"]
        for col, texto in enumerate(encabezados, start=1):
            celda = ws.cell(row=fila, column=col, value=texto)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = relleno_azul
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.border = borde
        ws.row_dimensions[fila].height = 20

        for i, item in enumerate(datos.get('items', []), start=1):
            fila += 1
            valores = [i, item.get('codigo_proveedor') or '-', item.get('detalle', ''),
                       item.get('cantidad', 0), item.get('precio_unitario', 0.0), item.get('subtotal', 0.0)]
            for col, valor in enumerate(valores, start=1):
                celda = ws.cell(row=fila, column=col, value=valor)
                celda.border = borde
                if i % 2 == 0:
                    celda.fill = PatternFill("solid", fgColor=gris_claro)
                if col in (1, 2, 4):
                    celda.alignment = Alignment(horizontal="center")
                if col in (5, 6):
                    celda.number_format = fmt_moneda

        # --- Total ---
        fila += 1
        ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=5)
        celda_et = ws.cell(row=fila, column=1, value="TOTAL DE LA ORDEN")
        celda_et.font = Font(bold=True, color=azul)
        celda_et.alignment = Alignment(horizontal="right")
        celda_total = ws.cell(row=fila, column=6, value=datos.get('total', 0.0))
        celda_total.font = Font(bold=True, color=azul)
        celda_total.number_format = fmt_moneda
        for col in range(1, ultima_col + 1):
            ws.cell(row=fila, column=col).border = borde
            ws.cell(row=fila, column=col).fill = PatternFill("solid", fgColor="EFF6FF")

        # --- Observaciones ---
        fila += 2
        notas = [
            "Observaciones:",
            "• Los precios corresponden a la lista negociada vigente con Rosario Compras.",
            "• Por favor, confirmar la recepción de esta orden y la fecha estimada de entrega respondiendo al contacto indicado.",
            f"• Al entregar, indicar el N° de Orden {datos.get('codigo', '')} en el remito o factura.",
        ]
        for j, nota in enumerate(notas):
            ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=ultima_col)
            celda = ws.cell(row=fila, column=1, value=nota)
            celda.font = Font(bold=(j == 0), italic=(j > 0), color="475569", size=9 if j else 10)
            fila += 1

        # --- Anchos y configuración de impresión ---
        for col, ancho in enumerate([6, 16, 46, 11, 17, 18], start=1):
            ws.column_dimensions[get_column_letter(col)].width = ancho
        ws.page_setup.orientation = "portrait"
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_title_rows = "11:11"

        wb.save(ruta)
        return ruta
