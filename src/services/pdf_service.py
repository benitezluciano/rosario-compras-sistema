import os
from PyQt6.QtGui import QPdfWriter, QPageSize, QPageLayout, QPainter, QPen, QFont, QColor
from PyQt6.QtCore import QMarginsF, QRectF, QPointF, Qt

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

RESOLUCION = 300                 # dpi del PDF
MM = RESOLUCION / 25.4           # puntos de dispositivo por milímetro

# Geometría de la hoja A4 (en mm), siguiendo el modelo de remito
X0, X1 = 12.0, 198.0             # bordes izquierdo y derecho del recuadro
XC = 105.0                       # divisor central
Y0 = 14.0                        # borde superior del recuadro
Y_CABECERA = 54.0                # fin de la cabecera (emisor | X | remito)
Y_DESTINATARIO = 92.0            # fin del bloque Señor(es) / Domicilio
Y_REFERENCIAS = 101.0            # fin de la franja de referencias
Y_ENCABEZADO_TABLA = 107.0       # fin del encabezado de columnas
ALTO_FILA = 6.5
FILAS_POR_HOJA = 17              # renglones de artículos por hoja (+1 para el total)
Y_PIE = Y_ENCABEZADO_TABLA + ALTO_FILA * (FILAS_POR_HOJA + 1)   # inicio del pie (transporte y recepción)
Y1 = 284.0                       # borde inferior del recuadro

# Columnas de la tabla de artículos: (x inicial, título)
COLUMNAS = [(X0, "CANTIDAD"), (32.0, "UNIDAD"), (54.0, "CÓDIGO"), (82.0, "DESCRIPCIÓN DEL PRODUCTO")]

NEGRO = QColor("#111827")
GRIS = QColor("#4b5563")
GRIS_CLARO = QColor("#9ca3af")


def fecha_larga(fecha_iso):
    """'2026-11-23' → '23 de noviembre de 2026'."""
    try:
        anio, mes, dia = fecha_iso[:10].split("-")
        return f"{int(dia)} de {MESES[int(mes) - 1]} de {anio}"
    except (ValueError, IndexError):
        return fecha_iso or ""


