"""Generate the eight report figures from a small, deterministic SVG vocabulary.

Run with the bundled Python runtime. SVG files are the editable sources; PNG
copies are rasterized separately for Word insertion.
"""

from __future__ import annotations

from html import escape
from pathlib import Path


OUT = Path(__file__).resolve().parent
INK = "#183047"
BLUE = "#214E72"
LINE = "#62809A"
LIGHT = "#EAF2F8"
MINT = "#EDF7F4"
SAND = "#FFF3E6"
WHITE = "#FFFFFF"


class Diagram:
    def __init__(self, width: int, height: int, title: str, subtitle: str = ""):
        self.width, self.height = width, height
        self.items = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth"><path d="M 0 0 L 10 5 L 0 10 z" fill="#62809A"/></marker><marker id="openArrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto" markerUnits="strokeWidth"><path d="M 1 1 L 10 6 L 1 11" fill="none" stroke="#62809A" stroke-width="1.5"/></marker></defs>',
            f'<rect width="{width}" height="{height}" fill="{WHITE}"/>',
        ]
        self.text(width / 2, 43, title, size=28, weight="bold", anchor="middle")
        if subtitle:
            self.text(width / 2, 74, subtitle, size=17, anchor="middle", color=LINE)

    def rect(self, x, y, w, h, fill=WHITE, stroke=LINE, radius=13, dash=""):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"{extra}/>')

    def ellipse(self, x, y, w, h, fill=LIGHT):
        self.items.append(f'<ellipse cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="{fill}" stroke="{LINE}" stroke-width="2"/>')

    def text(self, x, y, value, size=19, weight="normal", anchor="start", color=INK):
        self.items.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial, Helvetica, sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">{escape(str(value))}</text>')

    def lines(self, x, y, values, size=19, line_h=26, anchor="start", weight="normal", color=INK):
        for i, value in enumerate(values):
            self.text(x, y + i * line_h, value, size, weight, anchor, color)

    def box(self, x, y, w, h, title, lines=(), fill=LIGHT, size=19):
        self.rect(x, y, w, h, fill=fill)
        if lines:
            self.text(x + 16, y + 29, title, size=size, weight="bold")
            self.lines(x + 16, y + 57, lines, size=size - 2, line_h=23)
        else:
            vals = title.split("\n")
            start = y + h / 2 - (len(vals) - 1) * 12 + 7
            self.lines(x + w / 2, start, vals, size=size, line_h=24, anchor="middle", weight="bold")

    def oval(self, x, y, w, h, values, fill=LIGHT):
        self.ellipse(x, y, w, h, fill)
        vals = values.split("\n")
        start = y + h / 2 - (len(vals) - 1) * 12 + 7
        self.lines(x + w / 2, start, vals, size=18, line_h=24, anchor="middle")

    def arrow(self, x1, y1, x2, y2, label="", lx=None, ly=None, dash=""):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LINE}" stroke-width="2.3" marker-end="url(#arrow)"{extra}/>')
        if label:
            self.text(lx if lx is not None else (x1+x2)/2, ly if ly is not None else (y1+y2)/2 - 9, label, size=17, anchor="middle")

    def plain_line(self, x1, y1, x2, y2, dash=""):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        self.items.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LINE}" stroke-width="2"{extra}/>')

    def note(self, x, y, w, h, lines):
        self.rect(x, y, w, h, fill=SAND, stroke="#C79054", radius=9)
        self.lines(x + 14, y + 27, lines, size=17, line_h=23)

    def uml_line(self, x1, y1, x2, y2, label="", lx=None, ly=None, dash="", marker=""):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        end = f' marker-end="url(#{marker})"' if marker else ""
        self.items.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{LINE}" stroke-width="2.2"{extra}{end}/>'
        )
        if label:
            self.text(lx if lx is not None else (x1 + x2) / 2,
                      ly if ly is not None else (y1 + y2) / 2 - 8,
                      label, size=16, anchor="middle")

    def uml_path(self, path, marker="arrow", dash="", width=2.2):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        end = f' marker-end="url(#{marker})"' if marker else ""
        self.items.append(
            f'<path d="{path}" fill="none" stroke="{LINE}" stroke-width="{width}"{extra}{end}/>'
        )

    def uml_actor(self, x, y, label, stereotype=""):
        self.items.append(f'<circle cx="{x}" cy="{y}" r="13" fill="white" stroke="{INK}" stroke-width="2.3"/>')
        self.uml_line(x, y + 13, x, y + 48)
        self.uml_line(x - 22, y + 27, x + 22, y + 27)
        self.uml_line(x, y + 48, x - 18, y + 72)
        self.uml_line(x, y + 48, x + 18, y + 72)
        self.text(x, y + 96, label, size=17, weight="bold", anchor="middle")
        if stereotype:
            self.text(x, y + 116, stereotype, size=14, anchor="middle", color=LINE)

    def uml_action(self, x, y, w, h, label, fill=LIGHT, size=19):
        self.rect(x, y, w, h, fill=fill, stroke=LINE, radius=15)
        values = label.split("\n")
        self.lines(x + w / 2, y + h / 2 - (len(values) - 1) * 12 + 6,
                   values, size=size, line_h=24, anchor="middle")

    def uml_decision(self, x, y, w, h, label):
        points = f'{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}'
        self.items.append(f'<polygon points="{points}" fill="{WHITE}" stroke="{LINE}" stroke-width="2.2"/>')
        self.lines(x + w / 2, y + h / 2 - 7, label.split("\n"), size=17, line_h=21, anchor="middle")

    def uml_initial(self, x, y, radius=11):
        self.items.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{INK}"/>')

    def uml_final(self, x, y, radius=13):
        self.items.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="white" stroke="{INK}" stroke-width="2.4"/>')
        self.items.append(f'<circle cx="{x}" cy="{y}" r="{radius-5}" fill="{INK}"/>')

    def uml_package(self, x, y, w, h, name, contents=(), fill=WHITE):
        tab_w, tab_h = min(w * 0.68, max(185, len(name) * 12 + 28)), 27
        name_size = 18 if len(name) > 18 else 20
        self.items.append(
            f'<path d="M{x} {y+tab_h} L{x} {y} L{x+tab_w} {y} L{x+tab_w+18} {y+tab_h} '
            f'L{x+w} {y+tab_h} L{x+w} {y+h} L{x} {y+h} Z" '
            f'fill="{fill}" stroke="{LINE}" stroke-width="2.2"/>'
        )
        self.text(x + 13, y + 21, name, size=name_size, weight="bold")
        if contents:
            self.lines(x + 18, y + tab_h + 29, list(contents), size=15, line_h=22)

    def uml_artifact(self, x, y, w, h, name, name_size=16):
        fold = 17
        self.items.append(
            f'<path d="M{x} {y} L{x+w-fold} {y} L{x+w} {y+fold} L{x+w} {y+h} '
            f'L{x} {y+h} Z M{x+w-fold} {y} L{x+w-fold} {y+fold} L{x+w} {y+fold}" '
            f'fill="{LIGHT}" stroke="{LINE}" stroke-width="2"/>'
        )
        self.text(x + w / 2, y + 17, "«artifact»", size=13, anchor="middle", color=LINE)
        self.text(x + w / 2, y + h - 10, name, size=name_size, weight="bold", anchor="middle")

    def uml_component(self, x, y, w, h, name, details=(), fill=LIGHT, name_size=19):
        self.rect(x, y, w, h, fill=fill, radius=2)
        self.items.append(f'<rect x="{x+w-24}" y="{y+12}" width="17" height="9" fill="white" stroke="{LINE}" stroke-width="1.7"/>')
        self.items.append(f'<rect x="{x+w-24}" y="{y+25}" width="17" height="9" fill="white" stroke="{LINE}" stroke-width="1.7"/>')
        self.text(x + w / 2, y + 24, "«component»", size=15, anchor="middle", color=LINE)
        self.text(x + w / 2, y + 50, name, size=name_size, weight="bold", anchor="middle")
        if details:
            self.lines(x + w / 2, y + 72, list(details), size=16, line_h=19, anchor="middle")

    def uml_class(self, x, y, w, h, name, attributes, title_note=""):
        self.rect(x, y, w, h, fill=WHITE, radius=0)
        name_h = 39 if not title_note else 55
        self.items.append(f'<line x1="{x}" y1="{y+name_h}" x2="{x+w}" y2="{y+name_h}" stroke="{LINE}" stroke-width="1.6"/>')
        self.text(x + w / 2, y + 24, name, size=22, weight="bold", anchor="middle")
        if title_note:
            self.text(x + w / 2, y + 45, title_note, size=12, anchor="middle", color=LINE)
        self.lines(x + 12, y + name_h + 22, list(attributes), size=20, line_h=23)

    def uml_node(self, x, y, w, h, name, details=(), fill=LIGHT, stereotype="«device»"):
        depth = 18
        # UML node notation as a cuboid with distinct top, front and right faces.
        self.items.append(f'<rect x="{x}" y="{y+depth}" width="{w-depth}" height="{h-depth}" fill="{fill}" stroke="{LINE}" stroke-width="2.2"/>')
        self.items.append(f'<path d="M{x} {y+depth} L{x+depth} {y} L{x+w} {y} L{x+w-depth} {y+depth} Z" fill="{fill}" stroke="{LINE}" stroke-width="2.2"/>')
        self.items.append(f'<path d="M{x+w-depth} {y+depth} L{x+w} {y} L{x+w} {y+h-depth} L{x+w-depth} {y+h} Z" fill="{fill}" stroke="{LINE}" stroke-width="2.2"/>')
        self.text(x + w / 2, y + 48, stereotype, size=16, anchor="middle", color=LINE)
        self.text(x + w / 2, y + 73, name, size=20, weight="bold", anchor="middle")
        if details:
            self.lines(x + w / 2, y + 99, list(details), size=17, line_h=20, anchor="middle")

    def uml_note(self, x, y, w, h, lines, size=14, line_h=20):
        fold = 18
        self.items.append(
            f'<path d="M{x} {y} L{x+w-fold} {y} L{x+w} {y+fold} L{x+w} {y+h} '
            f'L{x} {y+h} Z M{x+w-fold} {y} L{x+w-fold} {y+fold} L{x+w} {y+fold}" '
            f'fill="{SAND}" stroke="#C79054" stroke-width="2"/>'
        )
        self.lines(x + 13, y + 27, list(lines), size=size, line_h=line_h)

    def save(self, filename):
        self.items.append("</svg>")
        path = OUT / filename
        path.write_text("\n".join(self.items) + "\n", encoding="utf-8")
        return path


