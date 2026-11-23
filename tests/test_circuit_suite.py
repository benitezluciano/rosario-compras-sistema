"""
Prueba integral del circuito operativo (pedidos por proveedor).

Se ejecuta sobre una base temporal creada con el seed (seeds/seed_db.py) y carpetas
temporales para PDFs y órdenes de compra, por lo que no depende ni modifica los datos
reales del proyecto.
Uso:  python tests/test_circuit_suite.py
"""
import os
import sys
import shutil
import tempfile
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication

# Asegurar instancia de QApplication para servicios que utilizan QTextDocument/QPdfWriter
app = QApplication.instance() or QApplication(sys.argv)

# --- Aislar la prueba: base (sembrada con el seed), PDFs y órdenes en un directorio temporal ---
import src.database as database
import seeds.seed_db as seed_db
TMP_DIR = tempfile.mkdtemp(prefix="rc_test_")
TMP_DB = os.path.join(TMP_DIR, "database.db")
seed_db.DB_PATH = TMP_DB
seed_db.seed()
database.DB_PATH = TMP_DB

from src.services.pdf_service import PdfService
PdfService.get_instance().carpeta_remitos = os.path.join(TMP_DIR, "remitos_pdf")
os.makedirs(PdfService.get_instance().carpeta_remitos, exist_ok=True)

from src.services.orden_compra_service import OrdenCompraService
OrdenCompraService.get_instance().carpeta_ordenes = os.path.join(TMP_DIR, "ordenes_compra")

from src.database import Database
from src.models.auth_model import AuthModel
from src.models.catalogo_model import CatalogoModel
from src.models.pedido_model import PedidoModel
from src.models.consolidacion_model import ConsolidacionModel
from src.models.reparto_model import RepartoModel
from src.models.notificacion_model import NotificacionModel
from src.models.historial_ejecutivo_model import HistorialEjecutivoModel
from src.models.remito_model import RemitoModel
import re

PROV_CENTRAL, PROV_LACTEOS, PROV_FRIGORIFICO, PROV_BEBIDAS = 1, 2, 4, 5


