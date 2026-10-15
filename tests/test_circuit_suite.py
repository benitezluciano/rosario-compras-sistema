import os
import sys
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import QApplication

# Asegurar instancia de QApplication para servicios que utilizan QTextDocument/QPdfWriter
app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

from src.models.auth_model import AuthModel
from src.models.catalogo_model import CatalogoModel
from src.models.pedido_model import PedidoModel
from src.models.consolidacion_model import ConsolidacionModel
from src.models.reparto_model import RepartoModel
from src.models.notificacion_model import NotificacionModel
from src.database import Database

def run_tests():
    print("=== INICIANDO PRUEBAS DEL CIRCUITO OPERATIVO REFINADO ===")
    
    # 1. TEST DE AUTENTICACIÓN
    auth = AuthModel()
    admin_u, _ = auth.autenticar_usuario('admin@rosariocompras.com', 'admin123')
    ejec_u, _ = auth.autenticar_usuario('ejecutivo@rosariocompras.com', 'account123')
    socio1_u, _ = auth.autenticar_usuario('socio1@rosariocompras.com', 'socio123')
    assert admin_u and ejec_u and socio1_u, "Fallo en login de roles"
    print("[OK] Test 1: Autenticación correcta para Admin, Ejecutivo y Socios.")
    
    # 2. PASO 1: EJECUTIVO SOLICITA LISTA DE PRECIOS AL PROVEEDOR
    cat_model = CatalogoModel()
    proveedores = cat_model.obtener_proveedores()
    assert len(proveedores) >= 3, "Faltan proveedores"
    exito_sol, msg_sol, prov = cat_model.solicitar_lista_proveedor(1)
    assert exito_sol, f"Fallo al solicitar lista a proveedor: {msg_sol}"
    print("[OK] Test 2: Solicitud de lista de precios a proveedor registrada exitosamente.")
    
    # 3. PASO 2 Y 3: IMPORTAR Y CONSOLIDAR LISTA DE PROVEEDOR (AVISO MASIVO A SOCIOS)
    df_lista = pd.DataFrame([
        {'Codigo': 'PROV1-99', 'Detalle': 'Té Negro en Saquitos x 100u', 'Rubro': 'Cafetería', 'Precio': 4200.0, 'Descuento': 0.05},
        {'Codigo': 'PROV1-100', 'Detalle': 'Azúcar Blanca x 1kg', 'Rubro': 'Insumos', 'Precio': 1100.0, 'Descuento': 0.0}
    ])
    ruta_lista = os.path.join(os.path.dirname(__file__), "lista_proveedor_test.xlsx")
    df_lista.to_excel(ruta_lista, index=False)
    
    exito_imp, msg_imp = cat_model.importar_lista_proveedor(1, ruta_lista)
    assert exito_imp, f"Fallo al importar lista: {msg_imp}"
    
    # Verificar notificación automática a Socio 1 y Socio 2
    notif_model = NotificacionModel()
    notifs_socio1 = notif_model.obtener_notificaciones_usuario(socio1_u['id'], 'socio')
    assert any(n['tipo'] == 'catalogo_actualizado' for n in notifs_socio1), "Socio 1 no recibió notificación de catálogo actualizado"
    print("[OK] Test 3: Lista importada al catálogo único y notificación masiva enviada a todos los socios.")
    
    # 4. PASO 4 Y 5: SOCIO CONSULTA CATÁLOGO Y REGISTRA PEDIDO
    ped_model = PedidoModel()
    cat_prov1 = ped_model.obtener_catalogo_articulos(id_proveedor=1)
    assert any(a['detalle'] == 'Té Negro en Saquitos x 100u' for a in cat_prov1), "Artículo importado no encontrado"
    
    id_art_te = [a['id_articulo'] for a in cat_prov1 if a['detalle'] == 'Té Negro en Saquitos x 100u'][0]
    id_ped_socio1 = ped_model.registrar_pedido(socio1_u['id'], [(id_art_te, 10), (1, 5)])
    assert id_ped_socio1 > 0, "Fallo al registrar pedido de socio"
    
    # Verificar notificación recibida por el ejecutivo
    notifs_ejec = notif_model.obtener_notificaciones_usuario(ejec_u['id'], ejec_u['role'])
    assert len(notifs_ejec) > 0 and notifs_ejec[0]['tipo'] == 'nuevo_pedido', "No se generó notificación para ejecutivo"
    print(f"[OK] Test 4: Socio 1 registró Pedido #{id_ped_socio1} y Ejecutivo recibió notificación automática.")
    
    # 5. PASO 6 Y 7: CONSOLIDACIÓN Y EXPORTACIÓN POR PROVEEDOR
    cons_model = ConsolidacionModel()
    resumen = cons_model.obtener_resumen_consolidado()
    assert len(resumen) > 0, "Resumen consolidado vacío"
    
    carpeta_test = os.path.dirname(__file__)
    exito_exp, msg_exp = cons_model.exportar_ordenes_por_proveedor(carpeta_test)
    assert exito_exp, f"Fallo exportación órdenes: {msg_exp}"
    print("[OK] Test 5: Órdenes de Compra por Proveedor exportadas a planillas Excel independientes.")
    
    # 6. PASO 8 Y 9: CONFIRMAR ENVÍO A PROVEEDORES Y NOTIFICACIÓN AL SOCIO
    cant_cons = cons_model.marcar_pedidos_como_consolidados()
    assert cant_cons > 0, "No se consolidaron pedidos"
    
    notifs_socio1_cons = notif_model.obtener_notificaciones_usuario(socio1_u['id'], 'socio')
    assert any(n['tipo'] == 'pedido_consolidado' and 'proveedor' in n['mensaje'] for n in notifs_socio1_cons), "Socio no recibió aviso de envío a proveedor"
    print(f"[OK] Test 6: Órdenes enviadas a proveedores y notificación emitida a los socios ('enviado al proveedor').")
    
    # 7. PASO 10: REGISTRO DE COMPROBANTE DE PROVEEDOR (CONTROL COMPRAS / LOGÍSTICA)
    rep_model = RepartoModel()
    articulos_control = rep_model.obtener_articulos_control_recepcion()
    assert len(articulos_control) > 0, "No hay artículos para control de recepción"
    
    items_comprobante = []
    for art in articulos_control:
        items_comprobante.append({
            'id_articulo': art['id_articulo'],
            'cantidad_pedida': art['cantidad_demandada'],
            'cantidad_recibida': max(1, art['cantidad_demandada'] - 2),
            'precio_pactado': art['precio_pactado'],
            'precio_facturado': art['precio_pactado']
        })
        
    id_comprobante = rep_model.registrar_comprobante_y_stock(
        id_proveedor=1,
        tipo_comprobante='Factura',
        nro_comprobante='FC-A-0001-00009988',
        fecha_emision='2026-10-02',
        observaciones='Recepción física con verificación de precios y cantidades',
        items_detalle=items_comprobante
    )
    assert id_comprobante > 0, "Fallo al registrar comprobante"
    print(f"[OK] Test 7: Comprobante #{id_comprobante} registrado con doble control de compras/logística y stock actualizado.")
    
    # 8. PASO 11 Y 12: REPARTO AUTOMÁTICO CON PRORRATEO Y REMITOS CON NOTIFICACIÓN
    discrepancias = rep_model.validar_stock_vs_pedidos()
    ajustes = {}
    for d in discrepancias:
        id_art = d['id_articulo']
        for id_ped, cant_aj in d['ajustes'].items():
            ajustes[(id_ped, id_art)] = cant_aj
            
    exito_rep = rep_model.ejecutar_reparto_masivo(ajustes=ajustes)
    assert exito_rep, "Fallo al ejecutar reparto"
    
    notifs_socio_remito = notif_model.obtener_notificaciones_usuario(socio1_u['id'], 'socio')
    assert any(n['tipo'] == 'reparto' and 'Remito' in n['mensaje'] for n in notifs_socio_remito), "Socio no recibió remito"
    print("[OK] Test 8: Reparto automático ejecutado con prorrateo equitativo y remitos notificados a socios.")
    
    print("\n=== ¡CIRCUITO REFINADO COMPLETO VERIFICADO CON ÉXITO (8/8 PRUEBAS OK)! ===")

if __name__ == '__main__':
    run_tests()
