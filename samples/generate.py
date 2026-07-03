"""
Sample evidence for a normal Refund Not Received dispute.
Customer : Deepak Ghosh (CUST-00001)
Txn      : TXN-00000003 | Raymond | Rs.12,451.48 | 02-Dec-2025 | UPI
Dispute  : Refund Not Received
Story    : Customer ordered a Raymond suit online. Order was cancelled (out of stock)
           on 05-Dec-2025. Merchant confirmed refund initiation but it never arrived.
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                Paragraph, Spacer, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

OUT      = os.path.dirname(os.path.abspath(__file__))
DARK     = colors.HexColor("#1A1A2E")
BRAND    = colors.HexColor("#8B0000")   # Raymond dark red
LGRAY    = colors.HexColor("#F7F7F7")
MGRAY    = colors.HexColor("#888888")
GREEN    = colors.HexColor("#1B5E20")

CUSTOMER  = "Deepak Ghosh"
CUST_ID   = "CUST-00001"
TXN_ID    = "TXN-00000003"
TXN_DATE  = "02-Dec-2025"
AMOUNT    = "Rs.12,451.48"
MERCHANT  = "Raymond"
ORDER_ID  = "RYM-ORD-2025-881234"
UPI_REF   = "406788123456"
REFUND_ID = "RYM-REF-2025-991122"


def hdr(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK)
    canvas.rect(0, A4[1]-2*cm, A4[0], 2*cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(1.5*cm, A4[1]-1.35*cm, MERCHANT + " — Official Document")
    canvas.setFont("Helvetica", 8.5)
    canvas.drawRightString(A4[0]-1.5*cm, A4[1]-1.35*cm, "www.raymond.in")
    canvas.setFillColor(MGRAY)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(1.5*cm, 0.7*cm, "Raymond Ltd | CIN: L17110MH1925PLC001 | GST: 27AAACR1234F1ZL")
    canvas.drawRightString(A4[0]-1.5*cm, 0.7*cm, f"Page {doc.page}")
    canvas.restoreState()


def row_table(rows, col_widths):
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), LGRAY),
        ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("GRID",       (0,0), (-1,-1), 0.4, colors.HexColor("#DDDDDD")),
        ("PADDING",    (0,0), (-1,-1), 6),
    ]))
    return t


# ── 1. ORIGINAL PAYMENT RECEIPT ──────────────────────────────────────────────
def make_payment_receipt():
    path = os.path.join(OUT, "payment_receipt.pdf")
    doc  = SimpleDocTemplate(path, pagesize=A4,
           topMargin=2.6*cm, bottomMargin=1.6*cm,
           leftMargin=2*cm, rightMargin=2*cm)
    story = []
    H = ParagraphStyle("H", fontSize=13, fontName="Helvetica-Bold",
                       textColor=DARK, spaceAfter=4)
    N = ParagraphStyle("N", fontSize=9, spaceAfter=4, leading=14)

    story += [
        Paragraph("PAYMENT RECEIPT", H),
        Paragraph(f"Order ID: <b>{ORDER_ID}</b>   |   Date: {TXN_DATE}", N),
        HRFlowable(width="100%", thickness=1, color=BRAND),
        Spacer(1, 0.3*cm),
    ]

    story.append(row_table([
        ["Customer Name",   CUSTOMER],
        ["Customer ID",     CUST_ID],
        ["Email",           "deepak.ghosh@email.com"],
        ["Phone",           "+91 98765 43210"],
        ["Delivery Address","23, Park Street, Kolkata, WB 700016"],
    ], [5*cm, 10*cm]))
    story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("ORDER SUMMARY", ParagraphStyle("s", fontSize=10,
                 fontName="Helvetica-Bold", textColor=DARK, spaceAfter=6)))

    items = [
        ["Item",                        "Qty", "Unit Price",  "Total"],
        ["Raymond Fine Wool Suit (Navy)", "1",  "Rs.10,999",  "Rs.10,999.00"],
        ["Pocket Square (Silk)",          "2",  "Rs.499",     "Rs.998.00"],
        ["Gift Wrapping",                 "1",  "Rs.199",     "Rs.199.00"],
        ["",                              "",   "Sub Total",  "Rs.12,196.00"],
        ["",                              "",   "GST (2.1%)", "Rs.255.48"],
        ["",                              "",   "Total",      "Rs.12,451.48"],
    ]
    t = Table(items, colWidths=[8*cm, 1.5*cm, 3*cm, 3.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0),  (-1,0),  DARK),
        ("TEXTCOLOR",   (0,0),  (-1,0),  colors.white),
        ("FONTNAME",    (0,0),  (-1,0),  "Helvetica-Bold"),
        ("FONTNAME",    (2,4),  (-1,-1), "Helvetica-Bold"),
        ("BACKGROUND",  (2,-1), (-1,-1), BRAND),
        ("TEXTCOLOR",   (2,-1), (-1,-1), colors.white),
        ("ROWBACKGROUNDS", (0,1), (-1,3), [colors.white, LGRAY]),
        ("FONTSIZE",    (0,0),  (-1,-1), 9),
        ("ALIGN",       (1,0),  (-1,-1), "RIGHT"),
        ("GRID",        (0,0),  (-1,3),  0.4, colors.HexColor("#DDDDDD")),
        ("LINEABOVE",   (0,4),  (-1,-1), 0.5, colors.HexColor("#CCCCCC")),
        ("PADDING",     (0,0),  (-1,-1), 6),
    ]))
    story += [t, Spacer(1, 0.4*cm)]

    story.append(row_table([
        ["Payment Method",  "UPI"],
        ["UPI ID",          "deepak.ghosh@oksbi"],
        ["UPI Reference",   UPI_REF],
        ["Bank",            "National Trust Bank"],
        ["Transaction ID",  TXN_ID],
        ["Payment Date",    TXN_DATE + " at 06:02 AM"],
        ["Payment Status",  "SUCCESS"],
    ], [5*cm, 10*cm]))

    story += [Spacer(1, 0.5*cm),
        Paragraph("Thank you for shopping with Raymond. Your order is being processed.",
                  ParagraphStyle("th", fontSize=9, textColor=MGRAY, alignment=TA_CENTER))]
    doc.build(story, onFirstPage=hdr, onLaterPages=hdr)
    print("done: payment_receipt.pdf")


# ── 2. ORDER CANCELLATION CONFIRMATION ───────────────────────────────────────
def make_cancellation():
    path = os.path.join(OUT, "order_cancellation.pdf")
    doc  = SimpleDocTemplate(path, pagesize=A4,
           topMargin=2.6*cm, bottomMargin=1.6*cm,
           leftMargin=2*cm, rightMargin=2*cm)
    story = []
    H = ParagraphStyle("H", fontSize=13, fontName="Helvetica-Bold", textColor=DARK, spaceAfter=4)
    N = ParagraphStyle("N", fontSize=9.5, spaceAfter=6, leading=16)

    story += [
        Paragraph("ORDER CANCELLATION CONFIRMATION", H),
        HRFlowable(width="100%", thickness=1, color=BRAND),
        Spacer(1, 0.3*cm),
        Paragraph(f"Dear <b>{CUSTOMER}</b>,", N),
        Paragraph(
            f"We regret to inform you that your order <b>{ORDER_ID}</b> placed on "
            f"<b>{TXN_DATE}</b> has been cancelled. The reason for cancellation is:",
            N),
        Paragraph("<b>Reason:</b> Ordered item (Raymond Fine Wool Suit — Navy, Size 40) "
                  "is currently out of stock at our warehouse. We were unable to fulfil "
                  "your order within the promised delivery window.", N),
        Spacer(1, 0.3*cm),
    ]

    story.append(row_table([
        ["Order ID",           ORDER_ID],
        ["Cancellation Date",  "05-Dec-2025"],
        ["Cancelled By",       "Raymond Fulfillment Team (Auto — Out of Stock)"],
        ["Refund Amount",      AMOUNT],
        ["Refund Reference",   REFUND_ID],
        ["Refund Initiated",   "05-Dec-2025 at 14:22 IST"],
        ["Expected Credit",    "7–10 business days (by 15-Dec-2025)"],
        ["Refund Mode",        "UPI — Original payment method"],
        ["Refund UPI ID",      "deepak.ghosh@oksbi"],
    ], [5.5*cm, 9.5*cm]))

    story += [Spacer(1, 0.5*cm),
        Paragraph(
            f"The refund of <b>{AMOUNT}</b> has been initiated to your original UPI ID "
            f"(<b>deepak.ghosh@oksbi</b>) on <b>05-Dec-2025</b>. "
            "If you do not receive the refund within 10 business days, please contact "
            "your bank or raise a dispute with us at <b>support@raymond.in</b>.",
            ParagraphStyle("N2", fontSize=9.5, spaceAfter=6, leading=16)),
        Spacer(1, 0.5*cm),
        Paragraph("We sincerely apologise for the inconvenience caused.",
                  ParagraphStyle("N3", fontSize=9.5, textColor=MGRAY)),
        Spacer(1, 0.5*cm),
        Paragraph("Raymond Customer Care<br/>support@raymond.in | 1800-209-RAYMOND",
                  ParagraphStyle("sig", fontSize=9, fontName="Helvetica-Bold", textColor=DARK)),
    ]
    doc.build(story, onFirstPage=hdr, onLaterPages=hdr)
    print("done: order_cancellation.pdf")


# ── 3. MERCHANT EMAIL COMMUNICATION ──────────────────────────────────────────
def make_merchant_email():
    path = os.path.join(OUT, "merchant_communication.pdf")
    doc  = SimpleDocTemplate(path, pagesize=A4,
           topMargin=2.6*cm, bottomMargin=1.6*cm,
           leftMargin=2*cm, rightMargin=2*cm)
    story = []
    H  = ParagraphStyle("H",  fontSize=12, fontName="Helvetica-Bold", textColor=DARK, spaceAfter=4)
    LB = ParagraphStyle("LB", fontSize=8.5, textColor=MGRAY, spaceAfter=1)
    LV = ParagraphStyle("LV", fontSize=9.5, spaceAfter=10, leading=14)
    EB = ParagraphStyle("EB", fontSize=9.5, backColor=LGRAY, borderPadding=10,
                        leading=16, spaceAfter=8)

    story += [
        Paragraph("EMAIL COMMUNICATION SCREENSHOT", H),
        Paragraph("Exported from: deepak.ghosh@email.com | Gmail",
                  ParagraphStyle("sub", fontSize=8.5, textColor=MGRAY, spaceAfter=12)),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD")),
        Spacer(1, 0.3*cm),
    ]

    emails = [
        {
            "from": "noreply@raymond.in",
            "to":   "deepak.ghosh@email.com",
            "date": "05-Dec-2025 at 14:25 IST",
            "subj": f"Refund Initiated — Order {ORDER_ID}",
            "body": (f"Dear {CUSTOMER},\n\n"
                     f"Your order {ORDER_ID} has been cancelled. We have initiated a "
                     f"refund of {AMOUNT} to your UPI ID deepak.ghosh@oksbi.\n\n"
                     f"Refund Reference: {REFUND_ID}\n"
                     "Expected credit: 7–10 business days.\n\n"
                     "Regards,\nRaymond Customer Support"),
        },
        {
            "from": "deepak.ghosh@email.com",
            "to":   "support@raymond.in",
            "date": "18-Dec-2025 at 11:05 IST",
            "subj": f"Re: Refund Initiated — Order {ORDER_ID} — NOT RECEIVED",
            "body": ("Hi,\n\n"
                     "My order was cancelled on 05-Dec-2025 and you confirmed a refund of "
                     f"{AMOUNT} (Ref: {REFUND_ID}). It has been 13 days now and the amount "
                     "has NOT been credited to my account.\n\n"
                     "Please look into this urgently. My bank statement shows no credit.\n\n"
                     "Transaction ID: TXN-00000003\n"
                     "UPI ID: deepak.ghosh@oksbi\n\n"
                     "Regards,\nDeepak Ghosh"),
        },
        {
            "from": "support@raymond.in",
            "to":   "deepak.ghosh@email.com",
            "date": "19-Dec-2025 at 09:30 IST",
            "subj": f"Re: Refund Initiated — Order {ORDER_ID} — NOT RECEIVED",
            "body": ("Dear Deepak,\n\n"
                     "Thank you for writing to us. We have confirmed with our payments "
                     "team that the refund was processed on 05-Dec-2025. Our bank "
                     "records show the refund was sent to your UPI ID.\n\n"
                     "We recommend contacting your bank (National Trust Bank) as the "
                     "funds may be held at their end. Please quote our Refund Reference: "
                     f"{REFUND_ID}.\n\n"
                     "Regards,\nRaymond Customer Support | Case #RYM-CS-2025-44312"),
        },
    ]

    for em in emails:
        story.append(row_table([
            ["From",    em["from"]],
            ["To",      em["to"]],
            ["Date",    em["date"]],
            ["Subject", em["subj"]],
        ], [2.5*cm, 12.5*cm]))
        body_lines = em["body"].replace("\n", "<br/>")
        story += [
            Paragraph(body_lines, EB),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#EEEEEE")),
            Spacer(1, 0.3*cm),
        ]

    doc.build(story, onFirstPage=hdr, onLaterPages=hdr)
    print("done: merchant_communication.pdf")


# ── 4. BANK STATEMENT (relevant section) ────────────────────────────────────
def make_bank_statement():
    path = os.path.join(OUT, "bank_statement.pdf")
    doc  = SimpleDocTemplate(path, pagesize=A4,
           topMargin=2.6*cm, bottomMargin=1.6*cm,
           leftMargin=1.5*cm, rightMargin=1.5*cm)
    story = []
    H  = ParagraphStyle("H",  fontSize=13, fontName="Helvetica-Bold", textColor=DARK, spaceAfter=4)
    N  = ParagraphStyle("N",  fontSize=9,  spaceAfter=4)

    story += [
        Paragraph("BANK ACCOUNT STATEMENT — Last 30 Days", H),
        Paragraph("National Trust Bank | Account: XXXX XXXX 5510 | Customer: " + CUSTOMER, N),
        Paragraph("Statement Period: 01-Dec-2025 to 31-Dec-2025", N),
        HRFlowable(width="100%", thickness=1, color=DARK),
        Spacer(1, 0.3*cm),
    ]

    txns = [
        ["Date",         "Description",                           "Ref No",        "Debit",       "Credit",   "Balance"],
        ["01-Dec-2025",  "UPI — Electricity Board APSEB",        "TXN-00000099",  "2,180.00",   "",          "1,45,320.00"],
        ["02-Dec-2025",  "UPI — Raymond (ORDER: " + ORDER_ID+")",TXN_ID,          "12,451.48",  "",          "1,32,868.52"],
        ["05-Dec-2025",  "UPI — Swiggy",                         "TXN-00000101",  "389.00",     "",          "1,32,479.52"],
        ["08-Dec-2025",  "NEFT Credit — Salary",                 "TXN-00000102",  "",           "85,000.00", "2,17,479.52"],
        ["10-Dec-2025",  "UPI — Amazon Pay",                     "TXN-00000103",  "1,299.00",   "",          "2,16,180.52"],
        ["12-Dec-2025",  "UPI — Zomato",                         "TXN-00000104",  "455.00",     "",          "2,15,725.52"],
        ["15-Dec-2025",  "UPI — Society Maintenance",            "TXN-00000105",  "4,500.00",   "",          "2,11,225.52"],
        ["18-Dec-2025",  "UPI — Flipkart",                       "TXN-00000106",  "2,199.00",   "",          "2,09,026.52"],
        ["20-Dec-2025",  "ATM Withdrawal",                       "TXN-00000107",  "5,000.00",   "",          "2,04,026.52"],
        ["25-Dec-2025",  "UPI — Electricity Board",              "TXN-00000108",  "2,340.00",   "",          "2,01,686.52"],
        ["31-Dec-2025",  "Closing Balance",                      "",               "",           "",          "2,01,686.52"],
    ]

    t = Table(txns, colWidths=[2.5*cm, 7*cm, 3*cm, 2.5*cm, 2.5*cm, 2.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),  (-1,0),  DARK),
        ("TEXTCOLOR",      (0,0),  (-1,0),  colors.white),
        ("FONTNAME",       (0,0),  (-1,0),  "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1),  (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
        ("BACKGROUND",     (0,2),  (-1,2),  colors.HexColor("#FFF3CD")),
        ("FONTNAME",       (0,2),  (-1,2),  "Helvetica-Bold"),
        ("FONTSIZE",       (0,0),  (-1,-1), 8),
        ("ALIGN",          (3,0),  (-1,-1), "RIGHT"),
        ("GRID",           (0,0),  (-1,-1), 0.4, colors.HexColor("#DDDDDD")),
        ("PADDING",        (0,0),  (-1,-1), 5),
    ]))
    story += [t, Spacer(1, 0.4*cm)]

    story.append(Paragraph(
        f"<b>Note:</b> The highlighted row (02-Dec-2025) shows a debit of "
        f"<b>Rs.12,451.48</b> to Raymond for Order {ORDER_ID} (Ref: {TXN_ID}). "
        "No corresponding credit/refund has been received in this statement period "
        "despite the merchant confirming refund initiation on 05-Dec-2025.",
        ParagraphStyle("note", fontSize=8.5, textColor=colors.HexColor("#7B5800"),
                       backColor=colors.HexColor("#FFF3CD"), borderPadding=8)))

    doc.build(story, onFirstPage=hdr, onLaterPages=hdr)
    print("done: bank_statement.pdf")


# ── 5. REFUND CONFIRMATION FROM MERCHANT ─────────────────────────────────────
def make_refund_confirmation():
    path = os.path.join(OUT, "refund_confirmation.pdf")
    doc  = SimpleDocTemplate(path, pagesize=(14*cm, 20*cm),
           topMargin=1.5*cm, bottomMargin=1.5*cm,
           leftMargin=1.5*cm, rightMargin=1.5*cm)
    story = []

    C = ParagraphStyle("C", alignment=TA_CENTER, fontSize=13, fontName="Helvetica-Bold",
                       textColor=DARK, spaceAfter=4)
    N = ParagraphStyle("N", fontSize=9.5, leading=16, spaceAfter=6)
    G = ParagraphStyle("G", fontSize=9.5, leading=16, textColor=GREEN, fontName="Helvetica-Bold")

    story += [
        Paragraph(MERCHANT, C),
        Paragraph("REFUND CONFIRMATION", ParagraphStyle("RC", alignment=TA_CENTER,
                  fontSize=12, fontName="Helvetica-Bold", textColor=BRAND, spaceAfter=6)),
        HRFlowable(width="100%", thickness=1.5, color=BRAND),
        Spacer(1, 0.4*cm),
        Paragraph(f"Dear <b>{CUSTOMER}</b>,", N),
        Paragraph(
            f"This is to confirm that a refund of <b>{AMOUNT}</b> has been "
            "successfully processed from our end for your cancelled order.",
            N),
        Spacer(1, 0.3*cm),
    ]

    story.append(row_table([
        ["Refund Reference",   REFUND_ID],
        ["Order ID",           ORDER_ID],
        ["Refund Amount",      AMOUNT],
        ["Refund Date",        "05-Dec-2025"],
        ["Refund Time",        "14:22:38 IST"],
        ["Payment Mode",       "UPI — Original Payment Method"],
        ["Beneficiary UPI ID", "deepak.ghosh@oksbi"],
        ["Bank",               "National Trust Bank"],
        ["Original Txn Ref",   TXN_ID],
        ["Refund Status",      "PROCESSED — Sent to beneficiary bank"],
        ["Expected Credit",    "Within 7–10 business days"],
    ], [5*cm, 6*cm]))

    story += [
        Spacer(1, 0.5*cm),
        Paragraph(
            "The refund has been processed from Raymond's payment gateway "
            "(PayU India) to your registered UPI ID. If you have not received "
            "the amount after 10 business days, please contact your bank with "
            f"this Refund Reference: <b>{REFUND_ID}</b>.",
            ParagraphStyle("note", fontSize=8.5, leading=13,
                           backColor=colors.HexColor("#E8F5E9"), borderPadding=8)),
        Spacer(1, 0.5*cm),
        Paragraph("Raymond Customer Care", ParagraphStyle("s", fontSize=9,
                  fontName="Helvetica-Bold", textColor=DARK)),
        Paragraph("support@raymond.in  |  1800-209-RAYMOND", ParagraphStyle("s2",
                  fontSize=8.5, textColor=MGRAY)),
        Spacer(1, 0.3*cm),
        Paragraph("— This is a system-generated document —",
                  ParagraphStyle("sys", fontSize=7.5, textColor=MGRAY, alignment=TA_CENTER)),
    ]
    doc.build(story)
    print("done: refund_confirmation.pdf")


if __name__ == "__main__":
    print("Generating evidence documents...")
    make_payment_receipt()
    make_cancellation()
    make_merchant_email()
    make_bank_statement()
    print(f"\nAll saved to: {OUT}")
    print("\n--- FORM FILL GUIDE ---")
    print("Step 1  Customer ID      : CUST-00001")
    print("Step 2  Transaction ID   : TXN-00000003")
    print("Step 3  Dispute Reason   : Refund Not Received")
    print("        Description      : I placed an order on Raymond's website (Order: RYM-ORD-2025-881234)")
    print("                           and paid Rs.12,451.48 via UPI on 02-Dec-2025.")
    print("                           The order was cancelled by Raymond on 05-Dec-2025 due")
    print("                           to stock unavailability. Raymond confirmed a refund")
    print("                           (Ref: RYM-REF-2025-991122) but it has not been")
    print("                           credited to my account even after 30 days.")
    print("        All fraud flags  : No (leave all as No)")
    print("Step 4  Upload documents :")
    print("          - payment_receipt.pdf")
    print("          - order_cancellation.pdf")
    print("          - merchant_communication.pdf")
    print("          - bank_statement.pdf")
