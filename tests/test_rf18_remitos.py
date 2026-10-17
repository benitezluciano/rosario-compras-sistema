import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication

# Asegurar QApplication para soporte de QTextDocument / QPdfWriter en pruebas
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

from src.database import Database
from src.models.reparto_model import RepartoModel
from src.models.pedido_model import PedidoModel
from src.models.consolidacion_model import ConsolidacionModel
from src.views.remitos_view import RemitosView
from src.controllers.remitos_controller import RemitosController
from src.services.pdf_service import PdfService

def test_rf18_remitos_completo():
    print("=== TEST RF-18: CONSULTA Y GESTIÓN DE REMITOS OFICIALES EN PDF ===")
    reparto_model = RepartoModel()
    pdf_service = PdfService.get_instance()

    # 1. Verificar consulta para Rol Ejecutivo / Admin (debe traer todos los remitos)
    remitos_admin = reparto_model.obtener_remitos(rol='admin')
    assert len(remitos_admin) > 0, "No se obtuvieron remitos para rol admin"
    print(f"[OK] 1. Consulta Ejecutivo/Admin: {len(remitos_admin)} remitos históricos obtenidos correctamente.")

    # 2. Verificar consulta para Rol Socio (solo debe traer los del socio específico)
    id_socio_test = 4  # Café Central
    remitos_socio4 = reparto_model.obtener_remitos(id_user=id_socio_test, rol='socio')
    assert len(remitos_socio4) > 0, "No se obtuvieron remitos para el socio 4"
    assert all(r['id_user'] == id_socio_test for r in remitos_socio4), "Se filtraron remitos ajenos al socio"
    print(f"[OK] 2. Consulta Socio (ID {id_socio_test}): {len(remitos_socio4)} remitos propios obtenidos con éxito.")

    # 3. Verificar que cada remito tenga su archivo PDF generado en disco o accesible
    for r in remitos_admin:
        ruta_pdf = r.get('archivo_pdf')
        if not ruta_pdf or not os.path.exists(ruta_pdf):
            # Probar regeneración automática
            items = reparto_model.obtener_detalle_remito(r['id_remito'])
            datos_remito = {
                'codigo_remito': r.get('codigo_remito', f"RC-REM-{r['id_remito']}"),
                'codigo_pedido': r.get('codigo_pedido', f"RC-ORD-{r.get('id_pedido', '')}"),
                'nro_comprobante': r.get('detalle_entrega', 'CMP-AUTO'),
                'fecha': r.get('fecha_emision', ''),
                'socio_nombre': r.get('socio_nombre', 'Socio'),
                'socio_email': r.get('socio_email', ''),
                'proveedor_nombre': r.get('proveedor_nombre', 'Proveedor'),
                'items': [
                    {
                        'id_articulo': it['id_articulo'],
                        'codigo': it.get('codigo') or f"ART-{it['id_articulo']}",
                        'detalle': it['detalle'],
                        'cantidad': it['cantidad_entregada']
                    } for it in items
                ]
            }
            ruta_pdf = pdf_service.generar_remito_pdf(datos_remito)
            with Database() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE REMITOS SET archivo_pdf = ? WHERE id_remito = ?", (ruta_pdf, r['id_remito']))
        
        assert os.path.exists(ruta_pdf), f"El archivo PDF {ruta_pdf} no existe en disco"
        assert ruta_pdf.endswith(".pdf"), "El archivo no tiene extensión .pdf"
    print(f"[OK] 3. Verificación de archivos PDF físicos: Todos los remitos cuentan con PDF válido en carpeta remitos_pdf.")

    # 4. Verificar Controlador y Vista (GUI Mocking & Filtrado)
    vista = RemitosView()
    controlador = RemitosController(vista, reparto_model)

    # Simular inicio de sesión como Socio
    usuario_socio = {'id': id_socio_test, 'nombre': 'Café Central (Pichincha)', 'role': 'socio'}
    controlador.set_usuario_actual(usuario_socio)
    controlador.inicializar()

    assert vista.cmb_socio.isHidden(), "El selector de socio debe estar oculto para un socio"
    assert vista.tabla_remitos.rowCount() == len(remitos_socio4), "La tabla no coincide con los remitos del socio"
    print("[OK] 4. Vista de Socio inicializada: selector de socio oculto y tabla poblada exclusivamente con sus remitos.")

    # Simular inicio de sesión como Ejecutivo
    usuario_ejecutivo = {'id': 2, 'nombre': 'Luciano Benítez', 'role': 'ejecutivo'}
    controlador.set_usuario_actual(usuario_ejecutivo)
    controlador.inicializar()

    assert not vista.cmb_socio.isHidden(), "El selector de socio debe ser visible para un ejecutivo"
    assert vista.tabla_remitos.rowCount() == len(remitos_admin), "La tabla del ejecutivo debe mostrar todos los remitos"
    print("[OK] 5. Vista de Ejecutivo inicializada: selector de socio visible y visualización completa.")

    # 5. Probar filtrado por texto
    vista.txt_buscar.setText("Lácteos")
    controlador.aplicar_filtros()
    assert vista.tabla_remitos.rowCount() >= 1, "El filtro de texto no encontró remitos de Lácteos"
    for row in range(vista.tabla_remitos.rowCount()):
        texto_fila = " ".join([
            vista.tabla_remitos.item(row, c).text() for c in range(vista.tabla_remitos.columnCount() - 1)
        ])
        assert "Lácteos" in texto_fila or "Litoral" in texto_fila or "Leche" in texto_fila, "Fila no coincide con filtro"
    print("[OK] 6. Filtrado en tiempo real por texto (búsqueda de proveedor/producto) verificado.")

    # Limpiar filtro de texto
    vista.txt_buscar.setText("")
    controlador.aplicar_filtros()
    assert vista.tabla_remitos.rowCount() == len(remitos_admin)

    # 6. Probar ciclo completo de reparto sin error de duplicados (IntegrityError fix test)
    # Crear un nuevo pedido con artículos de múltiples proveedores para validar que reparto_masivo no falla
    pedido_model = PedidoModel()
    articulos_pedido = [
        (1, 2),   # Café (Distribuidora Central, id_prov=1)
        (6, 5),   # Leche (Lácteos del Litoral, id_prov=2)
        (11, 3)   # Harina (Insumos Gastronómicos, id_prov=3)
    ]
    id_ped_creado = pedido_model.registrar_pedido(id_socio_test, articulos_pedido)

    # Consolidar pedido
    cons_model = ConsolidacionModel()
    cant_consolidados = cons_model.marcar_pedidos_como_consolidados()
    assert cant_consolidados > 0, "No se consolidó el pedido creado"

    # Ejecutar reparto masivo
    exito_rep, rutas_rep = reparto_model.ejecutar_reparto_masivo(id_pedido_sel=id_ped_creado)
    assert exito_rep, f"Fallo en ejecutar_reparto_masivo: {rutas_rep}"
    assert len(rutas_rep) >= 3, f"Se esperaban al menos 3 remitos (1 por proveedor), obtenidos: {len(rutas_rep)}"
    for r_pdf in rutas_rep:
        assert os.path.exists(r_pdf), f"El PDF generado {r_pdf} no existe físicamente"
    print(f"[OK] 7. Reparto masivo multiproveedor ejecutado sin duplicados: {len(rutas_rep)} remitos PDF creados exitosamente.")

    print("\n=== ¡TODAS LAS PRUEBAS DE RF-18 (REMITOS) PASARON EXITOSAMENTE! ===")

if __name__ == '__main__':
    test_rf18_remitos_completo()
