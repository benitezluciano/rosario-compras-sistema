# rosario-compras-sistema
Repositorioa creado para almacenar todos los datos correspondientes a este proyecto de la empresa Rosario Compras
## Diagrama de Entidad-Relación 
'''mermaid
erDiagram
    PROVEEDORES ||--o{ LISTAS_PRECIOS : "emite"
    LISTAS_PRECIOS ||--|{ ARTICULOS : "contiene"
    SOCIOS ||--o{ PEDIDOS : "realiza"
    PEDIDOS ||--|{ DETALLE_PEDIDOS : "tiene"
    ARTICULOS ||--o{ DETALLE_PEDIDOS : "incluido_en"
    PROCESOS_REPARTO ||--o{ REMITOS : "genera"
    SOCIOS ||--o{ REMITOS : "recibe"
    REMITOS ||--|{ DETALLE_REMITOS : "tiene"
    ARTICULOS ||--o{ DETALLE_REMITOS : "despachado_en"

    PROVEEDORES {
        int id_proveedor PK
        string nombre
        string direccion
    }

    LISTAS_PRECIOS {
        int id_lista PK
        int id_proveedor FK
        date fecha_carga
        string nombre_archivo_source
    }

    ARTICULOS {
        int id_articulo PK "Autoincremental Interno"
        int id_lista FK
        string id_articulo_proveedor "Código de planilla Excel"
        string detalle
        string rubro
        decimal precio_final
        int cantidad_stock
    }

    SOCIOS {
        int id_socio PK
        string nombre
        string email
    }

    PEDIDOS {
        int id_pedido PK
        int id_socio FK
        date fecha
        string estado
    }

    DETALLE_PEDIDOS {
        int id_pedido PK, FK
        int id_articulo PK, FK
        int cantidad_pedida
    }

    PROCESOS_REPARTO {
        int id_proceso PK
        datetime fecha_proceso
        string archivo_consolidado
        string estado_reparto
    }

    REMITOS {
        int id_remito PK
        int id_socio FK
        int id_proceso FK
        date fecha_emision
        string detalle_entrega
    }

    DETALLE_REMITOS {
        int id_remito PK, FK
        int id_articulo PK, FK
        int cantidad_entregada
    }
