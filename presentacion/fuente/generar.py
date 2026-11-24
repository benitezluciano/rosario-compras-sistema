"""Genera la pagina del circuito AS-IS / TO-BE y los dos diagramas sueltos.

Uso (desde cualquier carpeta):
    python presentacion/fuente/generar.py

Salidas (en presentacion/):
    circuito_as_is_to_be.html     pagina autonoma
    diagramas/as-is.svg           diagrama AS-IS (colores incrustados)
    diagramas/to-be.svg           diagrama TO-BE (colores incrustados)

Los PNG se exportan aparte con un navegador (ver presentacion/README.md).
Para cambiar un diagrama se editan los diccionarios *_boxes y *_edges de abajo.
"""
import html
import os
import textwrap

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.dirname(AQUI)

LANES = ["Socios", "Ejecutivo", "Logística", "Administración", "Proveedor"]
LW, HEAD, RH, BW, BH = 118, 34, 80, 98, 50
NROWS = 9
W = LW * len(LANES)
H = HEAD + NROWS * RH + 6


def cx(l): return l * LW + LW / 2
def top(r): return HEAD + r * RH + (RH - BH) / 2
def bot(r): return top(r) + BH
def mid(r): return top(r) + BH / 2


def lines(text):
    out = textwrap.wrap(text, width=15)
    assert len(out) <= 3, (text, out)
    assert all(len(x) <= 15 for x in out), (text, out)
    return out


