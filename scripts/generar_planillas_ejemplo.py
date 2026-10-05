import os
import pandas as pd

def generar_planillas():
    carpeta_destino = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ejemplos_listas_precios")
    os.makedirs(carpeta_destino, exist_ok=True)
    print(f"Generando planillas de prueba en: {carpeta_destino}")

    # 1. Distribuidora Central (Alimentos y Cafetería) - Formato .xlsx
    datos_alimentos = {
        "codigo": [
            "CAF-001", "CAF-002", "CAF-003", "CAF-004", 
            "ALM-001", "ALM-002", "ALM-003", "ALM-004", 
            "ALM-005", "ALM-006", "ALM-007", "ALM-008", 
            "ALM-009", "ALM-010", "ALM-011"
        ],
        "detalle": [
            "Café en Grano Tostado Especial x 1kg",
            "Endulzante en Sobres x 800u",
            "Té Variedades en Saquitos x 100u",
            "Cacao en Polvo Amargo x 1kg",
            "Aceite de Girasol Alto Oleico x 5L",
            "Azúcar Blanco Superior Tipo A x 10kg",
            "Harina de Trigo 0000 Pastelera x 25kg",
            "Harina de Trigo 000 x 25kg",
            "Arroz Largo Fino 00000 x 5kg",
            "Fideos Secos Cinta x 5kg",
            "Sal Fina Refinada en Paquete x 1kg",
            "Tomate Triturado en Botella x 1kg",
            "Mostaza Clásica en Bidón x 3kg",
            "Mayonesa Gastronómica en Balde x 3kg",
            "Kétchup Tradicional en Bidón x 3kg"
        ],
        "rubro": [
            "Cafetería", "Cafetería", "Cafetería", "Cafetería",
            "Almacén", "Almacén", "Insumos", "Insumos",
            "Almacén", "Almacén", "Almacén", "Almacén",
            "Condimentos", "Condimentos", "Condimentos"
        ],
        "precio": [
            13500.0, 4800.0, 3200.0, 6500.0,
            9800.0, 11200.0, 19500.0, 16800.0,
            7400.0, 6200.0, 950.0, 1850.0,
            5100.0, 7900.0, 6800.0
        ],
        "descuento": [
            "5%", "10%", "0%", "5%",
            "0%", "8%", "10%", "5%",
            "0%", "0%", "0%", "5%",
            "0%", "5%", "0%"
        ]
    }
    df_alimentos = pd.DataFrame(datos_alimentos)
    ruta_alimentos = os.path.join(carpeta_destino, "1_distribuidora_central_alimentos.xlsx")
    df_alimentos.to_excel(ruta_alimentos, index=False)
    print(f"OK: Creado {os.path.basename(ruta_alimentos)} ({len(df_alimentos)} articulos)")

    # 2. Lácteos del Litoral (Lácteos y Quesos) - Formato .xlsx con nombres de columna alternativos
    datos_lacteos = {
        "cod_articulo": [
            "LAC-101", "LAC-102", "LAC-103", "LAC-104",
            "LAC-105", "LAC-106", "LAC-107", "LAC-108",
            "LAC-109", "LAC-110", "LAC-111", "LAC-112"
        ],
        "descripcion": [
            "Leche Entera Homogeneizada Ultra x 1L",
            "Leche Descremada 0% Grasa x 1L",
            "Crema de Leche Premium 38% Tenor x 1L",
            "Queso Mozzarella en Barra Cilindro x 4kg",
            "Queso Cremoso Primera Marca x 4kg",
            "Queso Tybo en Barra para Feteado x 3.5kg",
            "Queso Rallado Parmesano Estacionado x 1kg",
            "Manteca Calidad Extra Gastronómica x 500g",
            "Dulce de Leche Repostero Pastelero x 5kg",
            "Dulce de Leche Familiar Clásico x 5kg",
            "Yogur Natural Entero para Desayunos x 5L",
            "Ricotta Entera Fresca en Horma x 2kg"
        ],
        "categoria": [
            "Lácteos", "Lácteos", "Lácteos", "Quesos",
            "Quesos", "Quesos", "Quesos", "Lácteos",
            "Dulces", "Dulces", "Lácteos", "Lácteos"
        ],
        "precio_final": [
            1250.0, 1250.0, 4600.0, 24800.0,
            21500.0, 26200.0, 14500.0, 4100.0,
            18900.0, 16500.0, 8200.0, 7800.0
        ],
        "bonificacion": [
            "0%", "0%", "5%", "8%",
            "5%", "0%", "10%", "0%",
            "12%", "10%", "0%", "5%"
        ]
    }
    df_lacteos = pd.DataFrame(datos_lacteos)
    ruta_lacteos = os.path.join(carpeta_destino, "2_lacteos_del_litoral.xlsx")
    df_lacteos.to_excel(ruta_lacteos, index=False)
    print(f"OK: Creado {os.path.basename(ruta_lacteos)} ({len(df_lacteos)} articulos)")

    # 3. Insumos Gastronómicos del Sur (Descartables y Limpieza) - Formato .csv
    datos_insumos = {
        "referencia": [
            "INS-201", "INS-202", "INS-203", "INS-204",
            "INS-205", "INS-206", "INS-207", "INS-208",
            "INS-209", "INS-210"
        ],
        "articulo": [
            "Servilletas de Papel Interdobladas x 2000u",
            "Vasos Térmicos Polipapel 240cc x 500u",
            "Tapas Plásticas para Vasos Térmicos x 500u",
            "Bolsas Camiseta Kraft Biodegradables x 1000u",
            "Film Adherente de PVC 38cm x 300m",
            "Papel Aluminio Extra Grueso 45cm x 100m",
            "Detergente Desengrasante Concentrado x 5L",
            "Lavandina Concentrada Desinfectante x 5L",
            "Jabón Líquido Antibacterial para Manos x 5L",
            "Rollos de Papel Higiénico Institucional x 8u"
        ],
        "tipo": [
            "Descartables", "Descartables", "Descartables", "Packaging",
            "Insumos Cocina", "Insumos Cocina", "Limpieza", "Limpieza",
            "Higiene", "Higiene"
        ],
        "importe": [
            8500.0, 12400.0, 5900.0, 15800.0,
            11200.0, 14900.0, 6700.0, 4200.0,
            5600.0, 9100.0
        ],
        "desc": [
            "5%", "0%", "0%", "10%",
            "5%", "0%", "8%", "0%",
            "0%", "5%"
        ]
    }
    df_insumos = pd.DataFrame(datos_insumos)
    ruta_insumos = os.path.join(carpeta_destino, "3_insumos_gastronomicos_sur.csv")
    df_insumos.to_csv(ruta_insumos, index=False, sep=";", encoding="utf-8-sig")
    print(f"OK: Creado {os.path.basename(ruta_insumos)} ({len(df_insumos)} articulos)")

if __name__ == "__main__":
    generar_planillas()