def consultar(sql, params=()):
    with Database() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def run_tests():
    print("=== INICIANDO PRUEBAS DEL CIRCUITO (PEDIDOS POR PROVEEDOR) ===")
    print(f"(Base temporal: {TMP_DB})")

    notif_model = NotificacionModel()

    # 1. AUTENTICACIÓN
    auth = AuthModel()
    ejec_u, _ = auth.autenticar_usuario('ejecutivo@rosariocompras.com', 'account123')
    socio_u, _ = auth.autenticar_usuario('socio8@rosariocompras.com', 'socio123')  # El Parque: sin pedidos previos
    assert ejec_u and socio_u, "Fallo en login de roles"
    print("[OK] 1. Autenticación correcta.")

    # 2. IMPORTACIÓN: busca artículos dentro del proveedor y habilita la lista
    cat_model = CatalogoModel()
    ruta_lista = os.path.join(TMP_DIR, "lista_bebidas.xlsx")
    pd.DataFrame([
        # Mismo nombre que un artículo de Distribuidora Central: debe crearse uno NUEVO para Bebidas
        {'Codigo': 'BEB-900', 'Detalle': 'Café en Grano Tostado Especial x 1kg', 'Rubro': 'Cafetería', 'Precio': 15000.0, 'Descuento': 0.0},
        {'Codigo': 'BEB-001', 'Detalle': 'Agua Mineral sin Gas x 1.5L (Pack 6u)', 'Rubro': 'Bebidas', 'Precio': 4500.0, 'Descuento': 0.0},
    ]).to_excel(ruta_lista, index=False)
    exito, msg = cat_model.importar_lista_proveedor(PROV_BEBIDAS, ruta_lista)
    assert exito, msg

    compartidos = consultar("""
        SELECT id_articulo FROM PRECIOS_NEGOCIADOS GROUP BY id_articulo HAVING COUNT(*) > 1
    """)
    assert not compartidos, f"Hay artículos compartidos entre proveedores: {compartidos}"
    agua = consultar("SELECT COUNT(*) n FROM ARTICULOS WHERE detalle LIKE 'Agua Mineral%'")[0]['n']
    assert agua == 1, "El artículo existente (por código) debió actualizarse, no duplicarse"
    assert consultar("SELECT lista_habilitada FROM PROVEEDORES WHERE id_proveedor=?", (PROV_BEBIDAS,))[0]['lista_habilitada'] == 1
    print("[OK] 2. Importación por proveedor: sin artículos compartidos y lista habilitada.")

    # 3. EL SOCIO SOLO VE LISTAS HABILITADAS
    ped_model = PedidoModel()
    habilitados = {p['id_proveedor'] for p in ped_model.obtener_proveedores()}
    assert PROV_FRIGORIFICO not in habilitados and PROV_LACTEOS in habilitados, habilitados
    catalogo = ped_model.obtener_catalogo_articulos()
    assert all(a['id_proveedor'] in habilitados for a in catalogo)
    print("[OK] 3. El socio solo ve las listas habilitadas.")

    # 4. "ENVIAR TODO": un pedido independiente por proveedor
    art_central = [a['id_articulo'] for a in catalogo if a['id_proveedor'] == PROV_CENTRAL][:2]
    art_lacteos = [a['id_articulo'] for a in catalogo if a['id_proveedor'] == PROV_LACTEOS][:1]
    resultados = ped_model.guardar_pedidos(socio_u['id'], {
        PROV_CENTRAL: [(art_central[0], 3), (art_central[1], 2)],
        PROV_LACTEOS: [(art_lacteos[0], 10)],
    })
    assert len(resultados) == 2 and all(r['es_nuevo'] for r in resultados)
    vigentes = ped_model.obtener_pedidos_vigentes(socio_u['id'])
    assert set(vigentes) == {PROV_CENTRAL, PROV_LACTEOS}
    id_ped_lacteos = vigentes[PROV_LACTEOS]['id_pedido']
    id_ped_central = vigentes[PROV_CENTRAL]['id_pedido']

    # Editar la hoja de Lácteos actualiza el MISMO pedido (uno pendiente por proveedor)
    r = ped_model.guardar_pedido_proveedor(socio_u['id'], PROV_LACTEOS, [(art_lacteos[0], 12)])
    assert r['id_pedido'] == id_ped_lacteos and not r['es_nuevo']

    # Pedir sobre una lista cerrada o con artículos ajenos debe fallar
    for invalido in ({PROV_FRIGORIFICO: [(15, 1)]}, {PROV_LACTEOS: [(art_central[0], 1)]}):
        try:
            ped_model.guardar_pedidos(socio_u['id'], invalido)
            raise AssertionError(f"Debió rechazarse: {invalido}")
        except ValueError:
            pass

    notifs_ejec = notif_model.obtener_notificaciones_usuario(ejec_u['id'], ejec_u['role'])
    assert sum(1 for n in notifs_ejec if n['tipo'] == 'nuevo_pedido' and 'El Parque' in n['mensaje']) == 2
    print("[OK] 4. 'Enviar todo' generó 2 pedidos separados; edición, validaciones y notificaciones OK.")

    # 5. PRECIO CONGELADO: una lista nueva actualiza solo los pedidos 'Pendiente'
    precio_antes = consultar("SELECT precio_unitario FROM DETALLE_PEDIDOS WHERE id_pedido=?", (id_ped_lacteos,))[0]['precio_unitario']
    precio_consolidado_antes = consultar("SELECT precio_unitario FROM DETALLE_PEDIDOS WHERE id_pedido=12")
    ruta_lacteos = os.path.join(TMP_DIR, "lista_lacteos.xlsx")
    detalle_lacteo = consultar("SELECT detalle, id_articulo_proveedor FROM ARTICULOS WHERE id_articulo=?", (art_lacteos[0],))[0]
    pd.DataFrame([{'Codigo': detalle_lacteo['id_articulo_proveedor'], 'Detalle': detalle_lacteo['detalle'],
                   'Rubro': 'Lácteos', 'Precio': precio_antes + 1000, 'Descuento': 0.0}]).to_excel(ruta_lacteos, index=False)
    assert cat_model.importar_lista_proveedor(PROV_LACTEOS, ruta_lacteos)[0]
    precio_despues = consultar("SELECT precio_unitario FROM DETALLE_PEDIDOS WHERE id_pedido=?", (id_ped_lacteos,))[0]['precio_unitario']
    assert precio_despues == precio_antes + 1000, (precio_antes, precio_despues)
    assert consultar("SELECT precio_unitario FROM DETALLE_PEDIDOS WHERE id_pedido=12") == precio_consolidado_antes
    print("[OK] 5. Lista nueva: pedidos pendientes toman el precio nuevo; consolidados quedan congelados.")

    # 6. CONSOLIDACIÓN POR PROVEEDOR
    cons_model = ConsolidacionModel()
    matriz = cons_model.obtener_matriz_pedidos_proveedor(PROV_LACTEOS)
    pedidos_matriz = {s['id_pedido'] for s in matriz['socios']}
    prov_matriz = {r['id_proveedor'] for r in consultar(
        f"SELECT id_proveedor FROM PEDIDOS WHERE id_pedido IN ({','.join('?' * len(pedidos_matriz))})", list(pedidos_matriz))}
    assert prov_matriz == {PROV_LACTEOS}, prov_matriz

    # Planilla borrador (antes de consolidar) solo del proveedor seleccionado
    ruta_borrador = os.path.join(TMP_DIR, "borrador_lacteos.xlsx")
    exito_exp, msg_exp = cons_model.exportar_planilla(ruta_borrador, PROV_LACTEOS)
    assert exito_exp, msg_exp
    assert set(pd.read_excel(ruta_borrador, sheet_name='Resumen Consolidado')['Proveedor']) == {'Lácteos del Litoral'}

    total_esperado = round(sum(r['total_estimado'] for r in cons_model.obtener_resumen_consolidado(PROV_LACTEOS)), 2)
    ejecutivo = {'id': ejec_u['id'], 'nombre': ejec_u['nombre'], 'email': ejec_u['email']}
    orden = cons_model.consolidar_proveedor(PROV_LACTEOS, ejecutivo=ejecutivo)
    cant = orden['cantidad_pedidos']
    assert cant == len(pedidos_matriz)
    estado = {r['id_pedido']: r['estado'] for r in consultar(
        "SELECT id_pedido, estado FROM PEDIDOS WHERE id_pedido IN (?, ?)", (id_ped_lacteos, id_ped_central))}
    assert estado[id_ped_lacteos] == 'Consolidado' and estado[id_ped_central] == 'Pendiente', estado
    assert consultar("SELECT lista_habilitada FROM PROVEEDORES WHERE id_proveedor=?", (PROV_LACTEOS,))[0]['lista_habilitada'] == 0
    print(f"[OK] 6. Consolidación de Lácteos: {cant} pedidos; los de otros proveedores siguen pendientes; lista cerrada.")

    # 6b. ORDEN DE COMPRA generada al consolidar
    assert orden['codigo'].startswith('RC-OC-') and abs(orden['total'] - total_esperado) < 0.01, (orden['total'], total_esperado)
    assert os.path.exists(orden['ruta_archivo']) and orden['ruta_archivo'].startswith(TMP_DIR)
    hoja = pd.read_excel(orden['ruta_archivo'], header=None).astype(str).to_string()
    assert orden['codigo'] in hoja and 'Lácteos del Litoral' in hoja
    vinculados = consultar("SELECT COUNT(*) n FROM PEDIDOS WHERE id_orden_compra=?", (orden['id_orden_compra'],))[0]['n']
    assert vinculados == cant
    assert consultar("SELECT id_orden_compra FROM PEDIDOS WHERE id_pedido=?", (id_ped_central,))[0]['id_orden_compra'] is None

    # Si el archivo se pierde, se regenera desde la base (también para órdenes del seed sin archivo)
    os.remove(orden['ruta_archivo'])
    assert os.path.exists(cons_model.asegurar_archivo_orden(orden['id_orden_compra']))
    assert os.path.exists(cons_model.asegurar_archivo_orden(1))

    cons_model.registrar_envio_orden(orden['id_orden_compra'], 'pedidos@lacteosdellitoral.com')
    enviada = cons_model.obtener_orden_compra(orden['id_orden_compra'])
    assert enviada['fecha_envio_email'] and enviada['email_destino'] == 'pedidos@lacteosdellitoral.com'
    assert cons_model.consolidar_proveedor(PROV_LACTEOS, ejecutivo=ejecutivo) is None, "Sin pendientes no debe emitir otra orden"
    print(f"[OK] 6b. Orden de Compra {orden['codigo']}: Excel generado (${orden['total']:,.2f}), pedidos vinculados, regeneración y envío registrados.")

    # 7. RECEPCIÓN Y REPARTO POR PROVEEDOR (con faltante y prorrateo)
    rep_model = RepartoModel()
    control = rep_model.obtener_articulos_control_recepcion(PROV_LACTEOS)
    assert control, "No hay artículos para control de recepción"
    items = [{
        'id_articulo': a['id_articulo'],
        'cantidad_pedida': a['cantidad_demandada'],
        'cantidad_recibida': max(1, a['cantidad_demandada'] - 2),
        'precio_pactado': a['precio_pactado'],
        'precio_facturado': a['precio_pactado'],
    } for a in control]
    assert rep_model.registrar_comprobante_y_stock(PROV_LACTEOS, 'Factura', 'FC-TEST-001', '2026-10-03', 'Test', items) > 0

    discrepancias = rep_model.validar_stock_vs_pedidos(PROV_LACTEOS)
    ajustes = {(id_ped, d['id_articulo']): c for d in discrepancias for id_ped, c in d['ajustes'].items()}

    consolidados_frig_antes = consultar("SELECT COUNT(*) n FROM PEDIDOS WHERE id_proveedor=? AND estado='Consolidado'", (PROV_FRIGORIFICO,))[0]['n']
    pedidos_lacteos = {p['id_pedido'] for p in rep_model.obtener_pedidos_consolidados_por_proveedor(PROV_LACTEOS)}
    exito_rep, pdfs = rep_model.ejecutar_reparto_masivo(PROV_LACTEOS, ajustes=ajustes or None)
    assert exito_rep

    remitos = consultar("SELECT id_pedido, id_proveedor, codigo_comercial FROM REMITOS WHERE id_proveedor=? AND id_pedido IS NOT NULL", (PROV_LACTEOS,))
    remitos_nuevos = [r for r in remitos if r['id_pedido'] in pedidos_lacteos]
    assert len(remitos_nuevos) == len(pedidos_lacteos), "Debe haber exactamente un remito por pedido"
    assert len({r['codigo_comercial'] for r in remitos}) == len(remitos), "Los códigos de remito deben ser únicos"
    assert len(pdfs) == len(pedidos_lacteos)
    assert all(r['estado'] == 'Procesado' for r in consultar(
        f"SELECT estado FROM PEDIDOS WHERE id_pedido IN ({','.join('?' * len(pedidos_lacteos))})", list(pedidos_lacteos)))
    assert consultar("SELECT COUNT(*) n FROM PEDIDOS WHERE id_proveedor=? AND estado='Consolidado'", (PROV_FRIGORIFICO,))[0]['n'] == consolidados_frig_antes
    assert consultar("SELECT estado FROM PEDIDOS WHERE id_pedido=?", (id_ped_central,))[0]['estado'] == 'Pendiente'

    notifs_socio = notif_model.obtener_notificaciones_usuario(socio_u['id'], 'socio')
    assert any(n['tipo'] == 'reparto' for n in notifs_socio), "El socio no recibió su remito"
    print(f"[OK] 7. Reparto de Lácteos: {len(remitos_nuevos)} remitos (uno por pedido, códigos únicos); otros proveedores intactos.")

    # 7b. REMITO CON FORMATO DEL MODELO (número formal, datos fiscales, unidad, observaciones, 2 copias)
    numeros = consultar("SELECT id_remito, numero_remito FROM REMITOS WHERE id_proveedor=? ORDER BY id_remito", (PROV_LACTEOS,))
    assert all(re.fullmatch(r"\d{4}-\d{8}", r['numero_remito']) for r in numeros), numeros
    assert len({r['numero_remito'] for r in numeros}) == len(numeros), "Los números de remito deben ser únicos"
    rem_model = RemitoModel()
    id_rem_socio = consultar("SELECT id_remito FROM REMITOS WHERE id_pedido=?", (id_ped_lacteos,))[0]['id_remito']
    datos_rem = rem_model.obtener_datos_remito(id_rem_socio)
    assert datos_rem['letra'] == 'X' and datos_rem['destinatario']['nombre'].startswith('Cafetería & Brunch El Parque')
    assert datos_rem['destinatario']['domicilio'] and datos_rem['destinatario']['cuit_dni'] == 'XX-XXXXXXXX-X'
    assert all(i['unidad'] for i in datos_rem['items']) and 'Orden de Compra' in datos_rem['referencias']
    assert datos_rem['observaciones'].startswith('Entrega del pedido')
    if ajustes:
        assert any('Por faltante del proveedor' in rem_model.obtener_datos_remito(r['id_remito'])['observaciones'] for r in numeros)
    from PyQt6.QtPdf import QPdfDocument
    pdf_doc = QPdfDocument(None)
    ruta_pdf_socio = rem_model.asegurar_pdf(id_rem_socio)
    pdf_doc.load(ruta_pdf_socio)
    assert pdf_doc.pageCount() == 2, "El remito debe tener ORIGINAL y DUPLICADO"
    texto_pdf = pdf_doc.getAllText(0).text()
    pdf_doc.close()
    # (Sin fuentes del sistema, p. ej. QT_QPA_PLATFORM=offscreen, el PDF no incluye texto extraíble)
    if texto_pdf.strip():
        assert datos_rem['numero'] in texto_pdf and 'NO VÁLIDO' in texto_pdf, texto_pdf[:300]
    # Remito del seed sin PDF: se regenera con el formato nuevo
    assert rem_model.ruta_pdf_existente(consultar("SELECT codigo_comercial FROM REMITOS WHERE id_remito=1")[0]['codigo_comercial']) is None
    assert os.path.exists(rem_model.asegurar_pdf(1))
    print(f"[OK] 7b. Remito X {datos_rem['numero']}: datos fiscales, unidades, referencias y observaciones; PDF con 2 copias; regeneración OK.")

    # 8. HISTORIAL con proveedor y total por precio congelado
    historial = ped_model.obtener_historial_pedidos(socio_u['id'])
    assert len(historial) == 2 and all(h['proveedor_nombre'] for h in historial)
    h_lacteos = next(h for h in historial if h['id_pedido'] == id_ped_lacteos)
    assert abs(h_lacteos['total_estimado'] - 12 * precio_despues) < 0.01
    print("[OK] 8. Historial con proveedor y totales calculados con el precio congelado.")

    # 9. HISTORIAL DEL EJECUTIVO
    hist = HistorialEjecutivoModel()
    ordenes = hist.obtener_ordenes()
    assert ordenes[0]['id_orden_compra'] == orden['id_orden_compra'], "La orden más reciente va primero"
    assert all(o['id_proveedor'] == PROV_LACTEOS for o in hist.obtener_ordenes(PROV_LACTEOS))

    ids = lambda lista: {o['id_orden_compra'] for o in lista}
    repartidas = ids(hist.obtener_ordenes(estado=hist.ESTADO_REPARTIDA))
    pendientes = ids(hist.obtener_ordenes(estado=hist.ESTADO_PENDIENTE_ENTREGA))
    sin_enviar = ids(hist.obtener_ordenes(estado=hist.ESTADO_SIN_ENVIAR))
    assert orden['id_orden_compra'] in repartidas and 1 in pendientes and not (repartidas & pendientes)
    assert 2 in sin_enviar and orden['id_orden_compra'] not in sin_enviar

    pedidos_orden = hist.obtener_pedidos_de_orden(orden['id_orden_compra'])
    assert len(pedidos_orden) == cant and all(p['remito_codigo'] for p in pedidos_orden)

    remitos_hist = hist.obtener_remitos(PROV_LACTEOS)
    nuevos = [r for r in remitos_hist if r['orden_codigo'] == orden['codigo']]
    assert len(nuevos) == len(pedidos_lacteos) and all(r['ruta_pdf'] for r in nuevos), "Los remitos nuevos tienen PDF"
    assert any(r['ruta_pdf'] is None for r in remitos_hist), "El remito 2 del seed no tiene PDF"
    assert all(r['socio_nombre'] == 'Cafetería & Brunch El Parque (Parque Urquiza)'
               for r in hist.obtener_remitos(id_socio=socio_u['id']))

    con_dif = {c['nro_comprobante'] for c in hist.obtener_comprobantes(control=hist.CONTROL_CON_DIFERENCIAS)}
    sin_dif = {c['nro_comprobante'] for c in hist.obtener_comprobantes(control=hist.CONTROL_SIN_DIFERENCIAS)}
    assert {'FC-TEST-001', 'REM-R-0002-00018944'} <= con_dif and 'FC-A-0001-00045120' in sin_dif
    id_comp_test = next(c['id_comprobante'] for c in hist.obtener_comprobantes(PROV_LACTEOS) if c['nro_comprobante'] == 'FC-TEST-001')
    assert any(d['diferencia'] < 0 for d in hist.obtener_detalle_comprobante(id_comp_test))
    print(f"[OK] 9. Historial del ejecutivo: {len(ordenes)} órdenes (filtros de entrega y envío), remitos con/sin PDF y comprobantes con diferencias.")

    print("\n=== ¡CIRCUITO COMPLETO VERIFICADO CON ÉXITO (11/11 PRUEBAS OK)! ===")


if __name__ == '__main__':
    try:
        run_tests()
    finally:
        shutil.rmtree(TMP_DIR, ignore_errors=True)
