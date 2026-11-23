import sqlite3
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database.db"
REMITOS_DIR = BASE_DIR / "remitos_pdf"
ORDENES_DIR = BASE_DIR / "ordenes_compra"


TABLES_OPERATIVAS = (
    "DETALLE_REMITOS",
    "REMITOS",
    "PROCESOS_REPARTO",
    "DETALLE_COMPROBANTES_PROVEEDOR",
    "COMPROBANTES_PROVEEDOR",
    "NOTIFICACIONES",
    "DETALLE_PEDIDOS",
    "PEDIDOS",
    "ORDENES_COMPRA",  # después de PEDIDOS, que la referencia
)


def contar_si_existe(conn, tabla):
    """Cuenta registros; devuelve None si la tabla todavía no existe (base sin migrar)."""
    existe = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (tabla,)
    ).fetchone()
    return contar(conn, tabla) if existe else None


def contar(conn, tabla):
    return conn.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]


def limpiar():
    if not DB_PATH.exists():
        print(f"No existe la base de datos: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        con_registros = {tabla: contar_si_existe(conn, tabla) for tabla in TABLES_OPERATIVAS}

        with conn:
            for tabla in TABLES_OPERATIVAS:
                if con_registros[tabla] is not None:
                    conn.execute(f"DELETE FROM {tabla}")

            marcadores = ",".join("?" for _ in TABLES_OPERATIVAS)
            conn.execute(
                f"DELETE FROM sqlite_sequence WHERE name IN ({marcadores})",
                TABLES_OPERATIVAS,
            )

        pdfs_eliminados = 0
        if REMITOS_DIR.exists():
            for ruta_pdf in REMITOS_DIR.glob("*.pdf"):
                ruta_pdf.unlink()
                pdfs_eliminados += 1

        ordenes_eliminadas = 0
        if ORDENES_DIR.exists():
            for ruta_orden in ORDENES_DIR.glob("*.xlsx"):
                ruta_orden.unlink()
                ordenes_eliminadas += 1

        print("Limpiados los datos operativos:")
        for tabla in TABLES_OPERATIVAS:
            cantidad = con_registros[tabla]
            print(f"  - {tabla}: {'(la tabla no existe)' if cantidad is None else f'{cantidad} registro(s)'}")
        print(f"  - PDFs de remitos: {pdfs_eliminados} archivo(s)")
        print(f"  - Órdenes de compra (.xlsx): {ordenes_eliminadas} archivo(s)")

        conservados = (
            "USERS",
            "PROVEEDORES",
            "ARTICULOS",
            "PRECIOS_NEGOCIADOS",
        )
        print("Datos conservados:")
        for tabla in conservados:
            print(f"  - {tabla}: {contar(conn, tabla)} registro(s)")

        return 0
    except Exception as exc:
        conn.rollback()
        print(f"No se pudo limpiar la base de datos: {exc}", file=sys.stderr)
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(limpiar())
