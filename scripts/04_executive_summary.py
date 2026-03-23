"""
04_executive_summary.py
────────────────────────────────────────────────────────────
Generates a CFO-ready one-page executive summary PDF
and saves it to docs/executive_summary.pdf.
────────────────────────────────────────────────────────────
"""

import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.enums import TA_CENTER

# ── Data ──────────────────────────────────────────────────
df        = pd.read_csv("data/hotel_bookings_clean.csv")
confirmed = df[df["is_canceled"] == 0]

cancel_rate   = df["is_canceled"].mean() * 100
avg_adr       = confirmed["adr"].mean()
total_revenue = confirmed["total_revenue"].sum()
avg_nights    = confirmed["total_nights"].mean()
avg_lead      = df["lead_time"].mean()

seg_cancel = (df.groupby("market_segment")
                .agg(total=("is_canceled","count"), canceled=("is_canceled","sum"))
                .assign(rate=lambda x: x["canceled"] / x["total"] * 100)
                .sort_values("rate", ascending=False))

ch_stats = (confirmed.groupby("distribution_channel")
              .agg(bookings=("adr","count"),
                   avg_adr=("adr","mean"),
                   revenue=("total_revenue","sum"))
              .reset_index())
cancel_ch = (df.groupby("distribution_channel")["is_canceled"]
               .mean().reset_index()
               .rename(columns={"is_canceled": "cr"}))
ch_full = (ch_stats.merge(cancel_ch, on="distribution_channel")
                   .sort_values("revenue", ascending=False))

# ── Styles ────────────────────────────────────────────────
DARK_BLUE  = colors.HexColor("#0f2d5c")
MID_BLUE   = colors.HexColor("#1a5fa8")
LIGHT_BLUE = colors.HexColor("#e8f0fb")
GRAY       = colors.HexColor("#6b7280")
WHITE      = colors.white

styles = getSampleStyleSheet()

def style(name, **kwargs):
    return ParagraphStyle(name, parent=styles["Normal"], **kwargs)

title_s    = style("title",    fontSize=20, textColor=DARK_BLUE,
                   spaceAfter=4,  fontName="Helvetica-Bold")
subtitle_s = style("subtitle", fontSize=11, textColor=GRAY,
                   spaceAfter=16, fontName="Helvetica")
h2_s       = style("h2",       fontSize=13, textColor=DARK_BLUE,
                   spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold")
body_s     = style("body",     fontSize=10, textColor=colors.HexColor("#374151"),
                   spaceAfter=6, leading=15, fontName="Helvetica")
bullet_s   = style("bullet",   fontSize=10, textColor=colors.HexColor("#374151"),
                   spaceAfter=4, leading=15, fontName="Helvetica", leftIndent=16)
footer_s   = style("footer",   fontSize=8,  textColor=GRAY,
                   alignment=TA_CENTER, fontName="Helvetica")

def tbl_style(data):
    return TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  DARK_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_BLUE]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN",         (1, 0), (-1, -1), "CENTER"),
    ])

# ── Build PDF ─────────────────────────────────────────────
doc   = SimpleDocTemplate(
    "docs/executive_summary.pdf", pagesize=letter,
    rightMargin=0.75*inch, leftMargin=0.75*inch,
    topMargin=0.75*inch,   bottomMargin=0.75*inch
)
story = []

story.append(Paragraph("Hotel Performance Analysis", title_s))
story.append(Paragraph("Executive Summary | Corporate Analyst Portfolio Project", subtitle_s))
story.append(HRFlowable(width="100%", thickness=2, color=MID_BLUE))
story.append(Spacer(1, 12))

# KPI table
story.append(Paragraph("Key Performance Indicators", h2_s))
kpi_data = [
    ["Metric", "Value", "Insight"],
    ["Total Bookings Analyzed",  f"{len(df):,}",              "2015–2017 dataset"],
    ["Overall Cancellation Rate",f"{cancel_rate:.1f}%",       "Industry avg ~20% — elevated"],
    ["Average Daily Rate (ADR)", f"${avg_adr:.2f}",           "Confirmed stays only"],
    ["Estimated Total Revenue",  f"${total_revenue/1e6:.1f}M","Confirmed stays only"],
    ["Average Length of Stay",   f"{avg_nights:.1f} nights",  "Both hotel types combined"],
    ["Average Booking Lead Time",f"{avg_lead:.0f} days",      "Higher lead time → higher cancel risk"],
]
t = Table(kpi_data, colWidths=[2.5*inch, 1.5*inch, 3.2*inch])
t.setStyle(tbl_style(kpi_data))
story.append(t)
story.append(Spacer(1, 12))

# Cancellation section
story.append(Paragraph("Cancellation Risk Analysis", h2_s))
story.append(Paragraph(
    "At 37.1%, the overall cancellation rate significantly exceeds the hospitality "
    "industry average of ~20%. Segment-level analysis exposes where the risk is "
    "concentrated:", body_s))
for seg, row in seg_cancel.head(4).iterrows():
    story.append(Paragraph(
        f"• <b>{seg}</b>: {row['rate']:.1f}% cancellation rate "
        f"({int(row['canceled']):,} of {int(row['total']):,} bookings cancelled)",
        bullet_s))
story.append(Paragraph(
    "<b>Recommendation:</b> Introduce targeted deposit policies for the Online TA "
    "and Groups segments. A non-refundable tier with a modest discount incentive "
    "could materially reduce revenue leakage from late cancellations.", body_s))
story.append(Spacer(1, 8))

# Channel section
story.append(Paragraph("Revenue & Distribution Channel Performance", h2_s))
story.append(Paragraph(
    "Direct bookings carry a 17.5% cancellation rate and higher ADR — less than "
    "half the TA/TO channel rate of 41.1%. Shifting channel mix toward Direct "
    "improves both margin and forecast reliability.", body_s))

ch_data = [["Channel", "Confirmed", "Avg ADR", "Revenue", "Cancel Rate"]]
for _, r in ch_full.iterrows():
    ch_data.append([
        r["distribution_channel"],
        f"{int(r['bookings']):,}",
        f"${r['avg_adr']:.2f}",
        f"${r['revenue']/1e6:.1f}M",
        f"{r['cr']*100:.1f}%",
    ])
t2 = Table(ch_data, colWidths=[1.8*inch, 1.4*inch, 1.2*inch, 1.3*inch, 1.3*inch])
t2.setStyle(tbl_style(ch_data))
story.append(t2)
story.append(Spacer(1, 12))

# Forecast section
story.append(Paragraph("Forecast Accuracy & Recommendations", h2_s))
recs = [
    "Segment forecasts separately — Online TA and Groups need a cancellation haircut of 35–99%",
    "Apply lead-time decay factors: bookings 90+ days out cancel at nearly 2× the rate of same-week bookings",
    "Track rolling 30/60/90-day cancellation velocity as a leading indicator",
    "Treat Non-Refundable deposit bookings as near-certain revenue — they cancel at <1%",
]
for r in recs:
    story.append(Paragraph(f"• {r}", bullet_s))

story.append(Spacer(1, 16))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#d1d5db")))
story.append(Spacer(1, 6))
story.append(Paragraph(
    "Analysis based on 119,208 hotel bookings (2015–2017)  |  "
    "Source: Hotel Booking Demand Dataset (Kaggle)  |  "
    "Tools: Python · pandas · SQL · Power BI",
    footer_s))

doc.build(story)
print("Saved: docs/executive_summary.pdf")
