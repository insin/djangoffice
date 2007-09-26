# -*- coding: utf-8 -*-
from reportlab.platypus import *
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.rl_config import defaultPageSize
styles = getSampleStyleSheet()
PAGE_HEIGHT=defaultPageSize[1]
PAGE_WIDTH=defaultPageSize[0]

TITLE = 'Invoice'

def firstPage(canvas, doc):
    canvas.saveState()
    canvas.setFont('Times-Roman', 14)
    canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 20 * mm, 'Invoice')
    canvas.setFont('Times-Roman', 9)
    canvas.drawCentredString(PAGE_WIDTH / 2, 10 * mm, 'Page %d' % doc.page)
    canvas.restoreState()

def laterPages(canvas, doc):
    canvas.saveState()
    canvas.setFont('Times-Roman', 14)
    canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 20 * mm, 'Invoice')
    canvas.setFont('Times-Roman', 9)
    canvas.drawCentredString(PAGE_WIDTH / 2, 10 * mm, 'Page %d' % doc.page)
    canvas.restoreState()

tableStyle = TableStyle([
    ('FONT', (0, 0), (-1, -1), 'Times-Roman', 12),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('BOX', (0, 0), (-1, -1), 1.5, colors.black),
    ('LINEBELOW', (0,0), (-1, 0), 1.5, colors.black),
    ('LINEABOVE', (0,-1), (-1, -1), 1.5, colors.black),
    ('ALIGN', (0, -1), (0, -1), 'RIGHT'),
])

def go():
    doc = SimpleDocTemplate('invoice.pdf')
    elements = [
        Table([
            ['Task', 'Hours', 'Cost (£)'],
            ['Test Task 1', 66, 290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Test Task 1', 66, 1290.00],
            ['Test Task 2', 40, 1000.00],
            ['Total', 110, 2290.00],
        ], repeatRows=1, style=tableStyle,
        colWidths=(110 * mm, 40 * mm, 40 * mm)),
    ]
    doc.build(elements, onFirstPage=firstPage, onLaterPages=laterPages)

go()
