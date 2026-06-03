"""Generate mocked garage repair-invoice PDFs for the Garage Repair Checker demo.

Renders one PDF per claim with WeasyPrint. Three different garage "brands"/layouts
are used so the invoice parser is shown to be robust to format variation. Each
invoice's line items are crafted so the scenario verdict is defensible:

  CLM-A  Northgate   - fair repair, matches the photo            -> approve
  CLM-B  Apex        - panel-stuffing + inflated hours/rate/OEM  -> flag leakage
  CLM-C  Citywide    - costs ok but submitted photo is synthetic -> flag imagery
  CLM-D  Northgate   - extensive genuine damage, > total-loss %  -> total loss

All monetary values in GBP. VAT at 20%.
Output: assets/invoices/<CLAIM_ID>_<garage_slug>_invoice.pdf
"""
import os
from weasyprint import HTML

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "invoices")
os.makedirs(OUT_DIR, exist_ok=True)
VAT_RATE = 0.20


def money(x):
    return f"\u00a3{x:,.2f}"


# ---------------------------------------------------------------------------
# Garage "brands" - each gets its own colour + header layout so the parser
# has to cope with genuinely different document styles.
# ---------------------------------------------------------------------------
GARAGES = {
    "northgate": {
        "name": "Northgate Accident Repair Centre",
        "addr": "Unit 14 Northgate Industrial Estate, Coventry CV6 5RU",
        "tel": "024 7655 0142",
        "vat": "GB 482 5571 09",
        "accent": "#003781",  # Allianz-ish blue
        "slug": "northgate",
    },
    "apex": {
        "name": "Apex Prestige Bodyworks Ltd",
        "addr": "7 Brunel Way, Slough Trading Estate, Slough SL1 4DX",
        "tel": "01753 290 880",
        "vat": "GB 911 2043 66",
        "accent": "#1a1a1a",  # dark header, different feel
        "slug": "apex",
    },
    "citywide": {
        "name": "Citywide Crash Repairs",
        "addr": "221 Eastfield Road, Peterborough PE1 4BD",
        "tel": "01733 311 905",
        "vat": "GB 376 9981 22",
        "accent": "#15703a",  # green
        "slug": "citywide",
    },
}