def use_cases():
    d = Diagram(1200, 940, "Diagrama UML de casos de uso", "Interacciones del sistema UniMon con usuarios y sistemas externos")
    d.rect(245, 112, 710, 620, fill=WHITE, radius=0)
    d.text(265, 144, "Sistema UniMon", weight="bold", size=21)

    d.uml_actor(90, 285, "Solicitante")
    d.uml_actor(1100, 600, "Administrador")
    d.uml_actor(1100, 205, "Proveedor LLM", "«sistema externo»")
    d.uml_actor(1100, 385, "Ollama local", "«servicio local»")
    d.uml_actor(90, 790, "GLPI Cloud", "«sistema externo»")

    cases = [
        (285, 175, "Consultar soporte y\nresolver con fuentes"),
        (625, 175, "Recuperar y ordenar\nevidencia documental"),
        (285, 300, "Consultar trámite\ninstitucional"),
        (625, 300, "Generar respuesta\nconfigurada"),
        (285, 425, "Solicitar radicación\nde incidente"),
        (625, 425, "Administrar corpus e\ninstancias"),
        (285, 550, "Consultar seguimiento\nde ticket"),
        (625, 550, "Consultar métricas y\nauditorías"),
    ]
    for x, y, title in cases:
        d.oval(x, y, 290, 76, title)

    # UML actor-to-use-case associations are plain lines without arrowheads.
    for cy in (213, 338, 463, 588):
        d.uml_line(112, 312, 285, cy)
    # GLPI participates directly in ticket creation and follow-up. Plain
    # associations enter distinct lower-left points so they remain legible.
    d.uml_line(112, 817, 300, 482)
    d.uml_line(112, 817, 300, 607)
    # Administrative associations stay in the right margin of the system.
    d.uml_line(915, 463, 1080, 627)
    d.uml_line(915, 588, 1080, 627)
    d.uml_line(915, 338, 1080, 251)
    d.uml_line(915, 338, 1080, 431)

    # A dashed dependency with the UML include keyword shows the mandatory retrieval step.
    d.uml_line(575, 213, 625, 213, "«include»", lx=600, ly=196, dash="7 5", marker="openArrow")
    d.uml_note(260, 675, 680, 42, ["El canal web y el webhook de WhatsApp reutilizan los casos de consulta."])
    d.save("01_casos_de_uso.svg")


