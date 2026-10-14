"""
Build a single-file HTML dashboard: no server, no internet needed to view it, small enough to email.
Charts are embedded as images; a sub-district filter uses a few lines of plain JavaScript.
"""
from __future__ import annotations

import base64
import html
import io

from .brand import CREAM, FOREST, NAVY, OCHRE, TEAL

RAG_COLOURS = {"green": "#2E7D5B", "amber": "#C98A1B", "red": "#B23A2E"}


def rag(value, green_at, amber_at, higher_is_better=True) -> str:
    """Red / amber / green status for a KPI value."""
    if not higher_is_better:
        value, green_at, amber_at = -value, -green_at, -amber_at
    if value >= green_at:
        return "green"
    return "amber" if value >= amber_at else "red"


def fig_to_img(fig, alt: str = "chart") -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    data = base64.b64encode(buf.getvalue()).decode()
    return f'<img alt="{html.escape(alt)}" src="data:image/png;base64,{data}" style="max-width:100%">'


def build_dashboard(title: str, kpis: list, panels: list, subdistricts: list, notes: str = "",
                    period: str = "") -> str:
    """
    kpis   : list of dicts {label, value, unit, status, subdistrict ('All' or a name)}
    panels : list of dicts {title, html, subdistrict ('All' or a name)}
    """
    def card(k):
        colour = RAG_COLOURS.get(k.get("status"), TEAL)
        return (f'<div class="card" data-sd="{html.escape(k.get("subdistrict", "All"))}" style="border-top:6px solid {colour}">'
                f'<div class="lbl">{html.escape(k["label"])}</div>'
                f'<div class="val">{html.escape(str(k["value"]))}<span class="unit">{html.escape(k.get("unit", ""))}</span></div>'
                f'<div class="sd">{html.escape(k.get("subdistrict", "All"))}</div></div>')

    def panel(p):
        return (f'<div class="panel" data-sd="{html.escape(p.get("subdistrict", "All"))}">'
                f'<h3>{html.escape(p["title"])}</h3>{p["html"]}</div>')

    buttons = "".join(f'<button onclick="show(\'{html.escape(s)}\')">{html.escape(s)}</button>'
                      for s in ["All"] + list(subdistricts))
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
 body{{font-family:'IBM Plex Sans',Inter,Arial,sans-serif;margin:0;background:{CREAM};color:{FOREST}}}
 header{{background:{NAVY};color:{CREAM};padding:18px 28px;border-left:10px solid {OCHRE}}}
 header h1{{margin:0;font-size:24px}} header p{{margin:4px 0 0;opacity:.85}}
 .bar{{padding:12px 28px}} .bar button{{margin-right:6px;padding:6px 14px;border-radius:16px;border:2px solid {TEAL};
   background:white;color:{TEAL};font-weight:600;cursor:pointer}}
 .cards{{display:flex;flex-wrap:wrap;gap:12px;padding:0 28px}}
 .card{{background:white;border-radius:10px;padding:12px 16px;min-width:180px;flex:1;box-shadow:0 1px 3px #0002}}
 .lbl{{font-size:13px;opacity:.8}} .val{{font-size:28px;font-weight:700}} .unit{{font-size:14px;margin-left:3px}}
 .sd{{font-size:11px;color:{OCHRE};text-transform:uppercase;letter-spacing:1px}}
 .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:14px;padding:16px 28px}}
 .panel{{background:white;border-radius:10px;padding:12px 16px;box-shadow:0 1px 3px #0002}}
 .panel h3{{margin:0 0 8px;font-size:16px}}
 footer{{padding:14px 28px;font-size:12px;opacity:.8}}
 .legend span{{display:inline-block;width:10px;height:10px;border-radius:2px;margin:0 4px 0 12px}}
</style></head><body>
<header><h1>{html.escape(title)}</h1><p>{html.escape(period)}</p></header>
<div class="bar"><b>Sub-district:</b> {buttons}
 <span class="legend"><span style="background:{RAG_COLOURS['green']}"></span>On target
 <span style="background:{RAG_COLOURS['amber']}"></span>Watch <span style="background:{RAG_COLOURS['red']}"></span>Act</span></div>
<div class="cards">{''.join(card(k) for k in kpis)}</div>
<div class="grid">{''.join(panel(p) for p in panels)}</div>
<footer>{html.escape(notes)}<br>Prepared by Nqaba Health Informatics · BioCollaborator Health Informatics Programme ·
 Synthetic data - Ilanga District is fictional.</footer>
<script>
function show(sd){{document.querySelectorAll('[data-sd]').forEach(function(el){{
  var s=el.getAttribute('data-sd'); el.style.display=(sd==='All'||s===sd||s==='All')?'':'none';}});}}
</script></body></html>"""
