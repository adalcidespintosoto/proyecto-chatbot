from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from pathlib import Path
from copy import deepcopy

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'Informe_Practica_UniMon_Ajustado_a_Plantilla_UML_2026-10-30.docx'
OUTPUT = ROOT / 'Informe_Practica_UniMon_Ajustado_a_Plantilla_UML_2026-10-30_wireframes_QA.docx'
ASSETS = Path(__file__).resolve().parent


def replace_cell_text(cell, value):
    paragraph = cell.paragraphs[0]
    template_rpr = deepcopy(paragraph.runs[0]._r.rPr) if paragraph.runs and paragraph.runs[0]._r.rPr is not None else None
    paragraph.clear()
    run = paragraph.add_run(value)
    if template_rpr is not None:
        run._r.insert(0, template_rpr)
    for extra in cell.paragraphs[1:]:
        extra._element.getparent().remove(extra._element)


def main():
    doc = Document(REPORT)
    paragraphs = doc.paragraphs
    start = next(i for i, p in enumerate(paragraphs) if p.text.strip() == '5.4.2 Wireframes representativos')
    end = next(i for i, p in enumerate(paragraphs[start + 1:], start + 1) if p.text.strip() == '5.5 Diseño de Datos')
    section = paragraphs[start + 1:end]
    images = [p for p in section if p._p.xpath('.//a:blip')]
    if len(images) != 3:
        raise RuntimeError(f'Se esperaban tres imágenes en 5.4.2; se encontraron {len(images)}.')

    specs = [
        ('01_chat_web.png', 'Wireframe representativo del chat web UniMon en estado inicial.'),
        ('02_consulta_tramite.png', 'Wireframe representativo de una consulta de trámite con respuesta RAG, referencia y opciones rápidas.'),
        ('03_panel_admin.png', 'Wireframe representativo del panel administrativo UniMon con métricas y observabilidad.'),
    ]
    for paragraph, (filename, alt_text) in zip(images, specs):
        paragraph.clear()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_before = Pt(2)
        paragraph.paragraph_format.space_after = Pt(6)
        paragraph.paragraph_format.keep_together = True
        inline = paragraph.add_run().add_picture(str(ASSETS / filename), width=Inches(6.45))
        inline._inline.docPr.set('title', alt_text.split('.')[0])
        inline._inline.docPr.set('descr', alt_text)

    # Remove the empty spacer paragraphs left by the former ASCII blocks/photos.
    for paragraph in section:
        if paragraph not in images and not paragraph.text.strip() and not paragraph._p.xpath('.//a:blip'):
            if paragraph._p.xpath('.//w:br[@w:type="page"]') or paragraph._p.xpath('.//w:sectPr'):
                continue
            paragraph._element.getparent().remove(paragraph._element)

    # Keep each short label attached to the figure that follows it.
    remaining_paragraphs = doc.paragraphs
    start_p = next(p for p in remaining_paragraphs if p.text.strip() == '5.4.2 Wireframes representativos')
    labels = {'Chat web', 'Consulta de trámite no técnico', 'Panel /admin'}
    for p in remaining_paragraphs:
        if p.text.strip() in labels:
            p.paragraph_format.keep_with_next = True

    first_label = next(p for p in remaining_paragraphs if p.text.strip() == 'Chat web')
    note = first_label.insert_paragraph_before(
        'Las figuras representan el estado inicial del chat, una interacción de consulta con su respuesta referenciada y sus opciones rápidas, y el tablero de métricas del panel administrativo. Se elaboraron con base en las vistas codificadas en app/static/index.html y app/static/admin.html. El texto de respuesta y los valores métricos son ilustrativos; dependen de la consulta, las fuentes recuperadas y la telemetría disponible.'
    )
    note.style = doc.styles['Normal']
    note.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    note.paragraph_format.space_after = Pt(5)

    history_intro = next(p for p in doc.paragraphs if p.text.startswith('El historial sigue los apartados'))
    history_intro.text = history_intro.text.replace(
        '22 de octubre de 2026; cada jornada agrupa entre tres y cuatro puntos.',
        '30 de octubre de 2026; cada jornada agrupa entre dos y cuatro puntos.',
    )

    toc_wireframe = next(p for p in doc.paragraphs if p.text.strip() == '5.4.2 Wireframe')
    toc_wireframe.text = '5.4.2 Wireframes representativos'

    table_titles = (
        'Interfaz de Conversación (Chat Web)',
        'Flujo de Orientación para Trámite No Técnico',
        'Panel Administrativo y de Analítica (/admin)',
    )
    remove = []
    for table in doc.tables:
        content = ' '.join(cell.text for row in table.rows for cell in row.cells)
        if any(title in content for title in table_titles):
            remove.append(table._tbl)
    if len(remove) != 3:
        raise RuntimeError(f'Se esperaban tres tablas wireframe obsoletas; se encontraron {len(remove)}.')
    for element in remove:
        element.getparent().remove(element)

    history_rows = []
    for table in doc.tables:
        for row in table.rows:
            if row.cells and row.cells[0].text.strip() == 'R71':
                history_rows.append(row)
    if len(history_rows) != 1:
        raise RuntimeError(f'Se esperaba una fila R71 en el historial; se encontraron {len(history_rows)}.')
    row = history_rows[0]
    replace_cell_text(row.cells[2], '2.1 Referencias; 5.4.2 Wireframes; Anexo I')
    replace_cell_text(row.cells[3], 'Se agregó la referencia UML 2.5.1, se documentaron fuentes y criterios de las figuras y se recrearon las vistas de chat y administración con base en el código implementado.')

    doc.save(OUTPUT)
    print(f'Informe actualizado: {OUTPUT}')
    print(f'Tablas de wireframe retiradas: {len(remove)}; imágenes sustituidas: {len(images)}; notas de estructura nuevas: 0.')


if __name__ == '__main__':
    main()