def sequence_rag():
    d = Diagram(1200, 900, "Diagrama UML de secuencia RAG", "Líneas de vida, mensajes, respuestas y fragmento alternativo de contingencia")
    xs = [70, 220, 370, 520, 670, 820, 970, 1120]
    names = ["Solicitante", "API chat", "FSM / router", "RAG service", "ChromaDB +\nreranker", "LLM client", "Proveedor cloud", "Ollama local"]
    for x, name in zip(xs, names):
        d.rect(x - 62, 112, 124, 58, fill=LIGHT, radius=0)
        d.lines(x, 137 - (len(name.split("\n")) - 1) * 9, name.split("\n"), size=15, line_h=19, anchor="middle", weight="bold")
        d.plain_line(x, 170, x, 880, dash="6 5")

    for x, y1, y2 in [(220, 212, 810), (370, 262, 770), (520, 312, 730),
                      (670, 362, 425), (820, 462, 750), (970, 555, 580), (1120, 650, 675)]:
        d.rect(x - 7, y1, 14, y2 - y1, fill="#D8E5EE", stroke=LINE, radius=0)

    d.uml_line(70, 212, 220, 212, "POST /chat · consulta", lx=145, ly=199, marker="arrow")
    d.uml_line(220, 262, 370, 262, "procesar_mensaje()", lx=295, ly=249, marker="arrow")
    d.uml_line(370, 312, 520, 312, "consulta + rol", lx=445, ly=299, marker="arrow")
    d.uml_line(520, 362, 670, 362, "búsqueda vectorial y léxica", lx=595, ly=349, marker="arrow")
    d.uml_line(670, 412, 520, 412, "candidatos + referencias", lx=595, ly=399, dash="7 5", marker="openArrow")
    d.uml_line(520, 462, 820, 462, "contexto seleccionado", lx=670, ly=449, marker="arrow")

    # UML combined fragment: the configured provider is used, with a guarded fallback.
    d.rect(785, 490, 380, 205, fill=WHITE, stroke=INK, radius=0)
    d.items.append(f'<path d="M785 490 L850 490 L850 514 L785 514 Z" fill="{WHITE}" stroke="{INK}" stroke-width="1.7"/>')
    d.text(817, 508, "alt", size=15, weight="bold", anchor="middle")
    d.text(860, 527, "[proveedor cloud configurado responde]", size=14)
    d.uml_line(820, 555, 970, 555, "generate()", lx=895, ly=543, marker="arrow")
    d.uml_line(970, 580, 820, 580, "respuesta", lx=895, ly=568, dash="7 5", marker="openArrow")
    d.uml_line(785, 600, 1165, 600)
    d.text(860, 625, "[falla cloud y Ollama está habilitado]", size=14)
    d.uml_line(820, 650, 1120, 650, "generate()", lx=970, ly=638, marker="arrow")
    d.uml_line(1120, 675, 820, 675, "respuesta local", lx=970, ly=663, dash="7 5", marker="openArrow")

    d.uml_line(820, 730, 520, 730, "texto generado", lx=670, ly=718, dash="7 5", marker="openArrow")
    d.uml_line(520, 770, 370, 770, "respuesta + fuentes", lx=445, ly=758, dash="7 5", marker="openArrow")
    d.uml_line(370, 810, 220, 810, "respuesta validada", lx=295, ly=798, dash="7 5", marker="openArrow")
    d.uml_line(220, 850, 70, 850, "respuesta + fuentes", lx=145, ly=838, dash="7 5", marker="openArrow")
    d.save("02_secuencia_rag.svg")


