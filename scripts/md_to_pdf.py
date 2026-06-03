"""Render a markdown file to a branded PDF (Allianz blue / Databricks style) with WeasyPrint.

Usage:
  python3 scripts/md_to_pdf.py <input.md> <output.pdf> "Title" "Subtitle" [img1 img2 ...]

Any trailing image paths are appended as a labelled "Demo assets" gallery so the
document reads as a self-contained brief.
"""
import sys, os, datetime
import markdown
from weasyprint import HTML

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCENT = "#003781"   # Allianz blue
ACCENT2 = "#0a6cff"

CSS = f"""
@page {{ size: A4; margin: 20mm 18mm 18mm 18mm;
  @bottom-center {{ content: counter(page) " / " counter(pages); font-size: 9px; color: #888; }} }}
@page :first {{ margin: 0; }}
* {{ font-family: 'Helvetica Neue', Arial, sans-serif; }}
body {{ color: #1c2230; font-size: 11px; line-height: 1.55; }}
.cover {{ height: 297mm; padding: 48mm 24mm 0; background: linear-gradient(150deg, {ACCENT} 0%, #00224f 100%); color: #fff; }}
.cover .kicker {{ font-size: 13px; letter-spacing: 3px; text-transform: uppercase; color: #9ec1ff; }}
.cover h1 {{ font-size: 40px; line-height: 1.1; margin: 14px 0 10px; font-weight: 800; }}
.cover .sub {{ font-size: 16px; color: #d7e4ff; max-width: 150mm; }}
.cover .meta {{ position: absolute; bottom: 26mm; font-size: 11px; color: #9ec1ff; }}
.cover .rule {{ width: 70mm; height: 5px; background: {ACCENT2}; margin: 20px 0; border: none; }}
h1, h2, h3 {{ color: {ACCENT}; line-height: 1.25; }}
h2 {{ font-size: 18px; margin-top: 22px; border-bottom: 2px solid #e6ebf2; padding-bottom: 5px; }}
h3 {{ font-size: 14px; margin-top: 16px; }}
p, li {{ font-size: 11px; }}
code {{ font-family: 'SF Mono', Menlo, monospace; background: #f1f4f8; padding: 1px 4px; border-radius: 3px; font-size: 10px; color: #b1004e; }}
pre {{ background: #0f1b2d; color: #e7eefc; padding: 12px 14px; border-radius: 6px; overflow-x: auto; }}
pre code {{ background: none; color: #e7eefc; padding: 0; font-size: 9.5px; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 10px; }}
th {{ background: {ACCENT}; color: #fff; text-align: left; padding: 6px 8px; }}
td {{ border: 1px solid #e2e7ee; padding: 6px 8px; vertical-align: top; }}
tr:nth-child(even) td {{ background: #f7f9fc; }}
blockquote {{ border-left: 4px solid {ACCENT2}; background: #f3f7ff; margin: 10px 0; padding: 8px 14px; color: #33415c; }}
a {{ color: {ACCENT2}; text-decoration: none; }}
.gallery {{ page-break-before: always; }}
.gallery h2 {{ margin-top: 0; }}
.shots {{ display: flex; flex-wrap: wrap; gap: 10px; }}
.shot {{ width: 48%; }}
.shot img {{ width: 100%; border: 1px solid #d7deea; border-radius: 6px; }}
.shot .cap {{ font-size: 9.5px; color: #5a6678; margin-top: 4px; }}
"""


def main():
    inp, outp, title = sys.argv[1], sys.argv[2], sys.argv[3]
    subtitle = sys.argv[4] if len(sys.argv) > 4 else ""
    images = sys.argv[5:]

    with open(inp) as f:
        md_text = f.read()
    # Drop the first H1 (we render our own cover title)
    lines = md_text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    body_html = markdown.markdown("\n".join(lines), extensions=["tables", "fenced_code", "toc", "sane_lists"])

    today = datetime.date.today().strftime("%d %B %Y")
    cover = f"""
    <div class='cover'>
      <div class='kicker'>Allianz UK &middot; Agent Bricks on Databricks</div>
      <h1>{title}</h1>
      <hr class='rule'>
      <div class='sub'>{subtitle}</div>
      <div class='meta'>Field Engineering &middot; {today}</div>
    </div>
    """

    gallery = ""
    if images:
        caps = {
            "clm_a_golf_front": "CLM-A - VW Golf: isolated front bumper + headlamp damage (clean claim, approve).",
            "clm_b_focus_wing": "CLM-B - Ford Focus: single damaged near-side wing.",
            "clm_b_focus_wide": "CLM-B - the rest of the car is pristine (sets up panel-stuffing detection).",
            "clm_c_synthetic": "CLM-C - deliberately AI-generated image (warped wheel, melted trim) - flagged as synthetic.",
            "clm_d_audi_totalled": "CLM-D - Audi A4: severe frontal collision (total-loss candidate).",
        }
        shots = ""
        for img in images:
            stem = os.path.splitext(os.path.basename(img))[0]
            cap = caps.get(stem, stem)
            shots += f"<div class='shot'><img src='{img}'><div class='cap'>{cap}</div></div>"
        gallery = f"<div class='gallery'><h2>Demo assets - mocked pre-repair photos</h2><div class='shots'>{shots}</div></div>"

    html = f"<html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{cover}{body_html}{gallery}</body></html>"
    HTML(string=html, base_url=BASE).write_pdf(outp)
    print(f"Wrote {outp}")


if __name__ == "__main__":
    main()
