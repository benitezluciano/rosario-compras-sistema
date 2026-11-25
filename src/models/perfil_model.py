import re
from src.database import Database

CONDICIONES_IVA = [
    "Responsable Inscripto",
    "Monotributista",
    "Exento",
    "Consumidor Final",
]


def validar_cuit_dni(valor):
    """
    Valida un CUIT (11 dígitos, opcionalmente con guiones XX-XXXXXXXX-X)
    o un DNI (7 u 8 dígitos, opcionalmente con puntos).
    Retorna (True, valor_normalizado) o (False, mensaje_error).
    """
    texto = (valor or "").strip()
    if not texto:
        return False, "El CUIT o DNI es obligatorio."

    solo_digitos = re.sub(r"[-.\s]", "", texto)
    if not solo_digitos.isdigit():
        return False, "El CUIT/DNI solo puede contener dígitos, guiones o puntos."

    if len(solo_digitos) == 11:
        if "-" in texto and not re.fullmatch(r"\d{2}-\d{8}-\d", texto):
            return False, "El formato de CUIT debe ser XX-XXXXXXXX-X."
        normalizado = f"{solo_digitos[:2]}-{solo_digitos[2:10]}-{solo_digitos[10]}"
        return True, normalizado

    if len(solo_digitos) in (7, 8):
        return True, solo_digitos

    return False, "Ingresá un CUIT válido (11 dígitos: XX-XXXXXXXX-X) o un DNI válido (7 u 8 dígitos)."


class PerfilSocioModel:
    """Consulta y actualización de datos fiscales y domicilio del socio."""

    def obtener_perfil(self, id_user):
        with Database() as conn:
            row = conn.execute(
                """
                SELECT id, nombre, email, cuit_dni, condicion_iva, domicilio
                FROM USERS
                WHERE id = ?
                """,
                (id_user,),
            ).fetchone()
            return dict(row) if row else None

    def actualizar_datos_fiscales(self, id_user, nombre, cuit_dni, condicion_iva, domicilio):
        """
        Valida y guarda los datos fiscales y de entrega del socio en USERS.
        Retorna (True, perfil_actualizado) o (False, mensaje_error).
        """
        nombre_limpio = (nombre or "").strip()
        if not nombre_limpio:
            return False, "El nombre o razón social es obligatorio."

        ok_doc, doc_o_err = validar_cuit_dni(cuit_dni)
        if not ok_doc:
            return False, doc_o_err

        iva_limpio = (condicion_iva or "").strip()
        if iva_limpio not in CONDICIONES_IVA:
            return False, "Seleccioná una condición frente al IVA válida."

        domicilio_limpio = (domicilio or "").strip()
        if not domicilio_limpio:
            return False, "El domicilio de entrega es obligatorio."

        with Database() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE USERS
                SET nombre = ?, cuit_dni = ?, condicion_iva = ?, domicilio = ?
                WHERE id = ?
                """,
                (nombre_limpio, doc_o_err, iva_limpio, domicilio_limpio, id_user),
            )
            if cursor.rowcount == 0:
                return False, "No se encontró el usuario para actualizar."

        return True, self.obtener_perfil(id_user)