# ---------------------------------------------------------------------------
# Invoices. Each line: (section, description, qty_label, qty, unit_price)
# qty is hours for Labour/Paint labour lines, or units for Parts/Sublet.
# ---------------------------------------------------------------------------
INVOICES = [
    {
        "claim_id": "CLM-A",
        "garage": "northgate",
        "invoice_no": "NRC-24881",
        "date": "2026-05-12",
        "vehicle": "2021 Volkswagen Golf 1.5 TSI Life (Silver)",
        "reg": "LP21 ZRT",
        "vin": "WVWZZZ1KZMW402188",
        "mileage": "31,420",
        "labour_rate": 55.0,
        "lines": [
            ("Parts", "Front bumper cover - aftermarket (OE-equivalent)", "ea", 1, 210.00),
            ("Parts", "Offside (driver) headlamp unit - aftermarket", "ea", 1, 180.00),
            ("Parts", "Clips, fixings & consumables", "ea", 1, 25.00),
            ("Labour", "Remove & refit front bumper, O/S corner", "hrs", 1.5, 55.00),
            ("Labour", "Replace & align O/S headlamp", "hrs", 0.8, 55.00),
            ("Paint", "Refinish front bumper (prep, prime, colour)", "hrs", 2.0, 55.00),
            ("Paint", "Paint materials & sundries", "ea", 1, 85.00),
        ],
        "notes": "Light front O/S impact. Repairs limited to front bumper corner and driver-side headlamp.",
    },
    {
        "claim_id": "CLM-B",
        "garage": "apex",
        "invoice_no": "APX-7741",
        "date": "2026-05-19",
        "vehicle": "2019 Ford Focus 1.0 EcoBoost Zetec (Blue)",
        "reg": "BV19 KMO",
        "vin": "WF05XXGCC5JE91204",
        "mileage": "54,905",
        "labour_rate": 62.0,
        "lines": [
            ("Parts", "N/S front wing - genuine OEM Ford", "ea", 1, 320.00),
            ("Parts", "N/S front door skin - genuine OEM Ford", "ea", 1, 540.00),
            ("Parts", "Bonnet panel - genuine OEM Ford", "ea", 1, 480.00),
            ("Parts", "Fixings, clips & sundries", "ea", 1, 60.00),
            ("Labour", "Replace N/S front wing", "hrs", 3.0, 62.00),
            ("Labour", "Replace N/S front door skin", "hrs", 5.0, 62.00),
            ("Labour", "Repair O/S rear quarter panel", "hrs", 6.0, 62.00),
            ("Labour", "Replace bonnet panel", "hrs", 3.0, 62.00),
            ("Paint", "Refinish & blend - 8 panels", "hrs", 12.0, 62.00),
            ("Paint", "Paint materials & sundries", "ea", 1, 290.00),
        ],
        "notes": "Accident damage repair, multiple panels. Genuine OEM parts fitted throughout.",
    },
    {
        "claim_id": "CLM-C",
        "garage": "citywide",
        "invoice_no": "CCR-50318",
        "date": "2026-05-21",
        "vehicle": "2020 BMW 320i M Sport (Black)",
        "reg": "RK20 HWA",
        "vin": "WBA5R12090FH88210",
        "mileage": "42,110",
        "labour_rate": 56.0,
        "lines": [
            ("Parts", "Front bumper - genuine OEM BMW", "ea", 1, 390.00),
            ("Parts", "O/S headlamp - genuine OEM BMW", "ea", 1, 320.00),
            ("Parts", "N/S front wing - genuine OEM BMW", "ea", 1, 300.00),
            ("Parts", "Bonnet panel - genuine OEM BMW", "ea", 1, 450.00),
            ("Parts", "Fixings & consumables", "ea", 1, 70.00),
            ("Labour", "Remove & refit front bumper", "hrs", 1.5, 56.00),
            ("Labour", "Replace O/S headlamp", "hrs", 0.8, 56.00),
            ("Labour", "Replace N/S front wing", "hrs", 2.5, 56.00),
            ("Labour", "Replace bonnet panel", "hrs", 2.5, 56.00),
            ("Paint", "Refinish front bumper, wing & bonnet", "hrs", 7.0, 56.00),
            ("Paint", "Paint materials & sundries", "ea", 1, 240.00),
        ],
        "notes": "Front-end impact. Photographs of damage supplied by submitting party.",
    },
    {
        "claim_id": "CLM-D",
        "garage": "northgate",
        "invoice_no": "NRC-24903",
        "date": "2026-05-23",
        "vehicle": "2015 Audi A4 2.0 TDI S line (Dark Grey)",
        "reg": "YE15 OFN",
        "vin": "WAUZZZ8K5FA118975",
        "mileage": "98,640",
        "labour_rate": 55.0,
        "lines": [
            ("Parts", "Front bumper assembly - OEM", "ea", 1, 420.00),
            ("Parts", "Bonnet panel - OEM", "ea", 1, 510.00),
            ("Parts", "Headlamp units, pair - OEM", "ea", 1, 640.00),
            ("Parts", "Radiator & A/C condenser pack", "ea", 1, 480.00),
            ("Parts", "Front wings, pair - OEM", "ea", 1, 620.00),
            ("Parts", "Front slam panel / carrier", "ea", 1, 390.00),
            ("Parts", "Airbags (driver + passenger) & clock spring", "ea", 1, 1950.00),
            ("Parts", "Windscreen", "ea", 1, 320.00),
            ("Parts", "Coolant, fixings & sundries", "ea", 1, 180.00),
            ("Labour", "Strip & rebuild front end", "hrs", 18.0, 55.00),
            ("Labour", "Structural / chassis jig alignment", "hrs", 8.0, 55.00),
            ("Labour", "Airbag module replacement & coding", "hrs", 4.0, 55.00),
            ("Paint", "Refinish front panels", "hrs", 14.0, 55.00),
            ("Paint", "Paint materials & sundries", "ea", 1, 420.00),
            ("Sublet", "ADAS camera/radar calibration (sublet)", "ea", 1, 280.00),
            ("Sublet", "Four-wheel alignment (sublet)", "ea", 1, 120.00),
        ],
        "notes": "Severe frontal collision. Deployed airbags, structural deformation, radiator pack destroyed.",
    },
]


SECTION_ORDER = ["Parts", "Labour", "Paint", "Sublet"]


