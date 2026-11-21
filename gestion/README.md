# Gestión del proyecto

Esta carpeta guarda la memoria del proyecto fuera de los chats:

| Archivo | Qué contiene | Cuándo se actualiza |
| :--- | :--- | :--- |
| [ESTADO.md](ESTADO.md) | Foto corta de "dónde estamos hoy" | Se **reescribe** en cada sesión |
| [DECISIONES.md](DECISIONES.md) | Qué se decidió y por qué (DEC-001, DEC-002...) | En el **momento** en que se decide |
| [BITACORA.md](BITACORA.md) | Qué se hizo en cada sesión (lo nuevo arriba) | Al **cerrar** cada sesión |

**Al empezar una sesión:** leer `ESTADO.md`. **Al cerrarla:** agregar la entrada en `BITACORA.md`, registrar las decisiones en `DECISIONES.md` y reescribir `ESTADO.md`.

---

# Registro de decisiones

> **Para qué sirve:** guardar *qué* se decidió y *por qué*, para no volver a discutirlo ni perderlo si se cierra un chat o pasan semanas.
>
> **Reglas:**
> 1. Una entrada por decisión, con ID correlativo (DEC-001, DEC-002...).
> 2. Se registra **en el momento** en que se decide, no al final de la semana.
> 3. **Nunca se borra** una decisión. Si cambia, se marca como `Reemplazada` y se enlaza la nueva.
> 4. Estados posibles: `Propuesta` (en discusión) · `Cerrada` (vigente) · `Reemplazada` (ya no vale).
> 5. Si una decisión no tiene "alternativas consideradas", probablemente no se pensó lo suficiente.

---

# Estado actual del proyecto

> **Para qué sirve:** una foto corta de "dónde estamos hoy". Es lo primero que se lee al empezar una sesión y lo que se le pide a Copilot que lea antes de trabajar.
>
> **Reglas:**
> 1. Se **reescribe** en cada sesión (no es un historial: el historial va en `BITACORA.md`).
> 2. Tiene que entrar en una pantalla. Si crece, se resume o los detalles pasan a Issues.
> 3. Cada ítem pendiente debería apuntar a un Issue o a una decisión cuando exista.
> 4. Si algo lleva mucho tiempo en "Bloqueado", es una señal para actuar, no para dejarlo ahí.

---

# Bitácora de sesiones

> **Para qué sirve:** registro cronológico de qué se hizo en cada sesión de trabajo. Es la memoria de largo plazo que reemplaza al historial de chat.
>
> **Reglas:**
> 1. Una entrada por sesión de trabajo (no hace falta que sea diaria; sí que sea cada vez que trabajás).
> 2. Las entradas **nuevas van arriba**, así lo último se ve primero.
> 3. Se escribe al **cerrar** la sesión (10 minutos). Podés pedirle a Copilot que arme el borrador a partir de lo que se hizo, pero revisalo vos.
> 4. Las entradas viejas **no se editan**: si algo cambió, se aclara en la entrada nueva.
> 5. Lo que se decidió va a `DECISIONES.md` y se enlaza acá; no se duplica el detalle.