def sequence_glpi():
    d = Diagram(1200, 1040, "Diagrama UML de secuencia GLPI", "Mensajes de creación, alternativa de endpoint, asociación opcional y cierre de sesión")
    xs = [100, 340, 580, 820, 1080]
    names = ["Solicitante", "API / FSM", "GLPI adapter", "GLPI REST API", "SQLite telemetry"]
    for x, name in zip(xs, names):
        d.rect(x - 80, 112, 160, 58, fill=LIGHT, radius=0)
        d.text(x, 147, name, size=15, weight="bold", anchor="middle")
        d.plain_line(x, 170, x, 970, dash="6 5")
    for x, y1, y2 in [(340, 205, 975), (580, 355, 910), (820, 405, 885), (1080, 935, 955)]:
        d.rect(x - 7, y1, 14, y2 - y1, fill="#D8E5EE", stroke=LINE, radius=0)

    d.uml_line(100, 210, 340, 210, "POST /chat · solicita escalar", lx=220, ly=198, marker="arrow")
    d.uml_line(340, 255, 100, 255, "solicita datos requeridos", lx=220, ly=243, marker="arrow")
    d.uml_line(100, 300, 340, 300, "nombre, correo y descripción", lx=220, ly=288, marker="arrow")
    d.uml_line(340, 355, 580, 355, "create_ticket(datos)", lx=460, ly=343, marker="arrow")
    d.uml_line(580, 405, 820, 405, "GET /initSession", lx=700, ly=393, marker="arrow")
    d.uml_line(820, 445, 580, 445, "session_token", lx=700, ly=433, dash="7 5", marker="openArrow")

    # The implementation retries the alternate creation route when the first route fails.
    d.rect(545, 465, 360, 230, fill=WHITE, stroke=INK, radius=0)
    d.items.append(f'<path d="M545 465 L612 465 L612 489 L545 489 Z" fill="{WHITE}" stroke="{INK}" stroke-width="1.7"/>')
    d.text(579, 483, "alt", size=15, weight="bold", anchor="middle")
    d.text(625, 500, "[ruta preferida]", size=13)
    d.uml_line(580, 545, 820, 545, "POST /Assistance/Ticket", lx=700, ly=532, marker="arrow")
    d.uml_line(820, 570, 580, 570, "id o error", lx=700, ly=558, dash="7 5", marker="openArrow")
    d.uml_line(545, 595, 905, 595)
    d.text(625, 620, "[si falla, probar ruta alterna]", size=13)
    d.uml_line(580, 655, 820, 655, "POST /Ticket", lx=700, ly=643, marker="arrow")
    d.uml_line(820, 680, 580, 680, "id o error", lx=700, ly=668, dash="7 5", marker="openArrow")

    d.rect(545, 710, 360, 125, fill=WHITE, stroke=INK, radius=0)
    d.items.append(f'<path d="M545 710 L612 710 L612 734 L545 734 Z" fill="{WHITE}" stroke="{INK}" stroke-width="1.7"/>')
    d.text(579, 728, "opt", size=15, weight="bold", anchor="middle")
    d.text(625, 747, "[ticket confirmado y correo válido]", size=13)
    d.uml_line(580, 785, 820, 785, marker="arrow")
    d.text(700, 773, "POST /Ticket/{id}/Ticket_User", size=14, anchor="middle")
    d.uml_line(820, 812, 580, 812, "actor asociado", lx=700, ly=800, dash="7 5", marker="openArrow")
    d.uml_line(580, 860, 820, 860, "GET /killSession", lx=700, ly=848, marker="arrow")
    d.uml_line(820, 885, 580, 885, "sesión cerrada", lx=700, ly=873, dash="7 5", marker="openArrow")
    d.uml_line(580, 910, 340, 910, "ticket ID o error", lx=460, ly=898, dash="7 5", marker="openArrow")
    d.uml_line(340, 935, 1080, 935, "registrar resultado del ticket", lx=710, ly=923, marker="arrow")
    d.uml_line(340, 970, 100, 970, "resultado + estado", lx=220, ly=958, dash="7 5", marker="openArrow")
    d.uml_note(170, 990, 860, 38, ["UniMon informa un identificador solo cuando GLPI confirma su creación."])
    d.save("03_secuencia_glpi.svg")