def fecha_corta(fecha_iso):
    """'2026-11-23' → '23/11/2026'."""
    if fecha_iso and len(fecha_iso) >= 10:
        return f"{fecha_iso[8:10]}/{fecha_iso[5:7]}/{fecha_iso[0:4]}"
    return fecha_iso or ""


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

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------

    @staticmethod
    def nombre_archivo_remito(datos):
        """Remito_X_0001-00000003_<Socio>_<RC-REM-...>.pdf (termina en el código interno para poder ubicarlo)."""
        socio = datos.get('destinatario', {}).get('nombre', 'Socio')
        socio_safe = "".join(c for c in socio if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        return f"Remito_{datos.get('letra', 'X')}_{datos.get('numero', '')}_{socio_safe}_{datos.get('codigo', '')}.pdf"

    def generar_remito_pdf(self, datos):
        """
        Genera el remito en PDF con el formato del modelo (ORIGINAL y DUPLICADO).
        datos = {
            'letra', 'numero' ('0001-00000001'), 'codigo' (referencia interna RC-REM-...), 'fecha' (AAAA-MM-DD),
            'emisor': {'razon_social', 'cuit', 'condicion_iva', 'domicilio', 'localidad'},
            'destinatario': {'nombre', 'cuit_dni', 'condicion_iva', 'domicilio'},
            'referencias': str,
            'items': [{'cantidad', 'unidad', 'codigo', 'detalle'}],
            'total_unidades': int,
            'observaciones': str,
            'datos_simulados': bool,
        }
        Retorna la ruta absoluta del PDF generado.
        """
        os.makedirs(self.carpeta_remitos, exist_ok=True)
        ruta_pdf = os.path.join(self.carpeta_remitos, self.nombre_archivo_remito(datos))

        writer = QPdfWriter(ruta_pdf)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
        writer.setResolution(RESOLUCION)
        writer.setTitle(f"Remito {datos.get('letra', 'X')} {datos.get('numero', '')}")
        writer.setCreator("Rosario Compras - Sistema de Gestión")

        items = datos.get('items', [])
        p = QPainter(writer)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            ancho_desc = X1 - COLUMNAS[3][0] - 4.0
            alto_disp = (Y_PIE - Y_ENCABEZADO_TABLA) - ALTO_FILA
            hojas = self._paginar_items(p, items, ancho_desc, 9, alto_disp)
            primera = True
            for copia in ("ORIGINAL", "DUPLICADO"):
                for nro_hoja, items_hoja in enumerate(hojas, start=1):
                    if not primera:
                        writer.newPage()
                    primera = False
                    self._dibujar_hoja(p, datos, items_hoja, copia, nro_hoja, len(hojas))
        finally:
            p.end()
        return ruta_pdf

    # ------------------------------------------------------------------
    # Dibujo
    # ------------------------------------------------------------------

    @staticmethod
    def _r(x, y, w, h):
        return QRectF(x * MM, y * MM, w * MM, h * MM)

    @staticmethod
    def _linea(p, x1, y1, x2, y2, grosor=0.3, color=NEGRO, estilo=Qt.PenStyle.SolidLine):
        pen = QPen(color, grosor * MM)
        pen.setStyle(estilo)
        p.setPen(pen)
        p.drawLine(QPointF(x1 * MM, y1 * MM), QPointF(x2 * MM, y2 * MM))

    def _texto(self, p, x, y, w, h, texto, puntos=9, negrita=False, cursiva=False, color=NEGRO,
               alineacion=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, ajustar=False):
        fuente = QFont("Arial")
        fuente.setPointSizeF(puntos)
        fuente.setBold(negrita)
        fuente.setItalic(cursiva)
        p.setFont(fuente)
        p.setPen(color)
        rect = self._r(x, y, w, h)
        texto = "" if texto is None else str(texto)
        if ajustar:
            p.drawText(rect, int(alineacion | Qt.TextFlag.TextWordWrap), texto)
        else:
            texto = p.fontMetrics().elidedText(texto, Qt.TextElideMode.ElideRight, int(rect.width()))
            p.drawText(rect, int(alineacion), texto)

    def _alto_fila_item(self, p, texto, ancho_mm, puntos):
        """Calcula la altura en mm necesaria para mostrar `texto` en varias líneas."""
        fuente = QFont("Arial")
        fuente.setPointSizeF(puntos)
        p.setFont(fuente)
        rect = p.fontMetrics().boundingRect(
            0,
            0,
            int(max(ancho_mm, 10.0) * MM),
            100000,
            int(Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap),
            "" if texto is None else str(texto),
        )
        return max(ALTO_FILA, rect.height() / MM + 2.2)

    def _paginar_items(self, p, items, ancho_desc_mm, puntos, alto_disponible_mm):
        """Agrupa los ítems en hojas según la altura real de sus descripciones multilínea."""
        if not items:
            return [[]]
        hojas = []
        actual = []
        y_usado = 0.0
        for it in items:
            alto = self._alto_fila_item(p, it.get('detalle', ''), ancho_desc_mm, puntos)
            if actual and y_usado + alto > alto_disponible_mm:
                hojas.append(actual)
                actual = []
                y_usado = 0.0
            actual.append((it, alto))
            y_usado += alto
        if actual:
            hojas.append(actual)
        return hojas

    def _esquinas(self, p, x, y, w, h, largo=3.0):
        """Marcas en L en las cuatro esquinas (como los recuadros del modelo)."""
        for (cx, cy, dx, dy) in ((x, y, 1, 1), (x + w, y, -1, 1), (x, y + h, 1, -1), (x + w, y + h, -1, -1)):
            self._linea(p, cx, cy, cx + dx * largo, cy, 0.25)
            self._linea(p, cx, cy, cx, cy + dy * largo, 0.25)

    def _campo(self, p, x, y, w, etiqueta, puntos=8.5):
        """Etiqueta seguida de una línea para completar a mano."""
        fuente = QFont("Arial")
        fuente.setPointSizeF(puntos)
        p.setFont(fuente)
        ancho_etiqueta = p.fontMetrics().horizontalAdvance(etiqueta + " ") / MM
        self._texto(p, x, y - 4.5, ancho_etiqueta + 1, 5, etiqueta, puntos, alineacion=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)
        self._linea(p, x + ancho_etiqueta, y, x + w, y, 0.2, GRIS, Qt.PenStyle.DotLine)

    def _dibujar_hoja(self, p, d, items, copia, nro_hoja, total_hojas):
        emisor = d.get('emisor', {})
        dest = d.get('destinatario', {})
        izq = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        centro = Qt.AlignmentFlag.AlignCenter
        arriba = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop

        # --- Sobre el recuadro: copia y hoja ---
        etiqueta = copia if total_hojas == 1 else f"{copia} · Hoja {nro_hoja} de {total_hojas}"
        self._texto(p, X0, Y0 - 6, X1 - X0, 5, etiqueta, 8, negrita=True, color=GRIS,
                    alineacion=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # --- Recuadro exterior y divisiones horizontales ---
        pen = QPen(NEGRO, 0.5 * MM)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(self._r(X0, Y0, X1 - X0, Y1 - Y0))
        for y in (Y_CABECERA, Y_DESTINATARIO, Y_REFERENCIAS, Y_PIE):
            self._linea(p, X0, y, X1, y, 0.35)
        self._linea(p, X0, Y_ENCABEZADO_TABLA, X1, Y_ENCABEZADO_TABLA, 0.3)

        # --- Cabecera izquierda: emisor ---
        self._texto(p, X0 + 4, Y0 + 3, 40, 6, "Nombre:", 11, negrita=True)
        self._texto(p, X0 + 4, Y0 + 10, XC - X0 - 16, 7, emisor.get('razon_social', ''), 12.5, negrita=True)
        lineas_emisor = [
            f"Domicilio: {emisor.get('domicilio', '')}",
            f"C.U.I.T.: {emisor.get('cuit', '')}",
            f"Condición frente al IVA: {emisor.get('condicion_iva', '')}",
        ]
        for i, linea in enumerate(lineas_emisor):
            self._texto(p, X0 + 4, Y0 + 19 + i * 5, XC - X0 - 17, 5, linea, 7.8, color=GRIS)

        # --- Divisor central y recuadro de la letra ---
        self._linea(p, XC, Y0, XC, Y_DESTINATARIO, 0.35)
        caja_x, caja_y, caja_w, caja_h = XC - 10, Y0 + 3, 20, 31
        p.setPen(QPen(NEGRO, 0.4 * MM))
        p.setBrush(QColor("white"))
        p.drawRect(self._r(caja_x, caja_y, caja_w, caja_h))
        p.setBrush(Qt.BrushStyle.NoBrush)
        self._texto(p, caja_x, caja_y + 1, caja_w, 13, d.get('letra', 'X'), 30, negrita=True, alineacion=centro)
        self._texto(p, caja_x + 1, caja_y + 14, caja_w - 2, 16, "DOCUMENTO\nNO VÁLIDO\nCOMO\nFACTURA", 6.3,
                    negrita=True, alineacion=centro, ajustar=True)

        # --- Cabecera derecha: datos del remito ---
        xd = XC + 14
        self._texto(p, xd, Y0 + 2, X1 - xd - 3, 8, "REMITO", 17, negrita=True)
        self._texto(p, xd, Y0 + 11, X1 - xd - 3, 7, f"N.º {d.get('numero', '')}", 13, negrita=True)
        self._texto(p, xd, Y0 + 19.5, X1 - xd - 3, 5, f"Fecha de emisión: {fecha_corta(d.get('fecha', ''))}", 9)
        self._texto(p, xd, Y0 + 24.5, X1 - xd - 3, 5,
                    f"{emisor.get('localidad', 'Rosario')}, {fecha_larga(d.get('fecha', ''))}", 9, color=GRIS)
        self._texto(p, xd, Y0 + 32, X1 - xd - 3, 5, f"Ref. interna: {d.get('codigo', '')}", 7.5, color=GRIS_CLARO)

        # --- Destinatario: Señor(es) | Domicilio ---
        alto = Y_DESTINATARIO - Y_CABECERA
        self._esquinas(p, X0 + 3, Y_CABECERA + 3, XC - X0 - 6, alto - 13)
        self._esquinas(p, XC + 3, Y_CABECERA + 3, X1 - XC - 6, alto - 13)
        self._texto(p, X0 + 7, Y_CABECERA + 5.5, 60, 5, "Señor(es):", 8.5, color=GRIS)
        self._texto(p, X0 + 7, Y_CABECERA + 11, XC - X0 - 14, 13, dest.get('nombre', ''), 11, negrita=True,
                    alineacion=arriba, ajustar=True)
        self._texto(p, X0 + 3, Y_DESTINATARIO - 8, XC - X0 - 6, 6,
                    f"I.V.A.: {dest.get('condicion_iva') or '—'}", 9)
        self._texto(p, XC + 7, Y_CABECERA + 5.5, 60, 5, "Domicilio de entrega:", 8.5, color=GRIS)
        self._texto(p, XC + 7, Y_CABECERA + 11, X1 - XC - 14, 13, dest.get('domicilio') or '—', 10,
                    alineacion=arriba, ajustar=True)
        self._texto(p, XC + 3, Y_DESTINATARIO - 8, X1 - XC - 6, 6,
                    f"C.U.I.T. / D.N.I. N.º: {dest.get('cuit_dni') or '—'}", 9)

        # --- Referencias (franja de "Condición de venta" del modelo) ---
        self._texto(p, X0 + 3, Y_DESTINATARIO + 0.5, X1 - X0 - 6, Y_REFERENCIAS - Y_DESTINATARIO - 1,
                    f"Referencias: {d.get('referencias', '')}", 7.8, alineacion=izq, ajustar=True)

        # --- Tabla de artículos ---
        for i, (x, titulo) in enumerate(COLUMNAS):
            x_fin = COLUMNAS[i + 1][0] if i + 1 < len(COLUMNAS) else X1
            if i > 0:
                self._linea(p, x, Y_REFERENCIAS, x, Y_PIE, 0.3)
            self._texto(p, x, Y_REFERENCIAS, x_fin - x, Y_ENCABEZADO_TABLA - Y_REFERENCIAS, titulo, 7.5,
                        negrita=True, alineacion=centro)

        y = Y_ENCABEZADO_TABLA
        for entrada in items:
            it, alto_fila = entrada if isinstance(entrada, tuple) else (entrada, ALTO_FILA)
            valores = [str(it.get('cantidad', '')), it.get('unidad') or 'Unidad', it.get('codigo') or '-', it.get('detalle', '')]
            for i, (x, _) in enumerate(COLUMNAS):
                x_fin = COLUMNAS[i + 1][0] if i + 1 < len(COLUMNAS) else X1
                alin = izq if i == 3 else centro
                margen = 2 if i == 3 else 0.5
                self._texto(p, x + margen, y, x_fin - x - 2 * margen, alto_fila, valores[i], 9,
                            negrita=(i == 0), alineacion=alin, ajustar=(i == 3))
            self._linea(p, X0, y + alto_fila, X1, y + alto_fila, 0.15, GRIS_CLARO, Qt.PenStyle.DotLine)
            y += alto_fila

        if nro_hoja == total_hojas:
            self._texto(p, COLUMNAS[3][0] + 2, y, X1 - COLUMNAS[3][0] - 4, ALTO_FILA,
                        f"Total: {d.get('total_unidades', 0)} unidad(es) en {d.get('cantidad_renglones', len(items))} renglón(es)",
                        8.5, negrita=True, cursiva=True, color=GRIS, alineacion=izq)
        else:
            self._texto(p, COLUMNAS[3][0] + 2, y, X1 - COLUMNAS[3][0] - 4, ALTO_FILA,
                        "Continúa en la hoja siguiente…", 8.5, cursiva=True, color=GRIS, alineacion=izq)

        # --- Pie: transporte y recepción ---
        self._texto(p, X0 + 3, Y_PIE + 1.5, 80, 5, "TRANSPORTE Y RECEPCIÓN", 7.5, negrita=True, color=GRIS)
        self._campo(p, X0 + 3, Y_PIE + 12, X1 - X0 - 6, "Transportista / Chofer / Dominio:")
        self._texto(p, X0 + 3, Y_PIE + 14.5, 30, 5, "Observaciones:", 8.5, negrita=True)
        self._texto(p, X0 + 28, Y_PIE + 14.5, X1 - X0 - 31, 15, d.get('observaciones', ''), 8, alineacion=arriba, ajustar=True)

        y_firmas = Y_PIE + 41
        ancho_col = (X1 - X0 - 12) / 2
        self._campo(p, X0 + 3, y_firmas, ancho_col, "Recibí conforme:")
        self._campo(p, X0 + 9 + ancho_col, y_firmas, ancho_col, "Aclaración:")
        self._campo(p, X0 + 3, y_firmas + 11, ancho_col, "D.N.I.:")
        self._campo(p, X0 + 9 + ancho_col, y_firmas + 11, ancho_col, "Fecha y hora de recepción:")

        # --- Debajo del recuadro ---
        leyenda = "Documento emitido por el Sistema de Gestión Rosario Compras."
        if d.get('datos_simulados'):
            leyenda += " DATOS FISCALES SIMULADOS — completar con los datos reales del emisor y del destinatario."
        self._texto(p, X0, Y1 + 1.5, X1 - X0, 5, leyenda, 6.8, cursiva=True, color=GRIS, alineacion=centro)

    # ------------------------------------------------------------------
    # Nota de Pedido (copia del pedido del socio, con precios)
    # ------------------------------------------------------------------

    @staticmethod
    def nombre_archivo_nota_pedido(datos):
        """Nota_Pedido_<RC-ORD-...>_<Proveedor>.pdf"""
        prov = datos.get('proveedor', {}).get('nombre') or 'Proveedor'
        prov_safe = "".join(c for c in prov if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
        return f"Nota_Pedido_{datos.get('codigo', '')}_{prov_safe}.pdf"

    def generar_nota_pedido_pdf(self, datos, ruta_pdf):
        """
        Genera la Nota de Pedido del socio en `ruta_pdf` (una sola copia, con precios).
        datos = {
            'codigo' (RC-ORD-...), 'fecha', 'estado', 'leyenda_estado' (texto según el estado),
            'emisor': {...como en el remito, más 'email'},
            'socio': {'nombre', 'cuit_dni', 'condicion_iva', 'domicilio', 'email'},
            'proveedor': {'nombre', 'email', 'telefono'},
            'referencias': str,
            'items': [{'cantidad', 'entregado' (None si no hubo entrega), 'unidad', 'codigo', 'detalle',
                       'precio_unitario', 'subtotal'}],
            'entregado': bool (agrega la columna ENTREG.), 'total', 'total_unidades', 'datos_simulados'
        }
        Retorna la ruta del PDF.
        """
        carpeta = os.path.dirname(os.path.abspath(ruta_pdf))
        os.makedirs(carpeta, exist_ok=True)

        writer = QPdfWriter(ruta_pdf)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)
        writer.setResolution(RESOLUCION)
        writer.setTitle(f"Nota de Pedido {datos.get('codigo', '')}")
        writer.setCreator("Rosario Compras - Sistema de Gestión")

        items = datos.get('items', [])
        columnas = NP_COLUMNAS_ENTREGA if datos.get('entregado') else NP_COLUMNAS
        idx_desc = next(i for i, (_x, _t, clave, _a) in enumerate(columnas) if clave == 'detalle')
        ancho_desc = columnas[idx_desc + 1][0] - columnas[idx_desc][0] - 3.0
        alto_disp = (NP_Y_PIE - NP_Y_ENCABEZADO_TABLA) - ALTO_FILA

        p = QPainter(writer)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            hojas = self._paginar_items(p, items, ancho_desc, 8.5, alto_disp)
            for nro_hoja, items_hoja in enumerate(hojas, start=1):
                if nro_hoja > 1:
                    writer.newPage()
                self._dibujar_nota_pedido(p, datos, items_hoja, nro_hoja, len(hojas))
        finally:
            p.end()
        return ruta_pdf

    def _dibujar_nota_pedido(self, p, d, items, nro_hoja, total_hojas):
        emisor = d.get('emisor', {})
        socio = d.get('socio', {})
        prov = d.get('proveedor', {})
        izq = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        der = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        centro = Qt.AlignmentFlag.AlignCenter
        arriba = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        columnas = NP_COLUMNAS_ENTREGA if d.get('entregado') else NP_COLUMNAS

        if total_hojas > 1:
            self._texto(p, X0, Y0 - 6, X1 - X0, 5, f"Hoja {nro_hoja} de {total_hojas}", 8, negrita=True, color=GRIS,
                        alineacion=der)

        # --- Recuadro y divisiones ---
        p.setPen(QPen(NEGRO, 0.5 * MM))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(self._r(X0, Y0, X1 - X0, Y1 - Y0))
        for y in (NP_Y_CABECERA, NP_Y_PARTES, NP_Y_REFERENCIAS, NP_Y_PIE):
            self._linea(p, X0, y, X1, y, 0.35)
        self._linea(p, X0, NP_Y_ENCABEZADO_TABLA, X1, NP_Y_ENCABEZADO_TABLA, 0.3)
        self._linea(p, XC, Y0, XC, NP_Y_PARTES, 0.35)

        # --- Cabecera izquierda: emisor ---
        self._texto(p, X0 + 4, Y0 + 3, XC - X0 - 8, 8, emisor.get('razon_social', ''), 14, negrita=True)
        lineas = [
            f"Domicilio: {emisor.get('domicilio', '')}",
            f"C.U.I.T.: {emisor.get('cuit', '')} · IVA: {emisor.get('condicion_iva', '')}",
            f"Email: {emisor.get('email', '')}",
        ]
        for i, linea in enumerate(lineas):
            self._texto(p, X0 + 4, Y0 + 13 + i * 5, XC - X0 - 8, 5, linea, 7.8, color=GRIS)

        # --- Cabecera derecha: datos del pedido ---
        xd = XC + 5
        ancho_d = X1 - xd - 4
        self._texto(p, xd, Y0 + 2, ancho_d, 8, "NOTA DE PEDIDO", 16, negrita=True)
        self._texto(p, xd, Y0 + 11, ancho_d, 7, f"N.º {d.get('codigo', '')}", 12, negrita=True)
        self._texto(p, xd, Y0 + 19, ancho_d, 5, f"Fecha del pedido: {fecha_corta(d.get('fecha', ''))}", 9)
        self._texto(p, xd, Y0 + 24, ancho_d, 5, f"Estado: {d.get('estado_visible') or d.get('estado', '')}", 9, negrita=True,
                    color=NP_COLOR_ESTADO.get(d.get('estado'), NEGRO))
        self._texto(p, xd, Y0 + 29.5, ancho_d, 5, "Documento no válido como factura ni como remito", 7, cursiva=True,
                    color=GRIS_CLARO)

        # --- Socio | Proveedor ---
        self._esquinas(p, X0 + 3, NP_Y_CABECERA + 3, XC - X0 - 6, NP_Y_PARTES - NP_Y_CABECERA - 6)
        self._esquinas(p, XC + 3, NP_Y_CABECERA + 3, X1 - XC - 6, NP_Y_PARTES - NP_Y_CABECERA - 6)
        self._texto(p, X0 + 7, NP_Y_CABECERA + 4.5, 60, 5, "Socio:", 8.5, color=GRIS)
        self._texto(p, X0 + 7, NP_Y_CABECERA + 9.5, XC - X0 - 14, 6, socio.get('nombre', ''), 11, negrita=True)
        self._texto(p, X0 + 7, NP_Y_CABECERA + 16, XC - X0 - 14, 5,
                    f"Domicilio: {socio.get('domicilio') or '—'}", 8)
        self._texto(p, X0 + 7, NP_Y_CABECERA + 21, XC - X0 - 14, 5,
                    f"C.U.I.T./D.N.I.: {socio.get('cuit_dni') or '—'} · IVA: {socio.get('condicion_iva') or '—'}", 8)
        self._texto(p, XC + 7, NP_Y_CABECERA + 4.5, 60, 5, "Proveedor:", 8.5, color=GRIS)
        self._texto(p, XC + 7, NP_Y_CABECERA + 9.5, X1 - XC - 14, 6, prov.get('nombre') or '—', 11, negrita=True)
        self._texto(p, XC + 7, NP_Y_CABECERA + 16, X1 - XC - 14, 5, f"Email: {prov.get('email') or '—'}", 8)
        self._texto(p, XC + 7, NP_Y_CABECERA + 21, X1 - XC - 14, 5, f"Teléfono: {prov.get('telefono') or '—'}", 8)

        # --- Referencias ---
        self._texto(p, X0 + 3, NP_Y_PARTES + 0.5, X1 - X0 - 6, NP_Y_REFERENCIAS - NP_Y_PARTES - 1,
                    f"Referencias: {d.get('referencias') or '—'}", 7.8, alineacion=izq, ajustar=True)

        # --- Tabla ---
        for i, (x, titulo, _clave, _alin) in enumerate(columnas):
            x_fin = columnas[i + 1][0] if i + 1 < len(columnas) else X1
            if i > 0:
                self._linea(p, x, NP_Y_REFERENCIAS, x, NP_Y_PIE, 0.3)
            self._texto(p, x, NP_Y_REFERENCIAS, x_fin - x, NP_Y_ENCABEZADO_TABLA - NP_Y_REFERENCIAS, titulo, 7.2,
                        negrita=True, alineacion=centro)

        alineaciones = {'c': centro, 'i': izq, 'd': der}
        y = NP_Y_ENCABEZADO_TABLA
        for entrada in items:
            it, alto_fila = entrada if isinstance(entrada, tuple) else (entrada, ALTO_FILA)
            faltante = it.get('entregado') is not None and it['entregado'] < (it.get('cantidad') or 0)
            for i, (x, _titulo, clave, alin) in enumerate(columnas):
                x_fin = columnas[i + 1][0] if i + 1 < len(columnas) else X1
                valor = it.get(clave)
                if clave in ('precio_unitario', 'subtotal'):
                    texto = moneda(valor)
                elif clave == 'cantidad':
                    cant_orig = it.get('cantidad_original')
                    if cant_orig is not None and cant_orig != valor:
                        texto = f"{valor} (orig. {cant_orig})"
                    else:
                        texto = str(valor)
                elif clave == 'unidad':
                    texto = valor or 'Unidad'
                elif valor is None:
                    texto = '-'
                else:
                    texto = str(valor)
                margen = 1.5 if alin != 'c' else 0.5
                resaltar = clave == 'entregado' and faltante
                self._texto(p, x + margen, y, x_fin - x - 2 * margen, alto_fila, texto, 8.5,
                            negrita=(clave == 'cantidad' or resaltar), color=NP_COLOR_FALTANTE if resaltar else NEGRO,
                            alineacion=alineaciones[alin], ajustar=(clave == 'detalle'))
            self._linea(p, X0, y + alto_fila, X1, y + alto_fila, 0.15, GRIS_CLARO, Qt.PenStyle.DotLine)
            y += alto_fila

        x_desc = next(x for (x, _t, clave, _a) in columnas if clave == 'detalle')
        x_precio = next(x for (x, _t, clave, _a) in columnas if clave == 'precio_unitario')
        x_subtotal = columnas[-1][0]
        if nro_hoja == total_hojas:
            self._texto(p, x_desc + 1.5, y, x_precio - x_desc - 3, ALTO_FILA,
                        f"TOTAL ({d.get('total_unidades', 0)} unidad(es) en {len(d.get('items', []))} renglón(es))",
                        8.5, negrita=True, alineacion=der)
            self._texto(p, x_subtotal + 1.5, y, X1 - x_subtotal - 3, ALTO_FILA, moneda(d.get('total')), 9,
                        negrita=True, alineacion=der)
        else:
            self._texto(p, x_desc + 1.5, y, X1 - x_desc - 3, ALTO_FILA, "Continúa en la hoja siguiente…", 8.5,
                        cursiva=True, color=GRIS, alineacion=izq)

        # --- Pie: estado y aclaraciones ---
        self._texto(p, X0 + 3, NP_Y_PIE + 1.5, 80, 5, "ESTADO DEL PEDIDO", 7.5, negrita=True, color=GRIS)
        self._texto(p, X0 + 3, NP_Y_PIE + 7, X1 - X0 - 6, 12, d.get('leyenda_estado', ''), 9, alineacion=arriba,
                    ajustar=True)
        aclaracion = ("Precios unitarios congelados al momento de cargar el pedido (pueden actualizarse si el proveedor "
                      "publica una lista nueva mientras el pedido esté Pendiente). Importes estimados, sin impuestos; "
                      "el importe definitivo surge de la factura.")
        if d.get('entregado'):
            aclaracion += " La columna ENTREG. indica lo recibido según el remito."
        self._texto(p, X0 + 3, NP_Y_PIE + 19, X1 - X0 - 6, 12, aclaracion, 7.3, cursiva=True, color=GRIS,
                    alineacion=arriba, ajustar=True)

        leyenda = "Copia del pedido emitida por el Sistema de Gestión Rosario Compras."
        if d.get('datos_simulados'):
            leyenda += " DATOS FISCALES SIMULADOS."
        self._texto(p, X0, Y1 + 1.5, X1 - X0, 5, leyenda, 6.8, cursiva=True, color=GRIS, alineacion=centro)


def moneda(valor):
    """1234.5 → '$ 1.234,50' (formato argentino)."""
    texto = f"{(valor or 0):,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    return f"$ {texto}"


# Geometría de la Nota de Pedido (en mm)
NP_Y_CABECERA = 50.0
NP_Y_PARTES = 82.0
NP_Y_REFERENCIAS = 90.0
NP_Y_ENCABEZADO_TABLA = 96.0
NP_FILAS_POR_HOJA = 23
NP_Y_PIE = NP_Y_ENCABEZADO_TABLA + ALTO_FILA * (NP_FILAS_POR_HOJA + 1)
# Columnas: (x inicial, título, clave del item, alineación c/i/d)
NP_COLUMNAS = [
    (X0, "CANT.", 'cantidad', 'c'), (28.0, "UNIDAD", 'unidad', 'c'), (48.0, "CÓDIGO", 'codigo', 'c'),
    (72.0, "DESCRIPCIÓN DEL PRODUCTO", 'detalle', 'i'), (148.0, "P. UNITARIO", 'precio_unitario', 'd'),
    (172.0, "SUBTOTAL", 'subtotal', 'd'),
]
NP_COLUMNAS_ENTREGA = [
    (X0, "PEDIDO", 'cantidad', 'c'), (26.0, "ENTREG.", 'entregado', 'c'), (40.0, "UNIDAD", 'unidad', 'c'),
    (58.0, "CÓDIGO", 'codigo', 'c'), (80.0, "DESCRIPCIÓN DEL PRODUCTO", 'detalle', 'i'),
    (148.0, "P. UNITARIO", 'precio_unitario', 'd'), (172.0, "SUBTOTAL", 'subtotal', 'd'),
]
NP_COLOR_ESTADO = {'Pendiente': QColor("#b45309"), 'Consolidado': QColor("#1e3a8a"),
                   'Procesado': QColor("#15803d"), 'Repartido': QColor("#15803d")}
NP_COLOR_FALTANTE = QColor("#b45309")
