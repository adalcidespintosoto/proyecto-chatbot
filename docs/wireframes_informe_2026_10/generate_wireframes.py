"""Generate report wireframes from UniMon's current public and admin views.

The editable SVGs are intentionally static representations. Labels, controls,
spacing, and dark palette are derived from app/static/index.html and
app/static/admin.html; conversation text and empty dashboard values are examples.
"""

from __future__ import annotations

from html import escape
from pathlib import Path


OUT = Path(__file__).resolve().parent
W, H = 1600, 900
BG = "#090d16"
SURFACE = "#0f172a"
SURFACE_2 = "#1e293b"
LINE = "#334155"
TEXT = "#f8fafc"
CONTENT = "#e2e8f0"
MUTED = "#94a3b8"
BLUE = "#1d4ed8"
CYAN = "#00a3ff"
GREEN = "#34d399"
AMBER = "#fbbf24"
PURPLE = "#a78bfa"
FONT = "Segoe UI, Arial, sans-serif"


class SVG:
    def __init__(self, title: str, view_scale: float = 1):
        self.view_scale = view_scale
        view_w, view_h = W * view_scale, H * view_scale
        self.items = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{view_w:g}" height="{view_h:g}" viewBox="0 0 {view_w:g} {view_h:g}" role="img" aria-label="{escape(title)}">',
            '<defs><linearGradient id="brand" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0066cc"/><stop offset="1" stop-color="#00d2ff"/></linearGradient><radialGradient id="glow"><stop offset="0" stop-color="#00a3ff" stop-opacity=".12"/><stop offset="1" stop-color="#00a3ff" stop-opacity="0"/></radialGradient></defs>',
            f'<g transform="scale({view_scale:g})">',
            f'<rect width="{W}" height="{H}" fill="{BG}"/>',
            f'<ellipse cx="80" cy="55" rx="340" ry="230" fill="url(#glow)"/>',
            f'<ellipse cx="1530" cy="865" rx="360" ry="240" fill="url(#glow)"/>',
        ]

    def rect(self, x, y, w, h, fill=SURFACE, stroke=LINE, r=12, sw=1.5):
        self.items.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def line(self, x1, y1, x2, y2, color=LINE, sw=1.5):
        self.items.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"/>')

    def text(self, x, y, value, size=18, color=TEXT, weight=400, anchor="start"):
        rendered_size = size / self.view_scale
        self.items.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="{FONT}" font-size="{rendered_size:g}" font-weight="{weight}" text-anchor="{anchor}">{escape(str(value))}</text>')

    def lines(self, x, y, values, size=18, color=CONTENT, weight=400, line_h=27):
        for i, value in enumerate(values):
            self.text(x, y + i * line_h, value, size, color, weight)

    def button(self, x, y, w, label, fill=SURFACE_2, stroke=LINE, color=CONTENT, size=16, h=40):
        self.rect(x, y, w, h, fill, stroke, r=10)
        self.text(x + w / 2, y + h / 2 + size * .34, label, size, color, 600, "middle")

    def logo(self, x, y, size=44, label="⚡"):
        self.items.append(f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="12" fill="url(#brand)"/>')
        self.text(x + size / 2, y + size * .69, label, size * .58, "#ffffff", 700, "middle")

    def avatar(self, x, y, bot=True, size=38):
        fill = "#063b5d" if bot else "#172554"
        stroke = CYAN if bot else "#3b82f6"
        self.items.append(f'<circle cx="{x}" cy="{y}" r="{size/2}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        if bot:
            self.text(x, y + size * .22, "⚡", size * .5, "#ffffff", 700, "middle")
        else:
            self.items.append(f'<circle cx="{x}" cy="{y-5}" r="5" fill="#bfdbfe"/><path d="M{x-9} {y+10} Q{x} {y-1} {x+9} {y+10}" fill="#bfdbfe"/>')

    def save(self, filename: str):
        self.items.append("</g>")
        self.items.append("</svg>")
        (OUT / filename).write_text("\n".join(self.items) + "\n", encoding="utf-8")


def chat_header(svg: SVG):
    svg.rect(0, 0, W, 88, BG, BG, r=0, sw=0)
    svg.line(0, 87, W, 87, "#1f2937", 1)
    svg.logo(68, 24, 40)
    svg.text(122, 43, "UniMon • Soporte TI", 23, TEXT, 700)
    svg.text(122, 66, "Universidad Simón Bolívar · Asistente Virtual Oficial", 14, MUTED)
    svg.button(1330, 24, 205, "↻  Nueva conversación", fill="#111827", stroke="#263447", size=15, h=42)


def chat_shell(svg: SVG):
    # The public page uses .app-container { max-width: 1000px; width: 100%; }.
    svg.rect(300, 108, 1000, 754, SURFACE, "#263447", r=20, sw=1.7)
    svg.rect(301, 109, 998, 62, "#0c1423", "#0c1423", r=19, sw=0)
    svg.line(302, 171, 1298, 171, "#1f2937", 1)
    svg.rect(324, 121, 316, 38, "#111b2b", "#263447", r=19)
    svg.text(346, 146, "◉  Canales de Atención TI", 15, "#cbd5e1", 500)
    # Keep the chat's scroll area visibly distinct from its persistent composer.
    svg.rect(301, 172, 998, 568, "#0b1220", "#0b1220", r=0, sw=0)
    svg.line(302, 740, 1298, 740, "#1f2937", 1)
    svg.rect(324, 763, 952, 66, "#111827", "#334155", r=17, sw=1.5)
    svg.text(353, 804, "Escribe tu consulta o describe la falla...", 16, MUTED)
    svg.items.append('<circle cx="1251" cy="796" r="23" fill="#0284c7"/>')
    svg.items.append('<path d="M1242 796 L1260 788 L1254 805 L1250 798 Z" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linejoin="round"/>')


def chat_home():
    svg = SVG("Wireframe representativo del chat web UniMon en estado inicial")
    chat_header(svg)
    chat_shell(svg)
    svg.avatar(350, 245, True, 40)
    svg.rect(390, 204, 720, 198, SURFACE_2, "#29384a", r=16)
    svg.text(422, 247, "¡Hola! Soy UniMon", 22, TEXT, 700)
    svg.lines(422, 282, [
        "Tu asistente virtual de inteligencia artificial para soporte de TI",
        "de la Universidad Simón Bolívar.",
        "Estoy listo para ayudarte. Dime, ¿en qué te puedo colaborar hoy?",
    ], 18, CONTENT, 400, 30)
    svg.text(422, 375, "⚡ UniMon Unisimon • Soporte Conversacional Directo", 13, MUTED, 500)
    svg.save("01_chat_web.svg")


def chat_procedure():
    svg = SVG("Wireframe representativo de una consulta de trámite en el chat UniMon")
    chat_header(svg)
    chat_shell(svg)

    svg.avatar(350, 224, True, 36)
    svg.rect(386, 193, 640, 74, SURFACE_2, "#29384a", r=15)
    svg.text(412, 222, "¡Hola! Soy UniMon. ¿En qué te puedo colaborar hoy?", 16, CONTENT, 500)
    svg.text(412, 248, "⚡ UniMon Unisimon • Soporte Conversacional Directo", 12, MUTED)

    svg.avatar(1250, 326, False, 36)
    svg.rect(700, 287, 510, 72, BLUE, "#2563eb", r=15)
    svg.text(729, 331, "¿Cómo solicito un certificado de notas?", 17, "#ffffff", 500)

    svg.avatar(350, 440, True, 36)
    svg.rect(386, 386, 812, 246, SURFACE_2, "#29384a", r=15)
    svg.text(414, 427, "Orientación para tu trámite", 19, TEXT, 700)
    svg.lines(414, 462, [
        "Encontré una guía relacionada con trámites académicos. Revisa el",
        "documento institucional citado para consultar los requisitos y el",
        "canal de radicación vigente. Si me indicas tu perfil, puedo precisar",
        "la orientación disponible.",
    ], 17, CONTENT, 400, 26)
    svg.text(414, 558, "🤖 UniMon Nivel 1 • RAG • Ref: documento recuperado", 12, MUTED, 500)
    # These are the two quick replies used by the implemented RAG flow.
    svg.button(414, 576, 190, "✓  Sí, me funcionó", fill="#102b2a", stroke="#1c5c50", color="#a7f3d0", size=13, h=36)
    svg.button(616, 576, 210, "🎫  No, radicar ticket", fill="#17243a", stroke="#2c4770", color="#bfdbfe", size=13, h=36)
    svg.save("02_consulta_tramite.svg")


def admin_dashboard():
    # Scale the layout geometry to a tighter viewBox while retaining label size,
    # so the dense dashboard remains legible when printed in the report.
    svg = SVG("Wireframe representativo del panel administrativo UniMon", view_scale=.75)
    # Admin header mirrors app/static/admin.html and its three implemented tabs.
    svg.rect(0, 0, W, 74, "#0b1220", "#0b1220", r=0, sw=0)
    svg.line(0, 73, W, 73, "#263447", 1)
    svg.rect(50, 16, 42, 42, "#1d4ed8", "#1d4ed8", r=11, sw=0)
    svg.text(71, 45, "U", 24, "#ffffff", 800, "middle")
    svg.text(107, 34, "UniMon Admin Console", 21, TEXT, 700)
    svg.text(107, 55, "Universidad Simón Bolívar · Mesa de Ayuda TI", 13, MUTED)

    svg.rect(875, 19, 175, 34, "#10291f", "#24543b", r=17)
    svg.items.append('<circle cx="893" cy="36" r="5" fill="#34d399"/>')
    svg.text(906, 41, "Sistema Operativo", 13, "#bbf7d0", 600)
    svg.button(1062, 17, 105, "API Docs", fill="#111827", stroke="#334155", size=13, h=38)
    svg.button(1176, 17, 122, "Ir al Chat", fill="#111827", stroke="#334155", size=13, h=38)
    svg.button(1307, 17, 145, "↻  Actualizar", fill="#1d4ed8", stroke="#2563eb", color="#ffffff", size=13, h=38)

    # Tab bar: actual administration sections.
    svg.rect(52, 89, 1496, 50, "#101827", "#253247", r=11)
    svg.rect(60, 95, 405, 38, "#172a43", "#24496f", r=8)
    svg.text(262, 120, "▦  Métricas & Observabilidad", 16, "#bfdbfe", 700, "middle")
    svg.text(697, 120, "▤  Base de Conocimiento RAG", 15, MUTED, 600, "middle")
    svg.text(1187, 120, "⚡  Diagnóstico de Servidor", 15, MUTED, 600, "middle")

    # Time filters.
    svg.rect(100, 153, 1400, 78, SURFACE, "#263447", r=12)
    svg.text(122, 180, "Período:", 14, MUTED, 700)
    presets = [(210, 75, "Hoy", True), (293, 78, "Ayer", False), (379, 88, "7 Días", False), (473, 108, "Este Mes", False), (587, 116, "Histórico", False)]
    for x, width, label, active in presets:
        svg.button(x, 163, width, label, fill="#17375b" if active else "#111827", stroke="#2c5d92" if active else "#2d3748", color="#bfdbfe" if active else MUTED, size=13, h=32)
    svg.text(730, 180, "Personalizado:", 13, MUTED)
    svg.button(820, 163, 140, "dd/mm/aaaa", fill="#0b1220", stroke="#334155", color="#cbd5e1", size=12, h=32)
    svg.text(968, 184, "a", 13, MUTED)
    svg.button(992, 163, 140, "dd/mm/aaaa", fill="#0b1220", stroke="#334155", color="#cbd5e1", size=12, h=32)
    svg.button(1142, 163, 92, "⌕  Filtrar", fill="#111827", stroke="#334155", color=CONTENT, size=13, h=32)
    svg.text(1258, 181, "Mostrando: Hoy", 13, "#bbf7d0", 600)

    # Six KPI cards, arranged as the responsive dashboard does at a common desktop width.
    kpis = [
        (100, 246, "Consultas Totales", "0", "0 sesiones en el período", CYAN),
        (558, 246, "Resolución Nivel 1", "0%", "Autoservicio RAG resuelto", GREEN),
        (1016, 246, "Escalado a GLPI", "0%", "Tickets radicados en Mesa TI", AMBER),
        (100, 354, "Latencia Media", "0 ms", "Respuesta completa del asistente", CYAN),
        (558, 354, "Tokens LLM registrados", "0", "0 in / 0 out", PURPLE),
        (1016, 354, "Sesiones Auditadas", "0", "En período seleccionado", "#60a5fa"),
    ]
    for x, y, label, value, sub, accent in kpis:
        svg.rect(x, y, 442, 94, "#111b2b", "#263447", r=12)
        svg.rect(x, y, 4, 94, accent, accent, r=2, sw=0)
        svg.text(x + 22, y + 29, label, 15, MUTED, 600)
        svg.text(x + 22, y + 67, value, 28, TEXT, 700)
        svg.text(x + 205, y + 67, sub, 11, MUTED, 400)

    # Token/cost panel and supporting information visible below the KPI summary.
    svg.rect(100, 467, 1400, 115, SURFACE, "#3b3157", r=12)
    svg.text(124, 494, "Desglose de Tokens y Costo Estimado", 17, TEXT, 700)
    svg.text(1474, 494, "Proveedor configurado", 13, PURPLE, 600, "end")
    cost_items = [(124, "Entrada regular", "0 tokens", CYAN), (468, "Entrada en caché", "0 tokens", GREEN), (812, "Salida generada", "0 tokens", PURPLE), (1156, "Gasto estimado", "$0.0000 USD", AMBER)]
    for x, label, value, accent in cost_items:
        svg.rect(x, 508, 320, 55, "#121d2e", "#29384a", r=9)
        svg.text(x + 14, 530, label, 12, MUTED, 500)
        svg.text(x + 14, 552, value, 16, accent, 700)

    svg.rect(100, 601, 692, 236, SURFACE, "#263447", r=12)
    svg.text(124, 633, "Distribución de Consultas por Rol", 17, TEXT, 700)
    svg.line(124, 647, 768, 647, "#263447", 1)
    for i, role in enumerate(("Estudiante", "Profesor", "Administrativo", "General")):
        y = 681 + i * 34
        svg.text(127, y, role, 14, CONTENT)
        svg.rect(410, y - 14, 280, 9, "#1f2937", "#1f2937", r=5, sw=0)
        svg.rect(410, y - 14, 0, 9, CYAN, CYAN, r=5, sw=0)
        svg.text(768, y, "0", 13, MUTED, 500, "end")

    svg.rect(808, 601, 692, 236, SURFACE, "#263447", r=12)
    svg.text(832, 633, "Top 5 Documentos / Procedimientos", 17, TEXT, 700)
    svg.line(832, 647, 1476, 647, "#263447", 1)
    for i in range(5):
        y = 677 + i * 32
        svg.rect(834, y - 15, 24, 24, "#172a43", "#24496f", r=6)
        svg.text(846, y + 2, str(i + 1), 12, "#bfdbfe", 700, "middle")
        svg.text(872, y, "Documento consultado", 13, CONTENT, 500)
        svg.button(1388, y - 15, 90, "0 veces", fill="#111827", stroke="#29384a", color=MUTED, size=11, h=25)

    # Scrollbar indicates the admin dashboard continues with further audit panels.
    svg.rect(1575, 96, 7, 760, "#111827", "#111827", r=4, sw=0)
    svg.rect(1575, 106, 7, 312, "#475569", "#475569", r=4, sw=0)
    svg.save("03_panel_admin.svg")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    chat_home()
    chat_procedure()
    admin_dashboard()
    print(f"Generated three report wireframes in {OUT}")
