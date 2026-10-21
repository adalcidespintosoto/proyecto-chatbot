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
            '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto" markerUnits="strokeWidth"><path d="M 0 0 L 10 5 L 0 10 z" fill="#62809A"/></marker></defs>',
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

    def save(self, filename):
        self.items.append("</svg>")
        path = OUT / filename
        path.write_text("\n".join(self.items) + "\n", encoding="utf-8")
        return path


def use_cases():
    d = Diagram(1100, 795, "Casos de uso de UniMon", "Canales y funciones presentes en la versión revisada")
    d.rect(230, 105, 625, 630, fill=WHITE, dash="8 5")
    d.text(250, 137, "Sistema UniMon", weight="bold", size=21)
    d.box(25, 240, 180, 70, "Solicitante")
    d.box(25, 580, 180, 70, "Administrador")
    d.box(885, 235, 190, 75, "Proveedor LLM\no Ollama", fill=MINT)
    d.box(885, 475, 190, 75, "GLPI Cloud", fill=MINT)
    cases = [
        (280, 165, "Consultar soporte\ny documentos"),
        (555, 165, "Orientación de trámite\ninstitucional"),
        (280, 290, "Enrutar consulta\npor especialidad"),
        (555, 290, "Confirmar resultado\no pedir ayuda"),
        (280, 415, "Radicar incidencia\ntécnica"),
        (555, 415, "Consultar estado\nde ticket"),
        (280, 560, "Administrar fuentes\ne instancias"),
        (555, 560, "Ver analítica\ny auditorías"),
    ]
    for x, y, title in cases:
        d.oval(x, y, 235, 78, title)
    for y, x2, y2 in [(275, 280, 205), (275, 280, 330), (275, 280, 455)]:
        d.plain_line(205, y, x2, y2)
    d.plain_line(205, 615, 280, 600)
    d.plain_line(790, 205, 885, 272)
    d.plain_line(515, 455, 885, 510)
    d.plain_line(790, 455, 885, 510)
    d.note(250, 682, 580, 42, ["El canal web y el webhook WhatsApp comparten capacidades de consulta."])
    d.save("01_casos_de_uso.svg")


def sequence_rag():
    d = Diagram(1100, 755, "Secuencia de consulta documental", "Proveedor configurable; contingencia local si el proveedor falla")
    xs = [80, 245, 410, 575, 740, 925]
    names = ["Solicitante", "API / router", "RAG", "Chroma +\nreranker", "Cliente LLM", "Cloud /\nOllama"]
    for x, n in zip(xs, names):
        d.box(x - 69, 105, 138, 64, n, fill=LIGHT, size=17)
        d.plain_line(x, 169, x, 665, dash="6 5")
    steps = [
        (192, 0, 1, "1  Consulta"),
        (245, 1, 2, "2  Consulta de UniMon o instancia"),
        (298, 2, 3, "3  Recuperación local"),
        (351, 3, 2, "4  Fragmentos ordenados"),
        (404, 2, 4, "5  Contexto pertinente"),
        (457, 4, 5, "6  Generación configurada"),
        (510, 5, 4, "7  Texto o error"),
        (563, 4, 1, "8  Respuesta validada"),
        (616, 1, 0, "9  Orientación y fuentes"),
    ]
    for y, a, b, lab in steps:
        d.arrow(xs[a] + (8 if b > a else -8), y, xs[b] - (8 if b > a else -8), y, lab)
    d.note(152, 668, 790, 68, ["Si el proveedor remoto falla, el cliente puede intentar Ollama local.", "La API registra latencia, uso y fuentes en SQLite según la ruta."])
    d.save("02_secuencia_rag.svg")


def sequence_glpi():
    d = Diagram(1100, 790, "Secuencia de radicación en GLPI", "El identificador se comunica solo tras una respuesta de creación confirmada")
    xs = [90, 310, 530, 770, 990]
    names = ["Solicitante", "API / FSM", "GLPIService", "GLPI Cloud", "SQLite"]
    for x, n in zip(xs, names):
        d.box(x - 84, 105, 168, 62, n, size=18)
        d.plain_line(x, 168, x, 690, dash="6 5")
    steps = [
        (192, 0, 1, "1  Solicita radicación"),
        (248, 1, 0, "2  Captura nombre, correo y descripción"),
        (304, 1, 2, "3  create_ticket(datos)"),
        (360, 2, 3, "4  initSession"),
        (416, 2, 3, "5  POST /Assistance/Ticket o /Ticket"),
        (472, 3, 2, "6  ID confirmado o error"),
        (528, 2, 3, "7  Si hay ID, asociación opcional"),
        (584, 2, 3, "8  killSession en finally"),
        (640, 1, 4, "9  Registro local de actividad"),
    ]
    for y, a, b, lab in steps:
        d.arrow(xs[a] + (9 if b > a else -9), y, xs[b] - (9 if b > a else -9), y, lab)
    d.note(185, 697, 730, 72, ["Si no se confirma la creación, el flujo informa el error sin inventar radicado.", "La asociación depende de un correo válido y de la respuesta de GLPI."])
    d.save("03_secuencia_glpi.svg")