def activity():
    d = Diagram(1400, 1160, "Diagrama UML de actividad del flujo de UniMon", "Acciones, decisiones y flujos del diagnóstico y la radicación de soporte")
    d.uml_initial(700, 115)
    d.uml_action(560, 150, 280, 60, "Recibir consulta y sesión")
    d.uml_path("M700 126 L700 150")
    d.uml_decision(630, 240, 140, 80, "¿Rol válido?")
    d.uml_path("M700 210 L700 240")

    d.uml_action(70, 245, 300, 70, "Solicitar y validar\nel rol del usuario")
    d.uml_path("M630 280 L500 280 L370 280", marker="arrow")
    d.text(480, 266, "[sin rol]", size=15, anchor="middle")
    d.uml_path("M220 245 L220 225 L700 225 L700 240", marker="arrow")
    d.text(465, 216, "[rol capturado]", size=14, anchor="middle")

    d.uml_action(560, 360, 280, 70, "Diagnosticar y recuperar\nevidencia con RAG")
    d.uml_path("M700 320 L700 360")
    d.text(755, 345, "[rol válido]", size=15)

    d.uml_decision(630, 465, 140, 80, "¿Respuesta\nsustentada?")
    d.uml_path("M700 430 L700 465")
    d.uml_action(980, 470, 300, 70, "Mostrar orientación\ny fuentes")
    d.uml_path("M770 505 L980 505")
    d.text(875, 491, "[sí]", size=15, anchor="middle")
    d.uml_final(1130, 600)
    d.uml_path("M1130 540 L1130 587")

    d.uml_action(560, 590, 280, 70, "Ofrecer radicación\na GLPI")
    d.uml_path("M700 545 L700 590")
    d.text(754, 572, "[no]", size=15)
    d.uml_decision(630, 690, 140, 80, "¿Acepta\nescalar?")
    d.uml_path("M700 660 L700 690")

    d.uml_action(70, 695, 300, 70, "Informar alternativa\nde atención")
    d.uml_path("M630 730 L500 730 L370 730")
    d.text(490, 716, "[no]", size=15, anchor="middle")
    d.uml_final(220, 855)
    d.uml_path("M220 765 L220 842")

    d.uml_action(560, 820, 280, 70, "Capturar y validar nombre,\ncorreo y descripción")
    d.uml_path("M700 770 L700 820")
    d.text(755, 800, "[sí]", size=15)
    d.uml_action(940, 820, 300, 70, "Crear ticket mediante\nla API de GLPI", fill=SAND)
    d.uml_path("M840 855 L940 855")
    d.uml_decision(1020, 925, 140, 80, "¿GLPI confirma\nel identificador?")
    d.uml_path("M1090 890 L1090 925")

    d.uml_action(1120, 1025, 240, 64, "Mostrar ID\nconfirmado", fill=MINT, size=16)
    d.uml_path("M1160 965 L1240 965 L1240 1025")
    d.text(1200, 950, "[sí]", size=15, anchor="middle")
    d.uml_final(1240, 1130)
    d.uml_path("M1240 1089 L1240 1117")

    d.uml_action(430, 1025, 240, 64, "Informar error\nsin inventar radicado", fill=SAND, size=16)
    d.uml_path("M1020 965 L790 965 L790 1057 L670 1057")
    d.text(900, 950, "[no]", size=15, anchor="middle")
    d.uml_final(550, 1130)
    d.uml_path("M550 1089 L550 1117")
    d.save("04_actividad.svg")


