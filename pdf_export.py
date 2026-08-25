"""Renders the Client Report to a polished, letterhead-style PDF."""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Table, TableStyle, Paragraph, Spacer,
    Image as RLImage, NextPageTemplate, FrameBreak, KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from utils import fmt_id, fmt_pct

BRAND_DARK = colors.HexColor("#153327")
BRAND = colors.HexColor("#2F6B48")
CREAM = colors.HexColor("#E9E6C9")
KHAKI = colors.HexColor("#C9C6A2")
TEXT = colors.HexColor("#1B241D")
TEXT_MUTED = colors.HexColor("#6B7568")
CARD_BG = colors.HexColor("#F4F5EF")
BORDER = colors.HexColor("#CDD3BF")
GOOD = colors.HexColor("#1F6A3F")
BAD = colors.HexColor("#8C2E26")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("H1White", parent=styles["Heading1"], textColor=colors.white, fontSize=18, leading=22))
styles.add(ParagraphStyle("SubWhite", parent=styles["Normal"], textColor=CREAM, fontSize=9.5, leading=13))
styles.add(ParagraphStyle("SectionHead", parent=styles["Heading2"], textColor=BRAND_DARK, fontSize=12.5, spaceBefore=10, spaceAfter=6))
styles.add(ParagraphStyle("CardLabel", parent=styles["Normal"], textColor=BRAND_DARK, fontSize=8.5, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("CardValue", parent=styles["Normal"], textColor=TEXT, fontSize=15, leading=18, fontName="Helvetica-Bold", spaceBefore=2))
styles.add(ParagraphStyle("CardDelta", parent=styles["Normal"], textColor=TEXT_MUTED, fontSize=8, spaceBefore=2))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], textColor=TEXT, fontSize=9.3, leading=13.5))
styles.add(ParagraphStyle("BodySmall", parent=styles["Normal"], textColor=TEXT_MUTED, fontSize=8, leading=11))
styles.add(ParagraphStyle("Footer", parent=styles["Normal"], textColor=TEXT_MUTED, fontSize=7.5, alignment=TA_CENTER))


def _delta_text(delta, invert=False):
    if delta is None:
        return "vs. bulan lalu: n/a"
    good = (delta <= 0) if invert else (delta >= 0)
    arrow = "\u25b2" if delta >= 0 else "\u25bc"
    color = "#1F6A3F" if good else "#8C2E26"
    return f'<font color="{color}">{arrow} {fmt_id(abs(delta), 1)}%</font> vs. bulan lalu'


def _kpi_card(label, value, delta_html, width_mm=40):
    inner = Table(
        [[Paragraph(label, styles["CardLabel"])],
         [Paragraph(value, styles["CardValue"])],
         [Paragraph(delta_html, styles["CardDelta"])]],
        colWidths=[width_mm * mm],
    )
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
    ]))
    return inner


def _kpi_row(cards, col_count):
    width_each = 172 / col_count
    t = Table([cards], colWidths=[width_each * mm] * col_count)
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _bullets(items):
    rows = []
    for i, text in enumerate(items, start=1):
        rows.append(Paragraph(f'<b>{i}.</b>&nbsp;&nbsp;{text}', styles["Body"]))
        rows.append(Spacer(1, 4))
    return rows


