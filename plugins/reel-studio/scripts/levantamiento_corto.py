"""
Levantamiento express (1 hoja, 5 preguntas) + autorizaciones de imagen (2 hojas).

Uso:
  python levantamiento_corto.py "<Proyecto · Lugar>" [link_carpeta] [carpeta_salida]
"""
import os
import sys
from io import BytesIO

import qrcode
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

PROYECTO = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else "Proyecto"
LINK = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None
OUT_DIR = os.path.expanduser(sys.argv[3]) if len(sys.argv) > 3 else os.path.expanduser("~/Downloads")
SLUG = "".join(c if c.isalnum() else "_" for c in PROYECTO.split("·")[0].strip()).strip("_")

INK = colors.HexColor("#1F2430")
MUTED = colors.HexColor("#6B7280")
LINE = colors.HexColor("#C9CDD4")
SOFT = colors.HexColor("#F3F4F6")

H1 = ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=INK)
SUB = ParagraphStyle("SUB", fontName="Helvetica", fontSize=9, leading=12, textColor=MUTED)
Q = ParagraphStyle("Q", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=INK)
P = ParagraphStyle("P", fontName="Helvetica", fontSize=9.5, leading=13, textColor=INK)
SMALL = ParagraphStyle("SMALL", fontName="Helvetica", fontSize=7.5, leading=10, textColor=MUTED)
CENTER = ParagraphStyle("CENTER", parent=P, alignment=TA_CENTER, fontSize=8.5)

BOX_PNG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "box.png")
BOX = f'<img src="{BOX_PNG}" width="9" height="9" valign="-1"/>'
W = A4[0] - 30 * mm


def opts(*items):
    return Paragraph("&nbsp;&nbsp;&nbsp;".join(f"{BOX} {i}" for i in items), P)


def line(label=""):
    return Paragraph(f"{label}______________________________________________________________", P)


def qr():
    if not LINK:
        return Paragraph("Código QR<br/>de la carpeta<br/>(pegar aquí)", CENTER)
    img = qrcode.make(LINK, box_size=8, border=1)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return Image(buf, width=30 * mm, height=30 * mm)


def question(n, title, body, right=None):
    """Bloque de pregunta: número | pregunta + respuesta | (opcional) QR"""
    cells = [[Paragraph(f'<font size="20" color="#9CA3AF"><b>{n}</b></font>', P), [Paragraph(title, Q), Spacer(1, 4)] + body]]
    widths = [12 * mm, W - 12 * mm]
    if right is not None:
        cells[0].append(right)
        widths = [12 * mm, W - 12 * mm - 36 * mm, 36 * mm]
    t = Table(cells, colWidths=widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("VALIGN", (-1, 0), (-1, 0), "MIDDLE") if right is not None else ("VALIGN", (0, 0), (0, 0), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
    ] + ([("BOX", (-1, 0), (-1, 0), 0.6, INK), ("ALIGN", (-1, 0), (-1, 0), "CENTER")] if right is not None else [])))
    return t


hex_row = Table(
    [[Paragraph(f"{c} #________", P) for c in ["Principal", "Secundario", "Acento"]]],
    colWidths=[(W - 48 * mm - 12 * mm) / 3] * 3,
)
hex_row.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0)]))