def fsm():
    d = Diagram(1100, 790, "Estados principales de la conversación", "Vista condensada de router_logic.py; omite subreglas de intención")
    d.box(425, 104, 250, 64, "IDLE")
    d.box(80, 222, 245, 70, "PIDIENDO_ROL")
    d.box(425, 222, 250, 70, "DIAGNOSTICO")
    d.box(780, 222, 245, 70, "SOLUCIONADO /\nFINALIZADO", fill=MINT)
    d.arrow(425, 134, 325, 253, "sin rol", lx=315, ly=183)
    d.arrow(550, 168, 550, 222, "con rol", lx=615, ly=203)
    d.arrow(325, 253, 425, 253, "rol válido", lx=375, ly=240)
    d.arrow(675, 253, 780, 253, "resuelto", lx=727, ly=238)
    d.box(425, 355, 250, 70, "OFRECIENDO_\nRADICACION", fill=SAND)
    d.arrow(550, 292, 550, 355, "sin respuesta o pide soporte", lx=730, ly=331)
    d.box(62, 485, 205, 66, "PIDIENDO_\nNOMBRE")
    d.box(312, 485, 205, 66, "PIDIENDO_\nCORREO")
    d.box(562, 485, 205, 66, "PIDIENDO_\nDESCRIPCION")
    d.box(812, 485, 215, 66, "Crear ticket\nen GLPI", fill=SAND)
    d.arrow(425, 390, 164, 485, "acepta radicar", lx=282, ly=420)
    d.arrow(267, 518, 312, 518)
    d.arrow(517, 518, 562, 518)
    d.arrow(767, 518, 812, 518)
    d.box(672, 645, 200, 66, "TICKET_CREADO", fill=MINT)
    d.box(227, 645, 200, 66, "Error informado\no CANCELADO", fill=SAND)
    d.arrow(920, 551, 770, 645, "confirmado", lx=873, ly=608)
    d.arrow(920, 551, 327, 645, "fallo o cancelación", lx=525, ly=609)
    d.note(85, 723, 925, 54, ["La cancelación también puede ocurrir durante la captura; sesiones inactivas se limpian por TTL."])
    d.save("04_fsm.svg")


def modules():
    d = Diagram(1100, 775, "Vista lógica de módulos", "Dependencias principales verificadas en el paquete app")
    d.box(445, 105, 210, 62, "main.py", fill=MINT)
    d.arrow(550, 167, 550, 211)
    d.rect(45, 212, 1010, 130, fill=WHITE, dash="7 5")
    d.text(63, 242, "Routers FastAPI", size=20, weight="bold")
    for x, n in [(70, "chat.py"), (318, "admin_router.py"), (566, "analytics.py"), (814, "whatsapp.py")]:
        d.box(x, 263, 216, 56, n, size=18)
    d.arrow(550, 342, 550, 386)
    d.rect(45, 387, 1010, 210, fill=WHITE, dash="7 5")
    d.text(63, 419, "Servicios de aplicación", size=20, weight="bold")
    for x, n in [
        (70, "router_logic.py\nFSM de TI"),
        (318, "bot_router_service.py\nSelección de instancia"),
        (566, "rag_service.py\ny llm_client.py"),
        (814, "glpi_service.py\ny telemetry_service.py"),
    ]:
        d.box(x, 455, 216, 100, n, fill=MINT, size=18)
    d.note(95, 638, 910, 92, ["bot_instance_service.py gestiona asistentes por dependencia y su registro.", "golden_cache_service.py y document_catalog_service.py apoyan recuperación.", "Los routers delegan según el endpoint; no todos invocan todos los servicios."])
    d.save("05_modulos.svg")


