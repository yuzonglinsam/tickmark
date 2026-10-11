"""Single-page, source-linked English credit memo export."""
from __future__ import annotations

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

from .disclosures import Passage
from .memo import Memo
from .metrics import calculate
from .models import Snapshot
from .scoring import score

NAVY = colors.HexColor("#142C4B")
TEAL = colors.HexColor("#167C80")
MUTED = colors.HexColor("#657587")
PALE = colors.HexColor("#F5F7FA")
WIDTH, HEIGHT = 612, 792


def _amount(value: float | None, unit: str) -> str:
    if value is None:
        return "N/A"
    if unit == "x":
        return f"{value:.2f}x"
    if unit == "ratio":
        return f"{value * 100:.1f}%"
    scale = 1_000_000_000 if abs(value) >= 1_000_000_000 else 1_000_000
    suffix = "bn" if scale == 1_000_000_000 else "m"
    return f"{value / scale:,.2f} {suffix}"


def render_pdf(snapshot: Snapshot, memo: Memo, passages: tuple[Passage, ...],
               issuer_name: str) -> bytes:
    filing_urls = {p.accession: p.url.split('#')[0] for p in passages}
    source_urls = {source.evidence_id: filing_urls.get(source.accession, source.url.split('#')[0])
                   for fact in snapshot.facts.values() for source in fact.sources}
    source_urls.update({p.evidence_id: p.url.split('#')[0] for p in passages})
    used = {evidence_id for claims in memo.sections.values() for claim in claims
            for evidence_id in claim.evidence_ids}
    used.update(source.evidence_id for fact in snapshot.facts.values() for source in fact.sources)
    if not used or not used <= source_urls.keys():
        raise ValueError("Memo references lack exportable source links")
    url_index = {url: number for number, url in enumerate(sorted({source_urls[e] for e in used}), 1)}
    if len(url_index) > 12:
        raise ValueError("Too many separate filing links for a readable one-page memo")

    stream = BytesIO()
    pdf = canvas.Canvas(stream, pagesize=(WIDTH, HEIGHT), pageCompression=1)
    pdf.setTitle(f"{issuer_name} | Credit research memo")
    pdf.setAuthor("AI Credit Research Workbench")
    pdf.setFillColor(PALE)
    pdf.rect(0, HEIGHT - 83, WIDTH, 83, stroke=0, fill=1)
    pdf.setFillColor(TEAL)
    pdf.rect(42, HEIGHT - 50, 3, 21, stroke=0, fill=1)
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 16)
    title = issuer_name[:48]
    pdf.drawString(52, HEIGHT - 44, title)
    pdf.setFont("Helvetica", 9)
    pdf.setFillColor(MUTED)
    pdf.drawString(42, HEIGHT - 68,
                   f"{snapshot.ticker}  |  {snapshot.flow_period.basis.upper()} through "
                   f"{snapshot.flow_period.end}  |  As of {snapshot.as_of}")

    result = calculate(snapshot)
    health = score(snapshot)
    pdf.setStrokeColor(colors.HexColor("#D7E0E7"))
    pdf.line(42, 696, 570, 696)
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(42, 680, "FINANCIAL PROFILE")
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(MUTED)
    pdf.drawRightString(570, 680, f"{snapshot.currency} | reported units, scaled for display")
    rows = (("Revenue", "revenue"), ("Operating EBIT proxy", "operating_income"),
            ("EBITDA proxy", "ebitda_proxy"), ("Operating cash flow", "operating_cash_flow"),
            ("Free cash flow", "fcf"), ("Gross debt", "debt"),
            ("Gross leverage", "gross_leverage"), ("Interest coverage", "interest_coverage"))
    for i, (label, key) in enumerate(rows):
        x = 42 if i < 4 else 314
        y = 659 - (i % 4) * 18
        if i % 2 == 0:
            pdf.setFillColor(PALE)
            pdf.rect(x - 4, y - 4, 260, 16, stroke=0, fill=1)
        pdf.setFillColor(NAVY)
        pdf.setFont("Helvetica", 8.5)
        pdf.drawString(x, y, label)
        pdf.setFont("Helvetica-Bold", 8.5)
        pdf.drawRightString(x + 247, y, _amount(result[key].value, result[key].unit))

    pdf.setFillColor(TEAL)
    pdf.setFont("Helvetica-Bold", 9)
    score_text = (f"SCREENING SCORE  {health.value:.1f} / 100  |  {health.band}"
                  if health.value is not None else
                  f"SCREENING SCORE  N/A  |  coverage {health.coverage}%  |  possible {health.lower_bound:.1f}-{health.upper_bound:.1f}")
    pdf.drawString(42, 574, score_text)
    pdf.setFont("Helvetica", 7.5)
    pdf.setFillColor(MUTED)
    pdf.drawString(42, 562, "Uncalibrated screening heuristic; not a rating, default probability or investment recommendation.")
    pdf.setFont('Helvetica', 7)
    pdf.drawString(42, 540, "EBITDA uses a D&A scope proxy. Debt includes verified disposal-group borrowings where reported; gaps stay N/A.")
    pdf.line(42, 551, 570, 551)

    body_style = ParagraphStyle("body", fontName="Helvetica", fontSize=8.2,
                                leading=11.2, textColor=NAVY, alignment=TA_LEFT,
                                spaceAfter=0, allowWidows=0, allowOrphans=0)
    sections = (("CREDIT STRENGTHS", "credit_strengths"),
                ("KEY RISKS", "key_risks"),
                ("DEBT SERVICING CAPACITY", "debt_servicing_capacity"),
                ("OVERALL CREDIT VIEW", "overall_credit_view"))
    for column, part in enumerate((sections[:2], sections[2:])):
        x = 42 + column * 272
        y = 521
        for title, key in part:
            pdf.setFillColor(TEAL)
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(x, y, title)
            y -= 13
            for claim in memo.sections[key]:
                nums = sorted({url_index[source_urls[e]] for e in claim.evidence_ids})
                refs = ",".join(str(n) for n in nums)
                markup = escape(claim.text) + f" <font color='#167C80'>[{refs}]</font>"
                paragraph = Paragraph(markup, body_style)
                _, height = paragraph.wrap(251, 370)
                y -= height
                paragraph.drawOn(pdf, x, y)
                y -= 7
            y -= 12
        if y < 115:
            raise ValueError("Memo narrative exceeds one readable page; shorten claims before export")

    pdf.line(42, 108, 570, 108)
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(42, 96, "SOURCES & METHOD")
    unique = sorted(url_index.items(), key=lambda row: row[1])
    for offset, (url, number) in enumerate(unique):
        col = offset // 6
        row = offset % 6
        if col > 1:
            raise ValueError("Source list exceeds one page")
        x = 42 + col * 272
        y = 83 - row * 9
        accession = url.rstrip("/").split("/")[-1]
        label = f"[{number}] SEC filing {accession[:28]}"
        pdf.setFillColor(TEAL)
        pdf.setFont("Helvetica", 6.8)
        pdf.drawString(x, y, label)
        pdf.linkURL(url, (x, y - 1, x + stringWidth(label, "Helvetica", 6.8), y + 7), relative=0)
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 6.8)
    pdf.drawString(42, 13, f"Generated {memo.generated_at[:10]} | {memo.model} | {memo.prompt_version} | screening-v0.1 | 1 / 1")
    if memo.reviewed_at:
        pdf.drawString(42, 24, f"Editorial review {memo.reviewed_at[:10]} | deterministic tables; AI narrative reviewed against cited evidence")
    pdf.showPage()
    pdf.save()
    return stream.getvalue()
