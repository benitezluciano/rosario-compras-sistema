import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.database import inicializar_db
from src.models.proveedor_model import ProveedorModel
from src.models.catalogo_model import CatalogoModel
from src.services.email_service import EmailService

def run_tests():
    print("Iniciando pruebas de Proveedores, Catálogo y EmailService...")
    inicializar_db()
    
    # 1. Test ProveedorModel
    modelo_prov = ProveedorModel()
    proveedores = modelo_prov.obtener_todos()
    print(f"OK: Se obtuvieron {len(proveedores)} proveedores.")
    assert len(proveedores) >= 3, "Debería haber al menos 3 proveedores."
    
    # Verificar campos email y telefono
    for p in proveedores:
        assert "email" in p and "telefono" in p, f"Proveedor {p['nombre']} no tiene campos email/telefono."
        print(f"  - {p['nombre']}: Email={p.get('email')}, Tel={p.get('telefono')}, Resp={p.get('ejecutivo_nombre')}")
        
    # Crear un proveedor de prueba
    exito, id_nuevo = modelo_prov.crear_proveedor(
        nombre="Proveedor Test Unitario",
        email="test@proveedortest.com",
        telefono="341-999999",
        direccion="Calle Falsa 123",
        id_user=2
    )
    assert exito, "Error al crear proveedor."
    print(f"OK: Proveedor creado con ID={id_nuevo}.")
    
    # Editar
    exito, msg = modelo_prov.actualizar_proveedor(
        id_proveedor=id_nuevo,
        nombre="Proveedor Test Editado",
        email="editado@proveedortest.com",
        telefono="341-888888",
        direccion="Calle Modificada 456",
        id_user=2
    )
    assert exito, f"Error al editar: {msg}"
    print("OK: Proveedor editado con éxito.")
    
    # Eliminar
    exito, msg = modelo_prov.eliminar_proveedor(id_nuevo)
    assert exito, f"Error al eliminar: {msg}"
    print("OK: Proveedor eliminado con éxito.")
    
    # 2. Test Importación de las 3 planillas de ejemplo
    modelo_cat = CatalogoModel()
    
    # Planilla 1: Alimentos
    p1 = os.path.join(BASE_DIR, "ejemplos_listas_precios", "1_distribuidora_central_alimentos.xlsx")
    headers, filas, err = modelo_cat.leer_vista_previa(p1)
    assert err is None, f"Error leyendo vista previa {p1}: {err}"
    print(f"OK: Vista previa de {os.path.basename(p1)}: {len(headers)} cols, {len(filas)} filas.")
    
    exito, msg = modelo_cat.importar_lista_proveedor(1, p1)
    assert exito, f"Error importando {p1}: {msg}"
    print(f"OK: {os.path.basename(p1)} importado exitosamente.")
    
    # Planilla 2: Lácteos
    p2 = os.path.join(BASE_DIR, "ejemplos_listas_precios", "2_lacteos_del_litoral.xlsx")
    exito, msg = modelo_cat.importar_lista_proveedor(2, p2)
    assert exito, f"Error importando {p2}: {msg}"
    print(f"OK: {os.path.basename(p2)} importado exitosamente.")
    
    # Planilla 3: Insumos
    p3 = os.path.join(BASE_DIR, "ejemplos_listas_precios", "3_insumos_gastronomicos_sur.csv")
    exito, msg = modelo_cat.importar_lista_proveedor(3, p3)
    assert exito, f"Error importando {p3}: {msg}"
    print(f"OK: {os.path.basename(p3)} importado exitosamente.")
    
    # 3. Test EmailService (Modo Simulación)
    email_service = EmailService.get_instance()
    html_solicitud = email_service.generar_plantilla_solicitud_lista(
        nombre_proveedor="Distribuidora Central",
        nombre_ejecutivo="Luciano Benítez",
        email_ejecutivo="ejecutivo@rosariocompras.com"
    )
    assert "Rosario Compras" in html_solicitud
    
    exito_email = None
    msg_email = None
    def cb(e, m):
        nonlocal exito_email, msg_email
        exito_email = e
        msg_email = m
        
    email_service._enviar_correo_sync(
        destinatario="ventas@distribuidoracentral.com",
        asunto="Solicitud de Lista de Precios - Test",
        cuerpo_html=html_solicitud,
        callback=cb
    )
    assert exito_email is True, f"Error en envío simulado: {msg_email}"
    print(f"OK: EmailService funcionó correctamente: {msg_email}")

    print("\n=======================================================")
    print("  TODAS LAS PRUEBAS DE INTEGRACION PASARON CON EXITO!  ")
    print("=======================================================")

if __name__ == "__main__":
    run_tests()