def modules():
    d = Diagram(1200, 800, "Diagrama UML de paquetes de UniMon", "Vista lógica de los módulos Python y sus dependencias principales")
    d.uml_artifact(490, 105, 220, 62, "main.py")
    d.uml_package(45, 220, 490, 390, "app.routers")
    d.uml_package(610, 220, 545, 390, "app.services")

    router_files = [
        (75, 290, "chat.py"), (300, 290, "admin_router.py"),
        (75, 390, "analytics.py"), (300, 390, "whatsapp.py"),
    ]
    for x, y, name in router_files:
        d.uml_artifact(x, y, 195, 65, name)

    service_files = [
        (640, 285, "router_logic.py"), (885, 285, "bot_router_service.py"),
        (640, 370, "rag_service.py"), (885, 370, "llm_client.py"),
        (640, 455, "glpi_service.py"), (885, 455, "telemetry_service.py"),
        (640, 540, "bot_instance_service.py"), (885, 540, "document_catalog_service.py"),
    ]
    for x, y, name in service_files:
        d.uml_artifact(x, y, 225, 62, name, name_size=14 if name == "document_catalog_service.py" else 16)

    d.uml_line(550, 167, 290, 220, dash="7 5", marker="openArrow")
    d.uml_line(650, 167, 880, 220, dash="7 5", marker="openArrow")
    d.text(410, 192, "«use»", size=14, anchor="middle")
    d.text(775, 192, "«use»", size=14, anchor="middle")
    d.uml_line(535, 405, 610, 405, "«use»", lx=572, ly=389, dash="7 5", marker="openArrow")
    d.uml_note(135, 670, 930, 62, ["Los archivos se muestran como artefactos dentro de paquetes; la dependencia depende de la ruta y del servicio invocado."])
    d.save("05_modulos.svg")