sheet = [
    Paragraph("Levantamiento express de rodaje", H1),
    Paragraph(f"{PROYECTO} · Fecha: ____________ · Responsable cliente: ______________________________", SUB),
    Spacer(1, 6),
    question(
        1,
        "¿Ya subieron logo, colores y tipografía oficiales a la carpeta?",
        [
            opts("Sí, completo", "Parcial", "No"),
            Spacer(1, 5),
            hex_row,
            Spacer(1, 3),
            Paragraph("Logo en PNG transparente o SVG · incluir logotipo horizontal y elementos gráficos oficiales si existen.", SMALL),
        ],
        right=qr(),
    ),
    question(
        2,
        "¿Cómo se escriben exactamente los nombres y la frase de cierre?",
        [
            line("Nombre y cargo: "),
            Spacer(1, 5),
            line("Marca / negocio: "),
            Spacer(1, 5),
            line("Frase de cierre / slogan: "),
        ],
    ),
    question(
        3,
        "¿Qué música usamos?",
        [
            opts("Jingle / música oficial (subir a la carpeta)", "Música libre de derechos"),
            Spacer(1, 4),
            opts("Emotiva y sobria", "Energética", "Elegante / lifestyle"),
            Spacer(1, 4),
            line("Referencia o lo que NO quieren: "),
            Spacer(1, 3),
            Paragraph("Música comercial con derechos (canciones conocidas) puede bloquear el video en redes.", SMALL),
        ],
    ),
    question(
        4,
        "¿Graban en vertical 9:16 o en horizontal 4K para recortar?",
        [
            opts("Vertical 9:16", "Horizontal 4K (recomendado)"),
            Spacer(1, 4),
            opts("30 fps", "25 fps", "24 fps"),
            Spacer(1, 3),
            Paragraph("Todas las cámaras igual. El 4K horizontal da margen para encuadrar el 9:16 y sirve para otros formatos.", SMALL),
        ],
    ),
    question(
        5,
        "¿Están listas las autorizaciones de imagen?",
        [
            opts("Adultos", "Menores (firma del representante)", "Clientes del local"),
            Spacer(1, 3),
            Paragraph("Firmar antes de grabar a cada persona. Formularios en el archivo «Autorizaciones de imagen».", SMALL),
        ],
    ),
    question(
        6,
        "¿Quién aprueba los cortes (incluida la validación normativa) y en cuánto tiempo responde?",
        [
            line("Aprobador: "),
            Spacer(1, 5),
            opts("24 h", "48 h", "Máx. 2 rondas de cambios"),
            Spacer(1, 3),
            Paragraph("Comentarios siempre con el segundo exacto del video (ej.: «0:23 cambiar…»).", SMALL),
        ],
    ),
]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(MUTED)
    canvas.drawString(15 * mm, 8 * mm, PROYECTO)
    canvas.restoreState()


def build(name, story):
    path = os.path.join(OUT_DIR, name)
    SimpleDocTemplate(path, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=13 * mm, bottomMargin=13 * mm,
                      title=name).build(story, onFirstPage=footer, onLaterPages=footer)
    print("OK", path)


build(f"Levantamiento_Express_{SLUG}.pdf", sheet)

# ─── Autorizaciones (2 hojas) ───────────────────────────────────────────────
NOTE = Paragraph("Plantilla referencial: validar con asesoría legal (protección de datos y normativa electoral).", SMALL)
TXT = ("autorizan de forma libre, voluntaria y gratuita grabar, fotografiar, editar y publicar su imagen y voz en las piezas "
       f"de comunicación del proyecto «{PROYECTO}», en redes sociales y medios digitales, durante su período de difusión. "
       "Pueden pedir por escrito que no se use su imagen en nuevas publicaciones.")


def sign_table(header, n, widths, h=9.5 * mm):
    t = Table([header] + [[str(i)] + [""] * (len(header) - 1) for i in range(1, n + 1)], colWidths=widths,
              rowHeights=[7 * mm] + [h] * n)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("BACKGROUND", (0, 0), (-1, 0), SOFT),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.5),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


auth = [
    Paragraph("Autorización de imagen y voz · Mayores de edad", H1),
    NOTE,
    Spacer(1, 5),
    Paragraph("Las personas firmantes " + TXT, P),
    Spacer(1, 4),
    Paragraph("Lugar: ____________________________   Fecha: ______________", P),
    Spacer(1, 6),
    sign_table(["#", "Nombre completo", "Cédula", "Teléfono", "Firma"], 20, [8 * mm, 64 * mm, 30 * mm, 30 * mm, W - 132 * mm]),
    PageBreak(),
    Paragraph("Autorización de imagen y voz · Menores de edad", H1),
    NOTE,
    Spacer(1, 5),
    Paragraph("Los representantes legales firmantes, en nombre del menor indicado, " + TXT, P),
    Spacer(1, 4),
    Paragraph("Lugar: ____________________________   Fecha: ______________", P),
    Spacer(1, 6),
    sign_table(["#", "Nombre del menor", "Edad", "Representante y parentesco", "Cédula repr.", "Firma repr."], 14,
               [8 * mm, 46 * mm, 12 * mm, 50 * mm, 26 * mm, W - 142 * mm], h=12 * mm),
]
build(f"Autorizaciones_Imagen_{SLUG}.pdf", auth)
