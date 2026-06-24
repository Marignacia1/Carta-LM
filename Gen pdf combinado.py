from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from datetime import date, timedelta
import os

# ── CONFIGURACIÓN DE COLORES Y ESTILOS ──────────────────────────────
AZUL        = colors.HexColor('#1e4d8c')
AZUL_TABLA  = colors.HexColor('#b8cce4')
AZUL_TEXTO  = colors.HexColor('#0c447c')
NEGRO       = colors.black
BLANCO      = colors.white
ROJO        = colors.HexColor('#a32d2d')
GRIS        = colors.HexColor('#cccccc')
GRIS_CLARO  = colors.HexColor('#f5f8fd')

MESES = ['enero','febrero','marzo','abril','mayo','junio',
         'julio','agosto','septiembre','octubre','noviembre','diciembre']

def fecha_larga(d):
    return f"{d.day:02d} de {MESES[d.month-1]} de {d.year}"

def dias_habiles(n):
    d = date.today()
    c = 0
    while c < n:
        d += timedelta(days=1)
        if d.weekday() < 5:
            c += 1
    return d

def build_pdf(funcionario, firma_cfg, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    hoy     = date.today()
    plazo   = dias_habiles(5)

    # ── ESTILOS ──────────────────────────────────────────────────────────
    def s(name, **kw):
        defaults = dict(fontName='Helvetica', fontSize=10, textColor=NEGRO,
                        leading=14, spaceAfter=6)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    sN   = s('n')
    sNJ  = s('nj', alignment=TA_JUSTIFY)
    sNB  = s('nb', fontName='Helvetica-Bold')
    sR   = s('r', alignment=TA_RIGHT)
    sSec = s('sec', fontName='Helvetica-Bold', fontSize=11,
              textColor=BLANCO, spaceAfter=0)
    sHC  = s('hc', fontName='Helvetica-Bold', fontSize=9,
              textColor=BLANCO, alignment=TA_CENTER, leading=12)
    sCC  = s('cc', fontSize=9, alignment=TA_CENTER, leading=12)
    sCL  = s('cl', fontSize=9, alignment=TA_LEFT,   leading=12)
    sCB  = s('cb', fontName='Helvetica-Bold', fontSize=9,
              alignment=TA_CENTER, leading=12)
    sPie = s('pie', fontSize=9, textColor=AZUL, alignment=TA_CENTER, leading=13)

    story = []

    # ════════════════════════════════════════════════════════════════════
    # PÁGINA 1 — CARTA
    # ════════════════════════════════════════════════════════════════════

    story.append(Paragraph(fecha_larga(hoy), sR))
    story.append(Spacer(1, 14))

    story.append(Paragraph(f"Estimado/a <b>{funcionario['nombre']}</b>,", sN))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        f"Junto con saludar, se le notifica que a día de hoy <b>{fecha_larga(hoy)}</b>, "
        "según revisión de antecedentes, se registran licencia(s) médica(s) con estado "
        "<b>rechazado y/o reducido</b>, conforme al siguiente detalle:",
        sNJ))
    story.append(Spacer(1, 8))

    # Tabla de licencias
    th = [
        Paragraph('N° Licencia',  sHC),
        Paragraph('Fecha Inicio', sHC),
        Paragraph('Fecha Término',sHC),
        Paragraph('Días',         sHC),
        Paragraph('Resolución',   sHC),
    ]
    rows = [th]
    for l in funcionario['licencias']:
        sRes = s('res', fontSize=9, fontName='Helvetica-Bold',
                 textColor=ROJO, alignment=TA_CENTER, leading=12)
        rows.append([
            Paragraph(l['nlic'], sCC),
            Paragraph(l['fi'],   sCC),
            Paragraph(l['ft'],   sCC),
            Paragraph(l['dias'], sCC),
            Paragraph(l['res'],  sRes),
        ])

    col_w = [3.5*cm, 3.5*cm, 3.5*cm, 2*cm, 4*cm]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  AZUL),
        ('GRID',          (0,0), (-1,-1), 0.5, NEGRO),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [BLANCO, GRIS_CLARO]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        f"Se solicita revisar y regularizar su situación a la brevedad. "
        f"A contar de hoy, usted tiene <b>5 días hábiles</b> para presentar "
        f"Recurso de Reposición ante COMPIN, con fecha límite el "
        f"<b>{fecha_larga(plazo)}</b>.",
        sNJ))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "Se adjunta archivo con información respecto de apelación, plazos y normativa vigente.",
        sNJ))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        f"Para consultas o remisión de antecedentes, favor comunicarse al correo "
        f"<b>{firma_cfg['mail']}</b>.",
        sNJ))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Saludos cordiales,", sN))
    story.append(Spacer(1, 28))

    story.append(Paragraph(f"<b>{firma_cfg['nombre']}</b>", sN))
    story.append(Paragraph(firma_cfg['cargo'], sN))
    story.append(Paragraph(firma_cfg['inst'],  sN))
    story.append(Paragraph(f"<b>{firma_cfg['mail']}</b>",
                            s('fm', fontSize=10, textColor=AZUL)))

    # ════════════════════════════════════════════════════════════════════
    # PÁGINA 2 — INFORMACIÓN RECURSOS Y PLAZOS
    # ════════════════════════════════════════════════════════════════════
    story.append(PageBreak())

    def sec_header(num, titulo):
        data = [[Paragraph(f"{num}. {titulo}", sSec)]]
        t = Table(data, colWidths=['100%'])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0), (-1,-1), AZUL),
            ('TOPPADDING',    (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LEFTPADDING',   (0,0), (-1,-1), 8),
        ]))
        return t

    story.append(Paragraph('LICENCIAS MÉDICAS', s('t2', fontName='Helvetica-Bold',
                             fontSize=14, textColor=AZUL, alignment=TA_CENTER, spaceAfter=2)))
    story.append(Paragraph('DESAM — Departamento de Salud Municipal',
                             s('s2', fontSize=10, textColor=AZUL, alignment=TA_CENTER, spaceAfter=6)))
    story.append(HRFlowable(width='100%', thickness=2, color=AZUL, spaceAfter=12))

    story.append(sec_header(1, 'RECURSOS DISPONIBLES PARA GESTIÓN'))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        '<b>1°.</b> Usted puede presentar un <b>Recurso de Reposición</b> respecto de su licencia médica '
        'rechazada o reducida en la plataforma <b>www.milicenciamedica.cl</b>.', sNJ))
    story.append(Paragraph(
        '<b>2°.</b> En caso de que dicho recurso sea rechazado, podrá interponer un <b>Recurso de Apelación</b> '
        'ante la Superintendencia de Seguridad Social (SUSESO), disponible en <b>www.suseso.cl</b>.', sNJ))
    story.append(Paragraph(
        'Para fines administrativos, deberá remitir copia del formulario que acredite estar en trámite de '
        'reposición o apelación al correo <b>asistenciaylicenciasmedicas@saludpm.cl</b>, dentro de los plazos '
        'establecidos, a fin de evitar que se proceda al descuento de su remuneración.', sNJ))
    story.append(Spacer(1, 10))

    story.append(sec_header(2, 'PLAZOS Y ENTIDADES COMPETENTES'))
    story.append(Spacer(1, 8))

    plazos_data = [
        [Paragraph('SOLICITUD',sHC), Paragraph('ENTIDAD',sHC),
         Paragraph('FONASA',sHC),    Paragraph('ISAPRE',sHC)],
        [Paragraph('RECURSO DE\nREPOSICIÓN',sCB),
         Paragraph('COMPIN\n(Comisión de Medicina Preventiva e Invalidez)\nwww.milicenciamedica.cl\nFONO: 6003607777',sCL),
         Paragraph('5 DÍAS\nHÁBILES',sCB), Paragraph('15 DÍAS\nHÁBILES',sCB)],
        [Paragraph('',sCC),
         Paragraph('PLAZOS DESDE LA NOTIFICACIÓN',sCB),
         Paragraph('',sCC), Paragraph('',sCC)],
        [Paragraph('RECURSO DE\nAPELACIÓN',sCB),
         Paragraph('SUSESO\n(Superintendencia de Seguridad Social)\nwww.suseso.cl\nFONO: 226204500',sCL),
         Paragraph('6 MESES',sCB), Paragraph('6 MESES',sCB)],
    ]
    tpl = Table(plazos_data, colWidths=[3.2*cm, 7.3*cm, 2.8*cm, 2.8*cm], repeatRows=1)
    tpl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  AZUL),
        ('BACKGROUND',    (1,2), (3,2),   AZUL_TABLA),
        ('SPAN',          (1,2), (3,2)),
        ('GRID',          (0,0), (-1,-1), 0.5, NEGRO),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [BLANCO, GRIS_CLARO]),
    ]))
    story.append(tpl)
    story.append(Spacer(1, 10))

    story.append(sec_header(3, 'CONSIDERACIONES LEGALES Y ADMINISTRATIVAS'))
    story.append(Spacer(1, 8))

    sItem = s('it', fontSize=9.5, alignment=TA_JUSTIFY, leading=14,
               leftIndent=10, spaceAfter=5)
    sItemB = s('itb', fontSize=9.5, alignment=TA_JUSTIFY, leading=14,
                leftIndent=22, spaceAfter=4)

    items_principales = [
        'La ISAPRE o la COMPIN notifican el estado de las licencias médicas mediante <b>carta certificada o correo electrónico</b>.',
        'La presentación fuera de plazo habilita a la entidad competente para rechazarlas, salvo acreditación de fuerza mayor o caso fortuito, siempre que la presentación se realice durante la vigencia de la licencia.',
        'El <b>artículo 63 del Decreto N° 3 de 1984</b> del Ministerio de Salud, establece la obligación de devolver los estipendios indebidamente percibidos en caso de <b>RECHAZO o REDUCCIÓN</b>.',
        'La jurisprudencia de la <b>Contraloría General de la República</b> (Dictámenes N°s 24.790/2007, 43.760/2015 y 56.059/2016, entre otros) dispone que:',
    ]
    for i, item in enumerate(items_principales, 1):
        story.append(Paragraph(f'{i}. {item}', sItem))

    subitems = [
        'Las ausencias derivadas de licencias médicas rechazadas o reducidas se consideran <b>inasistencias injustificadas</b>.',
        'Procede el <b>descuento de remuneraciones</b>, o la devolución de lo indebidamente pagado.',
        'El descuento solo puede efectuarse una vez que la resolución de rechazo sea <b>ratificada por COMPIN</b>, o vencido el plazo de reclamación correspondiente.',
    ]
    for sub in subitems:
        story.append(Paragraph(f'• {sub}', sItemB))

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width='100%', thickness=1, color=GRIS, spaceAfter=6))
    story.append(Paragraph(
        'Para consultas o remisión de antecedentes: <b>asistenciaylicenciasmedicas@saludpm.cl</b>', sPie))

    doc.build(story)
    print(f"PDF generado: {output_path}")