def render_invoice(inv):
    g = GARAGES[inv["garage"]]
    rows = []
    subtotal = 0.0
    for section in SECTION_ORDER:
        sec_lines = [l for l in inv["lines"] if l[0] == section]
        if not sec_lines:
            continue
        rows.append(f'<tr class="sec"><td colspan="4">{section}</td></tr>')
        for _, desc, unit, qty, price in sec_lines:
            amount = qty * price
            subtotal += amount
            qty_disp = f"{qty:g} {unit}"
            rows.append(
                f"<tr><td class='desc'>{desc}</td><td class='num'>{qty_disp}</td>"
                f"<td class='num'>{money(price)}</td><td class='num'>{money(amount)}</td></tr>"
            )
    vat = round(subtotal * VAT_RATE, 2)
    total = subtotal + vat
    rows_html = "\n".join(rows)

    html = f"""<!doctype html><html><head><meta charset='utf-8'><style>
    @page {{ size: A4; margin: 18mm 16mm; }}
    * {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #1a1a1a; }}
    .hdr {{ border-bottom: 4px solid {g['accent']}; padding-bottom: 10px; margin-bottom: 18px; }}
    .gname {{ font-size: 22px; font-weight: 800; color: {g['accent']}; letter-spacing: 0.3px; }}
    .gmeta {{ font-size: 10.5px; color: #555; margin-top: 4px; line-height: 1.5; }}
    .title {{ float: right; text-align: right; }}
    .title h1 {{ font-size: 26px; margin: 0; color: {g['accent']}; letter-spacing: 2px; }}
    .title .inv {{ font-size: 11px; color: #555; }}
    .meta-box {{ width: 100%; border-collapse: collapse; margin: 14px 0 18px; font-size: 11px; }}
    .meta-box td {{ border: 1px solid #ddd; padding: 6px 8px; }}
    .meta-box .k {{ background: #f4f6f9; font-weight: 700; width: 22%; }}
    table.items {{ width: 100%; border-collapse: collapse; font-size: 11px; }}
    table.items th {{ background: {g['accent']}; color: #fff; text-align: left; padding: 7px 8px; }}
    table.items th.num, table.items td.num {{ text-align: right; }}
    table.items td {{ padding: 6px 8px; border-bottom: 1px solid #eee; }}
    table.items td.desc {{ width: 56%; }}
    tr.sec td {{ background: #eef1f5; font-weight: 700; text-transform: uppercase; font-size: 10px; letter-spacing: 0.6px; }}
    .totals {{ float: right; width: 46%; margin-top: 12px; font-size: 12px; }}
    .totals table {{ width: 100%; border-collapse: collapse; }}
    .totals td {{ padding: 5px 8px; }}
    .totals .lbl {{ text-align: right; color: #555; }}
    .totals .val {{ text-align: right; font-weight: 700; width: 38%; }}
    .totals .grand td {{ border-top: 2px solid {g['accent']}; font-size: 14px; color: {g['accent']}; }}
    .notes {{ clear: both; margin-top: 70px; font-size: 10px; color: #666; border-top: 1px solid #ddd; padding-top: 8px; }}
    </style></head><body>
    <div class='hdr'>
      <div class='title'><h1>INVOICE</h1>
        <div class='inv'>No. {inv['invoice_no']}<br>Date: {inv['date']}</div></div>
      <div class='gname'>{g['name']}</div>
      <div class='gmeta'>{g['addr']}<br>Tel {g['tel']} &nbsp;&middot;&nbsp; VAT Reg {g['vat']}</div>
    </div>

    <table class='meta-box'>
      <tr><td class='k'>Claim reference</td><td>{inv['claim_id']}</td>
          <td class='k'>Insurer</td><td>Allianz Insurance plc</td></tr>
      <tr><td class='k'>Vehicle</td><td>{inv['vehicle']}</td>
          <td class='k'>Registration</td><td>{inv['reg']}</td></tr>
      <tr><td class='k'>VIN</td><td>{inv['vin']}</td>
          <td class='k'>Mileage</td><td>{inv['mileage']}</td></tr>
      <tr><td class='k'>Labour rate</td><td>{money(inv['labour_rate'])} / hour</td>
          <td class='k'>Payment terms</td><td>30 days net</td></tr>
    </table>

    <table class='items'>
      <tr><th>Description</th><th class='num'>Qty / Hours</th><th class='num'>Unit</th><th class='num'>Amount</th></tr>
      {rows_html}
    </table>

    <div class='totals'><table>
      <tr><td class='lbl'>Subtotal (ex VAT)</td><td class='val'>{money(subtotal)}</td></tr>
      <tr><td class='lbl'>VAT @ 20%</td><td class='val'>{money(vat)}</td></tr>
      <tr class='grand'><td class='lbl'>Total due</td><td class='val'>{money(total)}</td></tr>
    </table></div>

    <div class='notes'><b>Repairer notes:</b> {inv['notes']}<br>
    This estimate is submitted for insurer authorisation prior to commencement of repair work.</div>
    </body></html>"""

    out = os.path.join(OUT_DIR, f"{inv['claim_id']}_{g['slug']}_invoice.pdf")
    HTML(string=html).write_pdf(out)
    print(f"  {inv['claim_id']:6s} {g['name'][:32]:32s} subtotal={money(subtotal)} vat={money(vat)} total={money(total)} -> {os.path.basename(out)}")
    return out


if __name__ == "__main__":
    print(f"Rendering {len(INVOICES)} invoices to {OUT_DIR}")
    for inv in INVOICES:
        render_invoice(inv)
    print("Done.")