def data_model():
    d = Diagram(1500, 930, "Diagrama UML de clases de persistencia", "Clases y asociaciones verificadas; {PK}, {FK} y {UNIQUE} resumen restricciones del esquema")
    d.uml_package(30, 120, 910, 555, "data/analytics.db · SQLite")
    d.uml_class(70, 185, 360, 195, "TelemetrySession", [
        "session_id: TEXT {PK}", "role: TEXT", "start_time: TIMESTAMP",
        "end_time: TIMESTAMP [0..1]", "final_status: TEXT", "escalated_ticket: INTEGER",
    ])
    d.uml_class(500, 170, 395, 270, "TelemetryInteraction", [
        "id: INTEGER {PK}", "session_id: TEXT {FK}", "timestamp: TIMESTAMP",
        "user_query: TEXT", "bot_response: TEXT", "source_used: TEXT",
        "latency_ms: REAL", "prompt_tokens / eval_tokens: INTEGER", "feedback: TEXT",
    ])
    d.uml_class(70, 445, 360, 180, "TelemetryTicket", [
        "id: INTEGER {PK}", "session_id: TEXT", "email: TEXT",
        "ticket_id: INTEGER", "action: TEXT", "created_at: TIMESTAMP",
    ])
    d.uml_class(500, 475, 395, 165, "TelemetryIgnoredQuery", [
        "id: INTEGER {PK}", "query_text: TEXT", "normalized_query: TEXT {UNIQUE}",
        "reason: TEXT", "dismissed_at: TIMESTAMP",
    ])

    # Enforced foreign-key association in telemetry_service.py.
    d.uml_line(430, 285, 500, 285)
    d.text(440, 270, "1", size=16, anchor="middle")
    d.text(489, 270, "0..*", size=16, anchor="middle")

    # The ticket session_id is stored as text and is not declared as a database FK.
    d.uml_line(250, 445, 250, 380, "session_id · sin FK", lx=320, ly=415, dash="7 5", marker="openArrow")

    d.uml_package(980, 120, 490, 300, "instances.sqlite3 · SQLite")
    d.uml_class(1020, 195, 410, 190, "ChatbotInstance", [
        "bot_id: TEXT {PK}", "display_name / dependency_name: TEXT",
        "scope_description: TEXT", "llm_provider / llm_model: TEXT", "enabled: INTEGER",
    ])
    d.uml_note(55, 720, 650, 120, [
        "ChromaDB contiene índices documentales por asistente y colecciones de Golden Cache.",
        "Son almacenes vectoriales independientes, no tablas de analytics.db.",
    ], size=17, line_h=23)
    d.uml_note(755, 720, 690, 120, [
        "GLPI Cloud conserva los tickets oficiales.",
        "TelemetryTicket guarda actividad local; no reemplaza el estado de GLPI.",
    ], size=17, line_h=23)
    d.save("06_modelo_datos.svg")


def components():
    d = Diagram(1320, 960, "Diagrama UML de componentes de UniMon", "Componentes de software y dependencias principales observables en el código")

    # System boundary, clients, and providers are components; directed dashed
    # dependencies point from each client to the component it consumes.
    d.rect(255, 105, 750, 795, fill=WHITE, radius=0, dash="9 6")
    d.text(280, 137, "Aplicación UniMon", size=21, weight="bold")

    # Draw dependencies before components so connectors remain behind symbols.
    dependencies = [
        "M225 220 L365 220",                           # Web -> API
        "M225 390 L270 390 L270 285 L365 285",         # WhatsApp -> API
        "M580 305 L580 335",                           # API -> orchestration
        "M500 435 L440 475",                            # orchestration -> RAG
        "M660 435 L785 475",                            # orchestration -> GLPI
        "M440 585 L440 635",                           # RAG -> LLM client
        "M785 585 L785 635",                           # GLPI -> ticket telemetry
        "M310 685 L225 685",                           # LLM client -> cloud provider
        "M910 530 L1030 530",                          # GLPI adapter -> GLPI API
        "M785 735 L785 780",                           # telemetry -> SQLite
        "M440 735 L440 780",                           # LLM client -> local Ollama
    ]
    for path in dependencies:
        d.uml_path(path, marker="openArrow", dash="7 5")

    d.uml_component(25, 175, 200, 90, "Web client", ["chat + panel admin"], fill=WHITE)
    d.uml_component(25, 345, 200, 90, "WhatsApp Cloud", ["webhook de entrada"], fill=WHITE)
    d.uml_component(25, 635, 200, 95, "Proveedor LLM", ["Gemini / OpenAI"], fill=SAND)
    d.uml_component(1030, 480, 255, 95, "GLPI REST API", ["creación de tickets"], fill=SAND)

    d.uml_component(365, 190, 430, 115, "API FastAPI", ["chat, administración y webhook", "validación"], fill=MINT)
    d.uml_component(450, 335, 260, 100, "Orquestación conversacional", ["FSM + selección de instancia"], fill=LIGHT, name_size=17)
    d.uml_component(310, 475, 260, 110, "Recuperación RAG", ["ChromaDB, catálogo", "reranking y fuentes"], fill=LIGHT)
    d.uml_component(660, 475, 250, 110, "Adaptador GLPI", ["sesión REST y radicación"], fill=LIGHT)
    d.uml_component(660, 635, 250, 100, "Telemetría e instancias", ["métricas, historial y tickets"], fill=LIGHT)
    d.uml_component(310, 635, 260, 100, "Cliente LLM", ["proveedor cloud", "contingencia Ollama"], fill=SAND)
    d.uml_component(660, 780, 250, 100, "Persistencia SQLite", ["analytics.db", "instances.sqlite3"], fill=MINT)
    d.uml_component(310, 780, 260, 100, "Ollama local", ["servicio de generación"], fill=SAND)
    d.note(170, 910, 980, 40, ["La disponibilidad de servicios externos requiere configuración y credenciales vigentes."])
    d.save("07_componentes.svg")