# ── EJECUCIÓN SEGURA EN WINDOWS ──────────────────────────────────────
if __name__ == '__main__':
    funcionario_test = {
        'nombre': 'MOREIRA ASENJO DEISY',
        'rut': '16047640-0',
        'licencias': [
            {'nlic':'20382371','fi':'13/01/2025','ft':'19/01/2025','dias':'7','res':'RECHAZADA'},
            {'nlic':'113306957','fi':'20/01/2025','ft':'18/02/2025','dias':'30','res':'RECHAZADA'},
            {'nlic':'20665049','fi':'19/02/2025','ft':'20/03/2025','dias':'30','res':'RECHAZADA'},
        ]
    }
    firma = {
        'nombre': 'Nombre Apellido',
        'cargo':  'Encargado/a de Licencias Médicas',
        'inst':   'DESAM — Departamento de Salud Municipal',
        'mail':   'asistenciaylicenciasmedicas@saludpm.cl',
    }

    # Ruta segura en el escritorio del usuario actual para evitar errores
    ruta_escritorio = os.path.join(os.path.expanduser("~"), "Desktop", "carta_MOREIRA_ASENJO.pdf")
    
    try:
        build_pdf(funcionario_test, firma, ruta_escritorio)
        print(f"Éxito: PDF generado en: {ruta_escritorio}")
    except PermissionError:
        print("ERROR: El archivo PDF está abierto. Por favor, ciérralo antes de ejecutar el script.")
    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")