def build_client_report_pdf(
    *, company, month_label, year_label, kpis, deltas, sust_deltas,
    pie_png, bar_png, achievements, critical_issues,
) -> bytes:
    buf = io.BytesIO()
    doc = BaseDocTemplate(buf, pagesize=A4, topMargin=0, bottomMargin=14 * mm,
                           leftMargin=14 * mm, rightMargin=14 * mm)
    frame = Frame(14 * mm, 14 * mm, doc.width, doc.height - 4 * mm, id="main")
    doc.addPageTemplates([PageTemplate(id="report", frames=[frame], onPage=_draw_footer)])

    story = []

    # ---- Header banner ----
    header_tbl = Table(
        [[Paragraph("Monthly Performance Report", styles["H1White"]),
          Paragraph("PT Akartha<br/>Energi Baru", ParagraphStyle("logo", parent=styles["Normal"], textColor=colors.white, fontSize=9.5, leading=12, fontName="Helvetica-Bold", alignment=TA_CENTER))],
         [Paragraph(f"Bulan: <b>{month_label}</b> &nbsp;&nbsp; Tahun: <b>{year_label}</b> &nbsp;&nbsp; Client: <b>{company}</b>", styles["SubWhite"]), ""]],
        colWidths=[140 * mm, 32 * mm], rowHeights=[12 * mm, 8 * mm],
    )
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_DARK),
        ("SPAN", (1, 0), (1, 1)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 1), "CENTER"),
        ("LEFTPADDING", (0, 0), (0, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 10))

    # ---- Matriks Ketercapaian ----
    story.append(Paragraph("Matriks Ketercapaian", styles["SectionHead"]))
    story.append(_hr())
    story.append(Spacer(1, 4))

    cards = [
        _kpi_card("LISTRIK TERSALURKAN", f"{fmt_id(kpis['listrik_tersalurkan_kwh'])} kWh", _delta_text(deltas.get("listrik_tersalurkan_kwh")), width_mm=38),
        _kpi_card("PERSENTASE ENERGI BERSIH", fmt_pct(kpis['ref_pct'], 2), _delta_text(deltas.get("ref_pct")), width_mm=38),
        _kpi_card("JUMLAH SOLAR", f"{fmt_id(kpis['jumlah_solar_l'])} Liter", _delta_text(deltas.get("jumlah_solar_l"), invert=True), width_mm=38),
        _kpi_card("AVAILABILITY", fmt_pct(kpis['availability_pct'], 2), _delta_text(deltas.get("availability_pct")), width_mm=38),
    ]
    story.append(_kpi_row(cards, 4))
    story.append(Spacer(1, 12))

    # ---- Charts ----
    pie_img = RLImage(pie_png, width=78 * mm, height=63 * mm)
    bar_img = RLImage(bar_png, width=94 * mm, height=63 * mm)
    chart_tbl = Table([[bar_img, pie_img]], colWidths=[98 * mm, 82 * mm])
    chart_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(chart_tbl)
    story.append(Spacer(1, 10))

    # ---- Sustainability KPI row ----
    story.append(Paragraph("Sustainability Impact", styles["SectionHead"]))
    story.append(_hr())
    story.append(Spacer(1, 4))
    sust_cards = [
        _kpi_card("CO2 AVOIDED", f"{fmt_id(kpis['co2_avoided_ton'], 1)} T CO2", _delta_text(sust_deltas.get("co2_avoided_ton"), invert=False), width_mm=53),
        _kpi_card("EQUIVALENT TREES PLANTED", f"{fmt_id(kpis['trees_equivalent'])} Trees", _delta_text(sust_deltas.get("trees_equivalent"), invert=False), width_mm=53),
        _kpi_card("DIESEL SAVINGS", f"{fmt_id(kpis['diesel_savings_l'])} Liter", _delta_text(sust_deltas.get("diesel_savings_l"), invert=False), width_mm=53),
    ]
    story.append(_kpi_row(sust_cards, 3))
    story.append(Spacer(1, 14))

    # ---- Key Achievements / Critical Issue, two columns ----
    ach_flow = [Paragraph("Key Achievements", styles["SectionHead"]), _hr(), Spacer(1, 4)] + _bullets(achievements)
    if critical_issues:
        issue_rows = [Paragraph(f'<font color="#B9812C"><b>{sev}</b></font> &nbsp; {desc}', styles["Body"]) for sev, desc in critical_issues]
        issue_flow = [Paragraph("Critical Issue", styles["SectionHead"]), _hr(), Spacer(1, 4)]
        for r in issue_rows:
            issue_flow.append(r)
            issue_flow.append(Spacer(1, 4))
    else:
        issue_flow = [Paragraph("Critical Issue", styles["SectionHead"]), _hr(), Spacer(1, 4),
                      Paragraph("--", styles["BodySmall"])]

    two_col = Table([[ach_flow, issue_flow]], colWidths=[108 * mm, 62 * mm])
    two_col.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 10)]))
    story.append(two_col)

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


def _hr():
    t = Table([[""]], colWidths=[172 * mm], rowHeights=[1])
    t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 1, BORDER)]))
    return t


def _draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawCentredString(A4[0] / 2, 8 * mm, "Confidential — Generated by Akartha O&M BI Dashboard (MVP)")
    canvas.restoreState()
