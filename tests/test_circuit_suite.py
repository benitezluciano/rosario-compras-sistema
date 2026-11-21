"""
Prueba integral del circuito operativo (pedidos por proveedor).

Se ejecuta sobre una COPIA temporal de database.db y una carpeta temporal de PDFs,
por lo que no modifica los datos reales del proyecto.
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

# --- Aislar la prueba: base y PDFs en un directorio temporal ---
import src.database as database
TMP_DIR = tempfile.mkdtemp(prefix="rc_test_")
TMP_DB = os.path.join(TMP_DIR, "database.db")
shutil.copyfile(database.DB_PATH, TMP_DB)
database.DB_PATH = TMP_DB

from src.services.pdf_service import PdfService
PdfService.get_instance().carpeta_remitos = os.path.join(TMP_DIR, "remitos_pdf")
os.makedirs(PdfService.get_instance().carpeta_remitos, exist_ok=True)

from src.database import Database
from src.models.auth_model import AuthModel
from src.models.catalogo_model import CatalogoModel
from src.models.pedido_model import PedidoModel
from src.models.consolidacion_model import ConsolidacionModel
from src.models.reparto_model import RepartoModel
from src.models.notificacion_model import NotificacionModel

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

    exito_exp, msg_exp = cons_model.exportar_ordenes_por_proveedor(TMP_DIR, PROV_LACTEOS)
    assert exito_exp, msg_exp

    cant = cons_model.marcar_pedidos_como_consolidados(PROV_LACTEOS)
    assert cant == len(pedidos_matriz)
    estado = {r['id_pedido']: r['estado'] for r in consultar(
        "SELECT id_pedido, estado FROM PEDIDOS WHERE id_pedido IN (?, ?)", (id_ped_lacteos, id_ped_central))}
    assert estado[id_ped_lacteos] == 'Consolidado' and estado[id_ped_central] == 'Pendiente', estado
    assert consultar("SELECT lista_habilitada FROM PROVEEDORES WHERE id_proveedor=?", (PROV_LACTEOS,))[0]['lista_habilitada'] == 0
    print(f"[OK] 6. Consolidación de Lácteos: {cant} pedidos; los de otros proveedores siguen pendientes; lista cerrada.")

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

    # 8. HISTORIAL con proveedor y total por precio congelado
    historial = ped_model.obtener_historial_pedidos(socio_u['id'])
    assert len(historial) == 2 and all(h['proveedor_nombre'] for h in historial)
    h_lacteos = next(h for h in historial if h['id_pedido'] == id_ped_lacteos)
    assert abs(h_lacteos['total_estimado'] - 12 * precio_despues) < 0.01
    print("[OK] 8. Historial con proveedor y totales calculados con el precio congelado.")

    print("\n=== ¡CIRCUITO COMPLETO VERIFICADO CON ÉXITO (8/8 PRUEBAS OK)! ===")


if __name__ == '__main__':
    try:
        run_tests()
    finally:
        shutil.rmtree(TMP_DIR, ignore_errors=True)