def data_model():
    d = Diagram(1100, 840, "Persistencia actual del proyecto", "Esquema relacional local y almacenes documentales separados")
    d.rect(35, 105, 670, 470, fill=WHITE, dash="8 5")
    d.text(55, 138, "data/analytics.db  SQLite", weight="bold", size=21)
    d.box(60, 166, 285, 118, "telemetry_sessions", ["PK session_id", "role, final_status", "start_time, end_time"], fill=LIGHT)
    d.box(385, 166, 285, 164, "telemetry_interactions", ["PK id; FK session_id", "query, response, source", "latency, tokens, feedback", "documentos de referencia"], fill=LIGHT)
    d.arrow(345, 227, 385, 227, "FK", lx=365, ly=207)
    d.box(60, 363, 285, 128, "telemetry_tickets", ["PK id; session_id (texto)", "email, ticket_id", "action, created_at"], fill=MINT)
    d.box(385, 363, 285, 128, "telemetry_ignored_queries", ["PK id; query_text", "normalized_query UNIQUE", "reason, dismissed_at"], fill=MINT)
    d.rect(745, 105, 320, 470, fill=WHITE, dash="8 5")
    d.text(762, 138, "Otros almacenes locales", weight="bold", size=21)
    d.box(765, 170, 280, 120, "instances.sqlite3", ["chatbot_instances", "proveedor y modelo", "configuración por instancia"], fill=LIGHT, size=18)
    d.box(765, 320, 280, 95, "ChromaDB", ["índice UniMon TI", "índices por instancia"], fill=MINT, size=18)
    d.box(765, 440, 280, 95, "Golden Cache", ["colección de casos validados", "en ChromaDB"], fill=MINT, size=18)
    d.box(90, 628, 920, 95, "GLPI Cloud  Sistema externo", ["Conserva los tickets oficiales. UniMon registra actividad local de tickets,", "pero no sustituye el almacenamiento ni el estado oficial de GLPI."], fill=SAND, size=20)
    d.note(90, 755, 920, 56, ["No existe una única tabla local interactions como esquema principal.", "Las colecciones vectoriales no forman parte del modelo relacional SQLite."])
    d.save("06_modelo_datos.svg")


def components():
    d = Diagram(1100, 795, "Componentes de UniMon", "Arquitectura implementada y servicios configurables")
    d.box(55, 120, 255, 70, "Web chat / panel admin")
    d.box(55, 235, 255, 70, "WhatsApp Cloud API", fill=LIGHT)
    d.box(405, 165, 275, 90, "FastAPI", ["routers, seguridad", "validación y telemetría"], fill=MINT)
    d.arrow(310, 155, 405, 195)
    d.arrow(310, 270, 405, 225)
    d.box(90, 360, 250, 105, "Enrutamiento", ["UniMon TI o instancia", "por dependencia"], fill=LIGHT)
    d.box(425, 360, 250, 105, "RAG local", ["ingesta, recuperación", "reranking y fuentes"], fill=LIGHT)
    d.box(760, 360, 250, 105, "Servicios de soporte", ["GLPI, Golden Cache", "analítica y catálogos"], fill=LIGHT)
    d.arrow(490, 255, 215, 360)
    d.arrow(490, 255, 550, 360)
    d.arrow(590, 255, 885, 360)
    d.box(85, 580, 250, 70, "Documentos + ChromaDB", fill=MINT)
    d.box(425, 580, 250, 70, "Cliente LLM", fill=SAND)
    d.box(765, 580, 250, 70, "SQLite / GLPI Cloud", fill=MINT)
    d.arrow(490, 465, 210, 580)
    d.arrow(550, 465, 550, 580)
    d.arrow(885, 465, 890, 580)
    d.note(107, 690, 885, 65, ["El cliente LLM puede usar proveedor remoto configurado o Ollama local.", "GLPI y WhatsApp requieren credenciales y configuración externas."])
    d.save("07_componentes.svg")


def deployment():
    d = Diagram(1100, 835, "Despliegue de referencia", "Topología de piloto; requiere validar infraestructura y configuración efectivas")
    d.box(45, 125, 250, 70, "Navegador del usuario")
    d.box(45, 230, 250, 70, "Meta WhatsApp Cloud", fill=SAND)
    d.rect(350, 115, 465, 575, fill=WHITE, dash="8 5")
    d.text(370, 150, "Entorno autorizado para UniMon", size=21, weight="bold")
    d.box(395, 180, 375, 100, "Aplicación FastAPI", ["routers, FSM, instancias", "seguridad y cliente LLM"], fill=LIGHT)
    d.box(395, 335, 375, 100, "Procesamiento local", ["embeddings, reranking", "Ollama si está disponible"], fill=MINT)
    d.box(395, 485, 375, 145, "Persistencia local", ["manuales y Markdown saneados", "ChromaDB, Golden Cache", "SQLite de telemetría e instancias"], fill=MINT)
    d.arrow(295, 160, 395, 220, "HTTPS", lx=340, ly=178)
    d.arrow(295, 265, 395, 235, "webhook", lx=340, ly=274)
    d.arrow(580, 280, 580, 335)
    d.arrow(580, 435, 580, 485)
    d.box(865, 185, 200, 80, "Proveedor LLM\nconfigurado", fill=SAND)
    d.box(865, 370, 200, 80, "GLPI Cloud", fill=SAND)
    d.arrow(770, 225, 865, 225, "API", lx=820, ly=207)
    d.arrow(770, 245, 865, 410, "REST", lx=842, ly=330)
    d.note(112, 728, 875, 67, ["La estación de desarrollo no demuestra despliegue en producción.", "Verificar en el entorno final TLS, accesos, respaldo y disponibilidad de Ollama."])
    d.save("08_despliegue.svg")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for fn in (use_cases, sequence_rag, sequence_glpi, fsm, modules, data_model, components, deployment):
        fn()
    print(f"Generated eight SVG figures in {OUT}")
