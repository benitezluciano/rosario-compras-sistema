# Presentación del proyecto

Material de la presentación grupal (4 integrantes, máximo 10 minutos, enfoque de negocio ante la gerencia). El criterio de armado está en la DEC-025 de [`gestion/DECISIONES.md`](../gestion/DECISIONES.md).

## Contenido

| Archivo | Qué es |
| :--- | :--- |
| `circuito_as_is_to_be.html` | Página autónoma (se abre en el navegador): AS-IS y TO-BE lado a lado, los 4 problemas del relevamiento, tabla eliminar / modificar / mantener y esqueleto del bloque de valor. |
| `diagramas/as-is.svg` · `as-is.png` | Circuito actual en 5 carriles y 9 filas. El PNG mide 1770 × 2292 px (fondo blanco). |
| `diagramas/to-be.svg` · `to-be.png` | Circuito con el módulo, en los mismos carriles y filas. |
| `contenido_diapositivas.md` | Texto para pegar en Gamma (10 diapositivas), notas del orador con tiempos y reparto, preguntas probables y puntos a confirmar. |
| `guion_video.md` | Guion del video del prototipo (7 escenas, unos 2:35) con datos, clics y narración. |
| `fuente/` | Lo necesario para regenerar todo (ver más abajo). |

El AS-IS sale del relevamiento (documentos 02 a 05 de [`documentacion/`](../documentacion)). El TO-BE sale del flujo vigente del prototipo (DEC-004 a DEC-024), no del README ni del manual, que están desactualizados.

## Regenerar

Para cambiar un diagrama se editan los diccionarios `as_boxes`, `as_edges`, `to_boxes` y `to_edges` de `fuente/generar.py`, y para cambiar los textos de la página, `fuente/page_body.html`.

```powershell
python presentacion/fuente/generar.py
```

Genera la página y los dos SVG. Los PNG se exportan con Edge (hay que correrlo desde la raíz del proyecto):

```powershell
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
foreach ($n in "as-is","to-be") {
  & $edge --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=3 `
    --window-size=590,764 --screenshot="$PWD\presentacion\diagramas\$n.png" "$PWD\presentacion\diagramas\$n.svg"
}
```

## Pendiente

- Fecha de la presentación: **27/11/2026**. Las diapositivas las arma Sergio en Gamma a partir de `contenido_diapositivas.md` (DEC-026).
- No se calcularon duraciones ni costos de implementación: las diapositivas no los incluyen (DEC-027). La portada la completa Sergio.
- Las cifras de 4 horas por pedido, más de 500 hojas por mes y 30 horas por semana son **estimaciones de la organización**, no medidas por el grupo. Así hay que rotularlas.
- Grabar el video y ensayar el recorrido con la base reseteada.