def deployment():
    d = Diagram(1500, 1010, "Diagrama UML de despliegue de UniMon", "Topología de referencia del piloto; debe contrastarse con el entorno institucional definitivo")

    # Draw the hosting device first so the nested nodes and their links remain visible.
    d.uml_node(340, 145, 650, 730, "Host autorizado para UniMon", ["nodo de referencia; no implica despliegue productivo"], fill=WHITE, stereotype="«device»")

    # Communication paths are solid, undirected links between deployment nodes.
    d.uml_line(270, 300, 340, 365, "HTTPS", lx=300, ly=320)
    d.uml_line(270, 610, 340, 445, "HTTPS", lx=305, ly=535)
    d.uml_line(990, 370, 1060, 300, "API", lx=1020, ly=325)
    d.uml_line(990, 455, 1060, 610, "REST", lx=1023, ly=535)
    d.uml_line(475, 495, 475, 535)
    d.uml_line(795, 495, 795, 535)

    d.uml_node(30, 215, 240, 170, "Equipo del usuario", ["Acceso mediante navegador"], fill=LIGHT, stereotype="«device»")
    d.uml_node(30, 500, 240, 190, "Meta WhatsApp Cloud", ["Webhook externo", "HTTPS"], fill=SAND, stereotype="«executionEnvironment»")
    d.uml_node(390, 270, 550, 225, "Python + FastAPI", ["entorno de ejecución"], fill=LIGHT, stereotype="«executionEnvironment»")
    d.uml_artifact(430, 380, 220, 75, "app/routers + services")
    d.uml_artifact(675, 380, 215, 75, "Configuración protegida")

    d.uml_node(390, 535, 245, 210, "Ollama local", ["servicio de generación"], fill=SAND, stereotype="«executionEnvironment»")
    d.uml_artifact(425, 650, 175, 55, "unimon:8b")
    d.uml_node(665, 535, 275, 320, "Volumen local de datos", ["persistencia del piloto"], fill=MINT, stereotype="«device»")
    d.uml_artifact(700, 650, 205, 48, "Documentos saneados")
    d.uml_artifact(700, 700, 205, 48, "ChromaDB persistente")
    d.uml_artifact(700, 750, 205, 48, "analytics.db")
    d.uml_artifact(700, 800, 205, 48, "instances.sqlite3")

    d.uml_node(1060, 215, 390, 170, "Proveedor LLM", ["Gemini u OpenAI configurado", "API HTTPS"], fill=SAND, stereotype="«executionEnvironment»")
    d.uml_node(1060, 500, 390, 190, "GLPI Cloud", ["API REST", "tickets institucionales"], fill=SAND, stereotype="«executionEnvironment»")
    d.uml_note(180, 910, 1140, 65, ["El diagrama expresa nodos, artefactos y rutas de comunicación previstas. La disponibilidad depende de credenciales vigentes y de la infraestructura aprobada."])
    d.save("08_despliegue.svg")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for fn in (use_cases, sequence_rag, sequence_glpi, activity, modules, data_model, components, deployment):
        fn()
    print(f"Generated eight SVG figures in {OUT}")
