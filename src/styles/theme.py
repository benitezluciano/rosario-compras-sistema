"""
Sistema de Estilos QSS Centralizado para Rosario Compras.
Diseño moderno, accesible y con jerarquía visual semántica.
"""

GLOBAL_STYLESHEET = """
/* --- CONFIGURACIÓN GLOBAL Y TIPOGRAFÍA --- */
QWidget {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
    color: #1e293b;
}

QMainWindow, QDialog {
    background-color: #f8fafc;
}

/* --- BARRA SUPERIOR DE SESIÓN --- */
#barra_sesion {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
}

#lbl_usuario_info {
    font-size: 13px;
    font-weight: 600;
    color: #1e293b;
    padding-left: 4px;
}

/* --- MENÚ LATERAL (SIDEBAR) --- */
QListWidget#menu_lateral {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    outline: none;
}

QListWidget#menu_lateral::item {
    padding: 12px 14px;
    margin: 4px 6px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    color: #334155;
}

QListWidget#menu_lateral::item:hover:!selected {
    background-color: #f1f5f9;
    color: #0f172a;
}

QListWidget#menu_lateral::item:selected {
    background-color: #1e293b;
    color: #ffffff;
    font-weight: bold;
}

/* --- ENCABEZADOS Y TÍTULOS DE PANTALLA --- */
QLabel#lbl_titulo {
    font-size: 18px;
    font-weight: bold;
    color: #0f172a;
    padding: 6px 0;
}

QLabel#lbl_sec1, QLabel#lbl_sec2 {
    font-size: 13px;
    font-weight: bold;
    color: #1e40af;
    padding-top: 4px;
}

/* --- ENTRADAS DE TEXTO Y COMBOS --- */
QLineEdit, QComboBox {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 6px 10px;
    color: #1e293b;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus {
    border: 2px solid #3b82f6;
    background-color: #ffffff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #e2e8f0;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    selection-background-color: #e0e7ff;
    selection-color: #1e3a8a;
    padding: 4px;
}

/* --- TABLAS (QTableWidget) --- */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    gridline-color: #e2e8f0;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    selection-background-color: #dbeafe;
    selection-color: #1e3a8a;
}

QHeaderView::section {
    background-color: #f1f5f9;
    color: #334155;
    font-weight: bold;
    font-size: 12px;
    padding: 8px 6px;
    border: none;
    border-bottom: 2px solid #cbd5e1;
    border-right: 1px solid #e2e8f0;
}

QTableWidget::item {
    padding: 6px 8px;
}

/* --- JERARQUÍA SEMÁNTICA DE BOTONES --- */
QPushButton {
    font-size: 13px;
    font-weight: 600;
    border-radius: 6px;
    padding: 8px 16px;
    border: 1px solid transparent;
}

/* 1. Botones Primarios (Acción Principal / CTA) - Azul Índigo */
QPushButton#btn_confirmar,
QPushButton#btn_consolidar,
QPushButton#btn_ejecutar,
QPushButton#btn_importar,
QPushButton#btn_login {
    background-color: #2563eb;
    color: #ffffff;
}

QPushButton#btn_confirmar:hover,
QPushButton#btn_consolidar:hover,
QPushButton#btn_ejecutar:hover,
QPushButton#btn_importar:hover,
QPushButton#btn_login:hover {
    background-color: #1d4ed8;
}

QPushButton#btn_confirmar:pressed,
QPushButton#btn_consolidar:pressed,
QPushButton#btn_ejecutar:pressed,
QPushButton#btn_importar:pressed,
QPushButton#btn_login:pressed {
    background-color: #1e40af;
}

/* 2. Botones de Éxito / Exportación Excel - Verde Esmeralda */
QPushButton#btn_exportar,
QPushButton#btn_exportar_proveedores {
    background-color: #10b981;
    color: #ffffff;
}

QPushButton#btn_exportar:hover,
QPushButton#btn_exportar_proveedores:hover {
    background-color: #059669;
}

QPushButton#btn_exportar:pressed,
QPushButton#btn_exportar_proveedores:pressed {
    background-color: #047857;
}

/* 3. Botones Secundarios y de Acción Rápida - Superficie Neutra */
QPushButton#btn_solicitar_lista,
QPushButton#btn_seleccionar_archivo,
QPushButton#btn_refrescar,
QPushButton#btn_guardar_comprobante,
QPushButton#btn_actualizar_stock {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
}

QPushButton#btn_solicitar_lista:hover,
QPushButton#btn_seleccionar_archivo:hover,
QPushButton#btn_refrescar:hover,
QPushButton#btn_guardar_comprobante:hover,
QPushButton#btn_actualizar_stock:hover {
    background-color: #f1f5f9;
    border-color: #94a3b8;
    color: #0f172a;
}

/* 4. Botón de Notificaciones - Ámbar Destacado */
QPushButton#btn_notificaciones {
    background-color: #f59e0b;
    color: #ffffff;
    font-weight: bold;
}

QPushButton#btn_notificaciones:hover {
    background-color: #d97706;
}

/* 5. Botón de Cerrar Sesión - Rojo Coral */
QPushButton#btn_logout {
    background-color: #ef4444;
    color: #ffffff;
    font-weight: bold;
}

QPushButton#btn_logout:hover {
    background-color: #dc2626;
}

/* --- TARJETAS GROUPBOX --- */
QGroupBox {
    font-size: 13px;
    font-weight: bold;
    color: #1e3a8a;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 14px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 3px 10px;
    background-color: #e0e7ff;
    color: #1e3a8a;
    border-radius: 4px;
    font-size: 12px;
}

/* --- SCROLLBARS MODERNOS --- */
QScrollBar:vertical {
    border: none;
    background: #f1f5f9;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
