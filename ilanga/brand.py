"""BioCollaborator visual identity for notebook outputs (renders in Colab & Jupyter)."""
from __future__ import annotations

import html as _html

NAVY, OCHRE, TEAL, FOREST, CREAM = "#0A2540", "#C85A32", "#1A7A6E", "#14283E", "#F7F1E3"
_FONTS = ("<link href='https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600;700&"
          "family=Inter:wght@400;600&display=swap' rel='stylesheet'>")
_BASE = "font-family:'IBM Plex Sans','Inter',Arial,sans-serif;"


def _show(markup: str, fallback: str) -> None:
    try:
        from IPython.display import HTML, display
        from IPython import get_ipython
        if get_ipython() is None:
            raise ImportError
        display(HTML(_FONTS + markup))
    except Exception:
        print(fallback)


def _e(x) -> str:
    return _html.escape(str(x))


def banner(module: int, title: str, phase: str, minutes: int = 90) -> None:
    markup = f"""
<div style="{_BASE}background:{NAVY};color:{CREAM};border-radius:14px;padding:26px 30px;
            border-left:10px solid {OCHRE};max-width:900px">
  <div style="font-size:12px;letter-spacing:3px;text-transform:uppercase;color:{OCHRE};font-weight:700">
    BioCollaborator &middot; Health Informatics Programme</div>
  <div style="font-size:30px;font-weight:700;margin:6px 0 4px">Module {module:02d} &mdash; {_e(title)}</div>
  <div style="font-size:15px;opacity:.9">{_e(phase)} &nbsp;|&nbsp; ~{minutes} minutes &nbsp;|&nbsp;
    You are a new analyst at <b>Nqaba Health Informatics</b>, contracted to <b>Ilanga District Health Services</b></div>
  <div style="margin-top:14px;font-size:13px;color:{TEAL};background:{CREAM};display:inline-block;
              padding:4px 12px;border-radius:20px;font-weight:600">Innovate Naturally</div>
</div>"""
    _show(markup, f"== Module {module:02d}: {title} | {phase} | BioCollaborator - Innovate Naturally ==")


def ticket(ticket_id: str, requester: str, role: str, summary: str, request: str,
           definition_of_done: list[str], priority: str = "Normal") -> None:
    dod = "".join(f"<li style='margin:3px 0'>{_e(d)}</li>" for d in definition_of_done)
    markup = f"""
<div style="{_BASE}border:2px solid {TEAL};border-radius:12px;max-width:900px;overflow:hidden">
  <div style="background:{TEAL};color:white;padding:10px 18px;display:flex;justify-content:space-between">
    <b>🎫 {_e(ticket_id)} &mdash; {_e(summary)}</b><span>Priority: {_e(priority)}</span></div>
  <div style="padding:14px 18px;background:{CREAM};color:{FOREST}">
    <div><b>From:</b> {_e(requester)}, <i>{_e(role)}</i></div>
    <p style="margin:10px 0;line-height:1.5">{_e(request)}</p>
    <b>Definition of done</b><ul style="margin:6px 0 0 0">{dod}</ul>
  </div>
</div>"""
    fallback = f"TICKET {ticket_id}: {summary}\nFrom {requester} ({role})\n{request}\nDone when:\n" + \
               "\n".join(f"  - {d}" for d in definition_of_done)
    _show(markup, fallback)


def gate_report(ticket_id: str, results: list[tuple[str, bool, str]]) -> bool:
    passed = all(ok for _, ok, _ in results)
    rows = "".join(
        f"<tr><td style='padding:6px 10px'>{'✅' if ok else '❌'}</td><td style='padding:6px 10px'>{_e(name)}</td>"
        f"<td style='padding:6px 10px;color:{OCHRE if not ok else TEAL}'>{_e('' if ok else hint)}</td></tr>"
        for name, ok, hint in results)
    head = (f"🚀 {ticket_id} passes the quality gate &mdash; ready for handover!" if passed
            else f"🔧 {ticket_id} is not ready yet &mdash; see the notes below. You've got this.")
    markup = f"""
<div style="{_BASE}max-width:900px;border-radius:12px;border:2px solid {TEAL if passed else OCHRE};overflow:hidden">
  <div style="background:{TEAL if passed else OCHRE};color:white;padding:10px 16px;font-weight:700">{head}</div>
  <table style="width:100%;border-collapse:collapse;background:{CREAM};color:{FOREST}">{rows}</table>
</div>"""
    fallback = head.replace("&mdash;", "-") + "\n" + "\n".join(
        f"  [{'PASS' if ok else 'FAIL'}] {n}" + ("" if ok else f"  -> {h}") for n, ok, h in results)
    _show(markup, fallback)
    return passed


def hint_box(ticket_id: str, level: int, text: str) -> None:
    markup = (f"<div style=\"{_BASE}max-width:900px;background:{CREAM};color:{FOREST};border-left:6px solid {OCHRE};"
              f"padding:10px 16px;border-radius:8px\"><b>💡 {ticket_id} hint {level}</b><br>{_e(text)}</div>")
    _show(markup, f"HINT {ticket_id}.{level}: {text}")