def svg(prefix, boxes, edges, label, badge_cls, standalone=False):
    p = []
    if standalone:
        p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(label)}">')
        p.append(f'<style>{SVG_CSS}</style>')
        p.append(f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>')
    else:
        p.append(f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{html.escape(label)}">')
    p.append(f'<defs><marker id="{prefix}-arr" viewBox="0 0 8 8" refX="7.5" refY="4" markerWidth="8" markerHeight="8" markerUnits="userSpaceOnUse" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="currentColor"/></marker></defs>')
    for i, name in enumerate(LANES):
        p.append(f'<rect class="lane l{i % 2}" x="{i*LW}" y="0" width="{LW}" height="{H}"/>')
        p.append(f'<rect class="lanehead" x="{i*LW}" y="0" width="{LW}" height="{HEAD-6}"/>')
        p.append(f'<text class="lanename" x="{cx(i)}" y="{(HEAD-6)/2+4}" text-anchor="middle">{name}</text>')
    for e in edges:
        a, b = boxes[e["from"]], boxes[e["to"]]
        cls = "edge new" if e.get("new") else "edge"
        mk = f'marker-end="url(#{prefix}-arr)"'
        lbl = e.get("label")
        if a["r"] == b["r"]:
            y = mid(a["r"])
            sgn = 1 if b["l"] > a["l"] else -1
            x1, x2 = cx(a["l"]) + sgn * BW / 2, cx(b["l"]) - sgn * BW / 2
            p.append(f'<path class="{cls}" d="M{x1},{y} H{x2}" {mk}/>')
            if lbl:
                p.append(f'<text class="elabel" x="{(x1+x2)/2}" y="{y-5}" text-anchor="middle">{lbl}</text>')
        elif e.get("side"):
            y = mid(a["r"])
            sgn = 1 if b["l"] > a["l"] else -1
            x1 = cx(a["l"]) + sgn * BW / 2
            tx = cx(b["l"]) + e.get("dx", 0)  # dx separa esta flecha de otra que llega a la misma caja
            p.append(f'<path class="{cls}" d="M{x1},{y} H{tx} V{top(b["r"])}" {mk}/>')
            if lbl:
                p.append(f'<text class="elabel" x="{(x1+tx)/2}" y="{y-5}" text-anchor="middle">{lbl}</text>')
        elif a["l"] == b["l"]:
            x = cx(a["l"])
            p.append(f'<path class="{cls}" d="M{x},{bot(a["r"])} V{top(b["r"])}" {mk}/>')
            if lbl:
                p.append(f'<text class="elabel" x="{x+6}" y="{(bot(a["r"])+top(b["r"]))/2+4}">{lbl}</text>')
        else:
            ym = bot(a["r"]) + (RH - BH) / 2
            p.append(f'<path class="{cls}" d="M{cx(a["l"])},{bot(a["r"])} V{ym} H{cx(b["l"])} V{top(b["r"])}" {mk}/>')
            if lbl:
                lx = cx(a["l"]) + (cx(b["l"]) - cx(a["l"])) * e.get("lpos", 0.5)  # lpos: posicion de la etiqueta en el tramo
                p.append(f'<text class="elabel" x="{lx}" y="{ym-5}" text-anchor="middle">{lbl}</text>')
    for k, b in boxes.items():
        x, y = cx(b["l"]) - BW / 2, top(b["r"])
        p.append(f'<rect class="box {b["kind"]}" x="{x}" y="{y}" width="{BW}" height="{BH}" rx="4"/>')
        ls = lines(b["t"])
        y0 = y + BH / 2 - (len(ls) - 1) * 6.5 + 4
        for i, ln in enumerate(ls):
            p.append(f'<text class="btxt" x="{cx(b["l"])}" y="{y0 + i*13}" text-anchor="middle">{html.escape(ln)}</text>')
        for j, n in enumerate(b.get("badges", [])):
            bx, by = x + BW - 4 - j * 20, y
            p.append(f'<circle class="{badge_cls}" cx="{bx}" cy="{by}" r="9"/>')
            p.append(f'<text class="badgetxt" x="{bx}" y="{by+3.8}" text-anchor="middle">{n}</text>')
    p.append("</svg>")
    return "\n".join(p)


# Estilos con colores literales (tema claro) para los SVG sueltos.
SVG_CSS = """
svg{color:#5B6874;font-family:Inter,'Segoe UI',Arial,sans-serif}
.lane.l0{fill:#ECF0F3}.lane.l1{fill:#F6F8F9}.lanehead{fill:#DDE3E8}
.lanename{fill:#17222D;font:600 11.5px Inter,'Segoe UI',Arial,sans-serif}
.box{stroke-width:1.5}
.box.keep{fill:#FFFFFF;stroke:#5B6874}
.box.ext{fill:#FFFFFF;stroke:#5B6874;stroke-dasharray:4 3}
.box.pain{fill:#FBE9E1;stroke:#B4421A}
.box.auto{fill:#DDF2EE;stroke:#0B6E66}
.btxt{fill:#17222D;font:500 11px Inter,'Segoe UI',Arial,sans-serif}
.edge{fill:none;stroke:#5B6874;stroke-width:1.3}
.edge.new{stroke:#0B6E66;color:#0B6E66;stroke-dasharray:5 3;stroke-width:1.6}
.elabel{fill:#5B6874;font:400 10.5px Inter,'Segoe UI',Arial,sans-serif;paint-order:stroke;stroke:#F6F8F9;stroke-width:3px;stroke-linejoin:round}
.badge-pain{fill:#B4421A}.badge-auto{fill:#0B6E66}
.badgetxt{fill:#FFFFFF;font:700 10.5px Inter,'Segoe UI',Arial,sans-serif}
"""

as_boxes = {
    "a1": dict(r=0, l=1, t="Sube listas negociadas", kind="keep"),
    "a2": dict(r=1, l=0, t="Pedido en Excel por mail", kind="pain", badges=[4, 2]),
    "a3": dict(r=2, l=1, t="Imprime y tipea 12 planillas", kind="pain", badges=[4, 2]),
    "a4": dict(r=3, l=1, t="Envía planilla al proveedor", kind="keep"),
    "a4p": dict(r=3, l=4, t="Prepara y entrega", kind="ext"),
    "a5": dict(r=4, l=2, t="Recibe y controla con remito", kind="keep"),
    "a5e": dict(r=4, l=1, t="Controla precios y cantidades", kind="keep"),
    "a6": dict(r=5, l=3, t="Carga factura y orden de pago", kind="keep"),
    "a7": dict(r=6, l=1, t="Reparte artículo por artículo", kind="pain", badges=[1]),
    "a8": dict(r=7, l=2, t="Remitos tardíos y picking", kind="pain", badges=[3]),
    "a9": dict(r=8, l=0, t="Retira con su transporte", kind="keep"),
}
as_edges = [
    dict(**{"from": "a1", "to": "a2"}, label="lista"),
    dict(**{"from": "a2", "to": "a3"}, label="mail"),
    dict(**{"from": "a3", "to": "a4"}),
    dict(**{"from": "a4", "to": "a4p"}, label="planilla consolidada"),
    dict(**{"from": "a4p", "to": "a5"}, label="camión"),
    dict(**{"from": "a5", "to": "a5e"}),
    dict(**{"from": "a5e", "to": "a6"}, label="factura", lpos=0.8),
    dict(**{"from": "a6", "to": "a7"}),
    dict(**{"from": "a7", "to": "a8"}),
    dict(**{"from": "a8", "to": "a9"}),
]

to_boxes = {
    "b1": dict(r=0, l=1, t="Importa y habilita la lista", kind="auto"),
    "b2": dict(r=1, l=0, t="Carga su pedido en el sistema", kind="auto", badges=[4, 2]),
    "b3": dict(r=2, l=1, t="Matriz automática y ajustes", kind="auto", badges=[4, 2]),
    "b4": dict(r=3, l=1, t="Consolida y genera orden de compra", kind="auto"),
    "b4p": dict(r=3, l=4, t="Recibe la orden por mail", kind="ext"),
    "b5": dict(r=4, l=2, t="Recibe y controla con remito", kind="keep"),
    "b5e": dict(r=4, l=1, t="Registra recepción, doble control", kind="auto"),
    "b6": dict(r=5, l=3, t="Carga factura y orden de pago", kind="keep"),
    "b7": dict(r=6, l=1, t="Reparto automático con prorrateo", kind="auto", badges=[1]),
    "b8": dict(r=7, l=2, t="Remito PDF al instante y picking", kind="auto", badges=[3]),
    "b9": dict(r=8, l=0, t="Ve su pedido y retira", kind="auto"),
}
to_edges = [
    dict(**{"from": "b1", "to": "b2"}, label="aviso"),
    dict(**{"from": "b2", "to": "b3"}, label="aviso"),
    dict(**{"from": "b3", "to": "b4"}),
    dict(**{"from": "b4", "to": "b4p"}, label="orden .xlsx"),
    dict(**{"from": "b4p", "to": "b5"}, label="camión"),
    dict(**{"from": "b5", "to": "b5e"}),
    dict(**{"from": "b5e", "to": "b6"}, label="factura", lpos=0.8),
    dict(**{"from": "b6", "to": "b7"}),
    dict(**{"from": "b7", "to": "b8"}),
    dict(**{"from": "b8", "to": "b9"}),
    dict(**{"from": "b7", "to": "b9"}, label="aviso", new=True, side=True, dx=-16),
]

LABEL_AS = ("Circuito actual en cinco carriles: los pedidos llegan por mail en Excel, el ejecutivo los tipea en una "
            "planilla y reparte artículo por artículo; cuatro problemas marcados.")
LABEL_TO = ("Circuito propuesto en los mismos cinco carriles: el socio carga el pedido en el sistema, la consolidación, "
            "la orden de compra, el reparto y el remito se generan automáticamente.")


def escribir(ruta, texto):
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)


def main():
    css = open(os.path.join(AQUI, "page.css"), encoding="utf-8").read()
    body = open(os.path.join(AQUI, "page_body.html"), encoding="utf-8").read()
    body = body.replace("{{SVG_AS}}", svg("as", as_boxes, as_edges, LABEL_AS, "badge-pain"))
    body = body.replace("{{SVG_TO}}", svg("to", to_boxes, to_edges, LABEL_TO, "badge-auto"))
    pagina = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Circuito Rosario Compras</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap">
<style>
:root {{ color-scheme: light; }}
body {{ margin: 0; }}
{css}
</style>
</head>
<body>
{body}
</body>
</html>
"""
    escribir(os.path.join(SALIDA, "circuito_as_is_to_be.html"), pagina)
    os.makedirs(os.path.join(SALIDA, "diagramas"), exist_ok=True)
    escribir(os.path.join(SALIDA, "diagramas", "as-is.svg"), svg("as", as_boxes, as_edges, LABEL_AS, "badge-pain", True))
    escribir(os.path.join(SALIDA, "diagramas", "to-be.svg"), svg("to", to_boxes, to_edges, LABEL_TO, "badge-auto", True))
    print("ok: pagina y dos SVG generados en", SALIDA)


if __name__ == "__main__":
    main()
