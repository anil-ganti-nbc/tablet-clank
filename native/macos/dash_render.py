"""HTML rendering for the Tablet Clank field-test dashboard.

Server-rendered strings, stdlib only - no template engine, no frontend
framework. Every dynamic value that could contain scraped/manufacturer text
goes through `esc()` before landing in a response.
"""

from __future__ import annotations

from html import escape as _html_escape

from dash_names import display_name, event_type_label, qc_decision_label

APP_NAME = "Tablet Clank"

NAV = [
    ("overview", "/", "OVERVIEW", None),
    ("queue", "/queue", "Active Queue", "QC"),
    ("qc-recent", "/qc/recent", "Recently QCed", "QC"),
    ("discoveries", "/discoveries", "Latest Discoveries", "DISCOVERY"),
    ("products", "/products", "Products", "DISCOVERY"),
    ("changes", "/changes", "Changes", "DISCOVERY"),
    ("sources-all", "/sources", "All Sources", "SOURCES"),
    ("sources-production", "/sources?scope=production", "Production", "SOURCES"),
    ("sources-experimental", "/sources?scope=experimental", "Experimental", "SOURCES"),
    ("source-health", "/sources/health", "Source Health", "SOURCES"),
    ("collect", "/collect", "Collect", "OPERATIONS"),
    ("runs", "/runs", "Run History", "OPERATIONS"),
    ("about", "/about", "About", "SYSTEM"),
]

HEALTH_CLASS = {
    "SUCCESS": "ok",
    "DEGRADED": "warn",
    "ZERO_ITEMS": "warn",
    "BLOCKED": "bad",
    "FAILED": "bad",
    "NEVER_RUN": "muted",
}


def esc(value) -> str:
    if value is None:
        return ""
    return _html_escape(str(value), quote=True)


from collector_ui import (  # noqa: E402  (sibling module, added to sys.path by the launchers)
    CSS as UI_CSS, DESIGN_SYSTEM_VERSION,
    badge as _ui_badge, empty as _ui_empty,
)

# Tablet Clank domain accent (the only visual token this Clank overrides).
ACCENT, ACCENT_SOFT = "#f59e0b", "#33240a"

# Only STATE words are family vocabulary. Domain labels -- QC decisions like
# "Useful"/"Not useful", relationship names -- are authored text and must keep
# their own wording and casing, so they are rendered as a plain chip instead of
# being forced through the shared status vocabulary.
_FAMILY_WORDS = {
    "finalized": "PRODUCTION", "soaking": "EXPERIMENTAL", "retired": "DISABLED",
    "SUCCESS": "SUCCESS", "DEGRADED": "DEGRADED", "ZERO_ITEMS": "DEGRADED",
    "BLOCKED": "BLOCKED", "FAILED": "FAILED", "NEVER_RUN": "UNKNOWN",
}
_TONES = {"accent": None, "muted": "", "bad": "bad", "good": "ok", "warn": "warn"}


def _badge(text: str, cls: str) -> str:
    if text in _FAMILY_WORDS:
        return _ui_badge(_FAMILY_WORDS[text], _TONES.get(cls))
    tone = _TONES.get(cls) or ""
    klass = "badge" + ((" " + tone) if tone else "")
    return f'<span class="{klass}">{esc(text)}</span>'


def _health_badge(health: str) -> str:
    return _badge(health.replace("_", " "), HEALTH_CLASS.get(health, "muted"))


def _fmt_time(value) -> str:
    return esc(value) if value else "—"


CSS = """
:root {
  --bg: #0a0d12; --bg2: #11151c; --bg3: #171c25; --border: #262d38;
  --text: #e6edf3; --muted: #7d8797; --accent: #58a6ff;
  --green: #3fb950; --yellow: #d29922; --red: #f85149; --purple: #a371f7;
  --sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  --mono: "SF Mono", "Cascadia Code", Consolas, monospace;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font-family: var(--sans); font-size: 13px; line-height: 1.45; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.shell { display: flex; min-height: 100vh; }
.sidebar { width: 200px; flex: 0 0 200px; background: var(--bg2); border-right: 1px solid var(--border); padding: 14px 0; position: sticky; top: 0; height: 100vh; overflow-y: auto; }
.brand { padding: 0 14px 14px; font-weight: 700; letter-spacing: 0.02em; font-size: 13px; border-bottom: 1px solid var(--border); margin-bottom: 10px; }
.brand .sub { display: block; margin-top: 4px; }
.navlabel { padding: 10px 14px 4px; font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
.navitem { display: block; padding: 5px 14px; color: var(--muted); font-size: 12px; border-left: 2px solid transparent; }
.navitem:hover { color: var(--text); text-decoration: none; background: var(--bg3); }
.navitem.active { color: var(--accent); border-left-color: var(--accent); background: var(--bg3); }
.main { flex: 1; min-width: 0; }
header.topbar { background: var(--bg2); border-bottom: 1px solid var(--border); padding: 8px 20px; display: flex; align-items: center; gap: 14px; font-size: 11px; color: var(--muted); flex-wrap: wrap; }
header.topbar b { color: var(--text); }
.content { padding: 18px 22px 50px; max-width: 1300px; }
h1 { font-size: 18px; margin: 0 0 4px; }
h2 { font-size: 14px; margin: 0 0 8px; color: var(--text); }
.pagesub { color: var(--muted); font-size: 12px; margin-bottom: 16px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 18px; }
.card { background: var(--bg2); border: 1px solid var(--border); border-radius: 6px; padding: 12px 14px; }
.card .value { font-size: 22px; font-weight: 700; }
.card .label { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2px; }
.panel { background: var(--bg2); border: 1px solid var(--border); border-radius: 6px; padding: 14px 16px; margin-bottom: 16px; }
table { width: 100%; border-collapse: collapse; font-size: 12px; }
th { text-align: left; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--border); padding: 5px 8px; font-size: 10px; text-transform: uppercase; letter-spacing: 0.03em; }
td { padding: 6px 8px; border-bottom: 1px solid var(--bg3); vertical-align: top; }
tr.clickable:hover td { background: var(--bg3); cursor: pointer; }
.badge { display: inline-block; padding: 2px 7px; border-radius: 3px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em; border: 1px solid var(--border); }
.badge.ok { color: var(--green); border-color: var(--green); }
.badge.warn { color: var(--yellow); border-color: var(--yellow); }
.badge.bad { color: var(--red); border-color: var(--red); }
.badge.muted { color: var(--muted); }
.badge.accent { color: var(--accent); border-color: var(--accent); }
.badge.fieldtest { color: var(--purple); border-color: var(--purple); }
.mono { font-family: var(--mono); }
.muted { color: var(--muted); }
.filters { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; align-items: center; }
select, button, .btn { background: var(--bg3); border: 1px solid var(--border); color: var(--text); padding: 5px 10px; border-radius: 4px; font-size: 12px; cursor: pointer; }
select:hover, button:hover, .btn:hover { border-color: var(--accent); }
button:disabled { opacity: 0.5; cursor: default; }
.empty { color: var(--muted); padding: 30px 10px; text-align: center; font-size: 13px; }
.empty .big { font-size: 14px; color: var(--text); margin-bottom: 6px; }
.detail-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px 20px; margin-bottom: 4px; }
.detail-grid div span.k { display: block; color: var(--muted); font-size: 10px; text-transform: uppercase; letter-spacing: 0.04em; }
.detail-grid div span.v { font-size: 13px; }
.runbox { margin-top: 10px; padding: 10px 12px; border-radius: 4px; background: var(--bg3); border: 1px solid var(--border); font-size: 12px; }
.runbox.running { border-color: var(--accent); color: var(--accent); }
.runbox.success { border-color: var(--green); }
.runbox.error { border-color: var(--red); }
.source-name { font-weight: 600; }
.source-id { color: var(--muted); font-size: 10px; }
"""


def layout(active: str, title: str, content: str, topbar: dict | None = None) -> bytes:
    nav_html = []
    last_group = None
    for key, href, label, group in NAV:
        if group != last_group and group is not None:
            nav_html.append(f'<div class="rail-group">{esc(group)}</div>')
            last_group = group
        elif group is None:
            last_group = None
        cls = "nav active" if key == active else "nav"
        nav_html.append(f'<a class="{cls}" href="{esc(href)}">{esc(label)}</a>')

    top = topbar or {}
    topbar_html = (
        f'<b>{esc(APP_NAME)}</b>'
        f'<span>{_badge("FIELD TEST", "fieldtest")}</span>'
        f'<span>rev {esc(top.get("build_revision", "—"))}</span>'
        f'<span>DB integrity: <b>{esc(top.get("integrity", "—"))}</b></span>'
        f'<span>alerts: <b>{esc(top.get("alerts_enabled", False))}</b></span>'
        f'<span>delivery disabled</span>'
    )

    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{esc(title)} — {esc(APP_NAME)}</title>
<style>{UI_CSS}
:root{{--accent:{ACCENT};--accent-soft:{ACCENT_SOFT};}}</style></head>
<body>
<div class="app">
<header class="topbar">
  <div class="brand"><span class="brand-mark">TB</span>
  <span class="brand-name">Tablet Clank</span>
  <span class="brand-suite">Clank Fleet</span></div>
  <div class="topbar-meta">{topbar_html}</div>
</header>
<div class="body">
<nav class="rail">{''.join(nav_html)}</nav>
<main class="main"><div class="wrap">{content}</div></main>
</div>
</div>
</body></html>""".encode("utf-8")


# ---------------------------------------------------------------- overview


def render_overview(data: dict) -> str:
    c = data["counts"]
    last_run = data.get("last_run")
    last_run_html = (
        f'{esc(display_name(last_run["source_id"]))} — <b>{esc(last_run["status"])}</b> · {_fmt_time(last_run["finished_at"])}'
        if last_run
        else "No runs yet"
    )
    return f"""
<h1>Overview</h1>
<p class="page-sub">What Tablet Clank has found so far, at a glance.</p>
<div class="cols">
  <div class="panel pad"><div class="value">{c['products']}</div><div class="label">Products</div></div>
  <div class="panel pad"><div class="value">{c['observations']}</div><div class="label">Observations</div></div>
  <div class="panel pad"><div class="value">{c['change_events']}</div><div class="label">Recent changes</div></div>
  <div class="panel pad"><div class="value">{data['sources_healthy']}/{data['sources_total']}</div><div class="label">Sources healthy</div></div>
</div>
<div class="panel"><h2>Last run</h2><p>{last_run_html}</p></div>
"""


# ------------------------------------------------------------ discoveries


def render_discoveries(data: dict) -> str:
    events = data["events"]
    if not events:
        body = f"""
<div class="empty">
  <div class="big">No post-baseline changes detected yet.</div>
  {data['product_count']} products are currently baselined across {data['source_count']} active sources.
</div>"""
    else:
        rows = "".join(
            f"""<tr class="clickable" onclick="location.href='/products/{e['product_id']}'">
<td>{_badge(event_type_label(e['event_type']), 'accent')}</td>
<td>{esc(e['manufacturer'])} {esc(e['name'])}</td>
<td>{esc(display_name(e['source_id']))}</td>
<td>{esc(e.get('product_region'))}</td>
<td class="mono muted">{_fmt_time(e['observed_at'])}</td>
<td>{f'<a href="{esc(e["evidence_url"])}" target="_blank" onclick="event.stopPropagation()">evidence</a>' if e.get('evidence_url') else '—'}</td>
</tr>"""
            for e in events
        )
        body = f"""
<table class="t"><thead><tr><th>Type</th><th>Product</th><th>Source</th><th>Region</th><th>Observed</th><th>Evidence</th></tr></thead>
<tbody>{rows}</tbody></table>"""
    return f"""
<h1>Latest Discoveries</h1>
<p class="page-sub">Meaningful post-baseline changes, most recent first.</p>
{body}
"""


# --------------------------------------------------------------- QC queue


def _qc_script(event_id: int) -> str:
    return f"""
<script>
(function() {{
  var deciding = false;
  document.querySelectorAll('.qc-btn').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
      if (deciding) return;
      deciding = true;
      document.querySelectorAll('.qc-btn').forEach(function(b) {{ b.disabled = true; }});
      var box = document.getElementById('qc-result');
      box.innerHTML = '<div class="runbox running">Recording decision…</div>';
      fetch('/qc?event_id={event_id}&decision=' + encodeURIComponent(btn.getAttribute('data-decision')), {{method: 'POST'}})
        .then(function(r) {{ return r.json().then(function(body) {{ return {{ok: r.ok, status: r.status, body: body}}; }}); }})
        .then(function(res) {{
          if (res.ok) {{
            box.innerHTML = '<div class="runbox success"><b>RECORDED</b> — ' + res.body.decision + '</div>';
            setTimeout(function() {{ location.href = '/queue'; }}, 700);
          }} else if (res.status === 409) {{
            box.innerHTML = '<div class="runbox error"><b>ALREADY QCED</b> — this item was already decided.</div>';
          }} else {{
            box.innerHTML = '<div class="runbox error"><b>FAILED</b><br>' + (res.body.error || 'unknown error') + '</div>';
            deciding = false;
            document.querySelectorAll('.qc-btn').forEach(function(b) {{ b.disabled = false; }});
          }}
        }})
        .catch(function(err) {{
          box.innerHTML = '<div class="runbox error">request error: ' + err + '</div>';
          deciding = false;
          document.querySelectorAll('.qc-btn').forEach(function(b) {{ b.disabled = false; }});
        }});
    }});
  }});
}})();
</script>"""


def _qc_buttons() -> str:
    return (
        '<div class="filters">'
        '<button class="btn qc-btn" data-decision="USEFUL">Useful</button>'
        '<button class="btn qc-btn" data-decision="NOT_USEFUL">Not useful</button>'
        '<button class="btn qc-btn" data-decision="FALSE_POSITIVE">False positive</button>'
        '<button class="btn qc-btn" data-decision="OUT_OF_STOCK">Out of stock</button>'
        "</div>"
    )


def render_queue(data: dict) -> str:
    events = data["events"]
    if not events:
        body = f"""
<div class="empty">
  <div class="big">Active queue is empty.</div>
  {data['total_events']} event(s) recorded, {data['decided_count']} already QC'd. A quiet queue after the first
  collector run is expected — the first run establishes a baseline, it does not flood the queue.
</div>"""
    else:
        rows = "".join(
            f"""<tr class="clickable" onclick="location.href='/queue/{e['id']}'">
<td>{_badge(event_type_label(e['event_type']), 'accent')}</td>
<td>{esc(e['manufacturer'])} {esc(e['name'])}</td>
<td>{esc(display_name(e['source_id']))}</td>
<td>{esc(e.get('old_value'))} → {esc(e.get('new_value'))}</td>
<td class="mono muted">{_fmt_time(e['observed_at'])}</td>
</tr>"""
            for e in events
        )
        body = f"""
<table class="t"><thead><tr><th>Type</th><th>Product</th><th>Source</th><th>Change</th><th>Observed</th></tr></thead>
<tbody>{rows}</tbody></table>"""
    return f"""
<h1>Active Queue</h1>
<p class="page-sub">{len(events)} lead(s) awaiting a QC decision. Click a row for detail and to decide.</p>
{body}
"""


def render_queue_item(data: dict) -> str:
    e = data["event"]
    fields = [
        ("Manufacturer", e.get("manufacturer")),
        ("Product", e.get("name")),
        ("Model", e.get("model_number")),
        ("SKU", e.get("sku")),
        ("Region", e.get("product_region")),
        ("Variant", e.get("variant")),
        ("Connectivity", e.get("connectivity")),
        ("RAM", f"{e['ram_gb']} GB" if e.get("ram_gb") else None),
        ("Storage", f"{e['storage_gb']} GB" if e.get("storage_gb") else None),
        ("Colour", e.get("colour")),
        ("Processor", e.get("processor")),
        ("Display", f"{e['display_size_in']}\"" if e.get("display_size_in") else None),
        ("OS", e.get("os")),
        ("Identity key", e.get("identity_key")),
        ("First observed", e.get("first_seen")),
        ("Last observed", e.get("last_seen")),
    ]
    detail_html = "".join(
        f'<div><span class="k">{esc(k)}</span><span class="v">{esc(v) if v else "—"}</span></div>' for k, v in fields
    )
    obs_rows = "".join(
        f"""<tr><td>{esc(display_name(o['source_id']))}</td><td class="mono muted">{_fmt_time(o['observed_at'])}</td>
<td>{esc(o['collector'])}</td><td><a href="{esc(o['url'])}" target="_blank">evidence</a></td></tr>"""
        for o in data["observations"]
    ) or '<tr><td colspan="4" class="muted">No observations.</td></tr>'
    return f"""
<p class="page-sub"><a href="/queue">&larr; Active Queue</a></p>
<h1>{_badge(event_type_label(e['event_type']), 'accent')} {esc(e['manufacturer'])} {esc(e['name'])}</h1>
<p class="pagesub mono">event #{e['id']} · run #{e.get('run_id') if e.get('run_id') is not None else '—'} · source {esc(e['source_id'])} ({esc(display_name(e['source_id']))})</p>
<div class="panel">
  <h2>What changed</h2>
  <p>{esc(e.get('old_value'))} &rarr; <b>{esc(e.get('new_value'))}</b></p>
  <p class="muted">Observed {_fmt_time(e['observed_at'])} · <a href="{esc(e['evidence_url'])}" target="_blank">evidence</a> · confidence {e.get('confidence')}</p>
</div>
<div class="panel"><h2>Item detail</h2><div class="detail-grid">{detail_html}</div></div>
<div class="panel"><h2>QC decision</h2>{_qc_buttons()}<div id="qc-result"></div></div>
<div class="panel"><h2>Observation history ({len(data['observations'])})</h2>
<table class="t"><thead><tr><th>Source</th><th>Observed</th><th>Collector</th><th>Evidence</th></tr></thead><tbody>{obs_rows}</tbody></table></div>
{_qc_script(e['id'])}
"""


def render_qc_recent(rows: list[dict]) -> str:
    if not rows:
        body = '<div class="empty">No QC decisions recorded yet.</div>'
    else:
        row_html = "".join(
            f"""<tr>
<td>{_badge(qc_decision_label(r['decision']), 'accent')}</td>
<td>{esc(r['manufacturer'])} {esc(r['product_name'])}</td>
<td>{esc(display_name(r['source_id']))}</td>
<td>{_badge(event_type_label(r['event_type']), 'muted')}</td>
<td>{esc(r.get('old_value'))} → {esc(r.get('new_value'))}</td>
<td class="mono muted">{_fmt_time(r['decided_at'])}</td>
<td>{f'<a href="{esc(r["evidence_url"])}" target="_blank">evidence</a>' if r.get('evidence_url') else '—'}</td>
</tr>"""
            for r in rows
        )
        body = f"""<table class="t"><thead><tr><th>Decision</th><th>Product</th><th>Source</th><th>Event type</th><th>Change</th><th>Decided</th><th>Evidence</th></tr></thead>
<tbody>{row_html}</tbody></table>"""
    return f"""
<h1>Recently QCed</h1>
<p class="page-sub">{len(rows)} most recent decision(s), from the separate QC archive — full provenance preserved, nothing deleted.</p>
{body}
"""


# ---------------------------------------------------------------- products


def render_products(data: dict) -> str:
    opts = data["filter_options"]
    applied = data["applied"]

    def _select(name, values, current, label_fn=None):
        options = ['<option value="">All</option>']
        for v in values:
            sel = " selected" if v == current else ""
            label = label_fn(v) if label_fn else v
            options.append(f'<option value="{esc(v)}"{sel}>{esc(label)}</option>')
        return f'<select name="{name}" onchange="this.form.submit()">{"".join(options)}</select>'

    filters_html = f"""
<form method="get" class="filters">
  {_select('manufacturer', opts['manufacturers'], applied['manufacturer'])}
  {_select('region', opts['regions'], applied['region'])}
  {_select('source', opts['source_ids'], applied['source'], display_name)}
  {_select('membership', ['production', 'experimental'], applied['membership'])}
</form>"""

    rows = data["rows"]
    if not rows:
        body = '<div class="empty">No products match these filters.</div>'
    else:
        row_html = "".join(
            f"""<tr class="clickable" onclick="location.href='/products/{p['id']}'">
<td>{esc(p['manufacturer'])}</td>
<td>{esc(p['name'])}</td>
<td>{esc(p['region'])}</td>
<td>{esc(', '.join(display_name(s) for s in p['source_ids']))}</td>
<td class="mono muted">{_fmt_time(p['last_seen'])}</td>
</tr>"""
            for p in rows
        )
        body = f"""<table class="t"><thead><tr><th>Manufacturer</th><th>Product</th><th>Region</th><th>Sources</th><th>Last seen</th></tr></thead>
<tbody>{row_html}</tbody></table>"""

    return f"""
<h1>Products</h1>
<p class="page-sub">{len(rows)} product(s) in the current baseline.</p>
{filters_html}
{body}
"""


def render_product_detail(data: dict) -> str:
    p = data["product"]
    fields = [
        ("Manufacturer", p.get("manufacturer")),
        ("Model", p.get("model_number")),
        ("SKU", p.get("sku")),
        ("Region", p.get("region")),
        ("Variant", p.get("variant")),
        ("Connectivity", p.get("connectivity")),
        ("RAM", f"{p['ram_gb']} GB" if p.get("ram_gb") else None),
        ("Storage", f"{p['storage_gb']} GB" if p.get("storage_gb") else None),
        ("Colour", p.get("colour")),
        ("Processor", p.get("processor")),
        ("Display", f"{p['display_size_in']}\"" if p.get("display_size_in") else None),
        ("OS", p.get("os")),
        ("First observed", p.get("first_seen")),
        ("Last observed", p.get("last_seen")),
    ]
    detail_html = "".join(
        f'<div><span class="k">{esc(k)}</span><span class="v">{esc(v) if v else "—"}</span></div>' for k, v in fields
    )

    obs_rows = "".join(
        f"""<tr><td>{esc(display_name(o['source_id']))}</td><td class="mono muted">{_fmt_time(o['observed_at'])}</td>
<td>{esc(o['collector'])}</td><td><a href="{esc(o['url'])}" target="_blank">evidence</a></td></tr>"""
        for o in data["observations"]
    ) or '<tr><td colspan="4" class="muted">No observations.</td></tr>'

    events = data["events"]
    events_html = (
        "".join(
            f"""<tr><td>{_badge(event_type_label(e['event_type']), 'accent')}</td>
<td>{esc(e.get('old_value'))} → {esc(e.get('new_value'))}</td>
<td class="mono muted">{_fmt_time(e['observed_at'])}</td></tr>"""
            for e in events
        )
        if events
        else '<tr><td colspan="3" class="muted">No post-baseline events for this product.</td></tr>'
    )

    return f"""
<p class="page-sub"><a href="/products">&larr; Products</a></p>
<h1>{esc(p['manufacturer'])} {esc(p['name'])}</h1>
<p class="pagesub mono">identity_key: {esc(p['identity_key'])}</p>
<div class="panel"><div class="detail-grid">{detail_html}</div></div>
<div class="panel"><h2>Observation history ({len(data['observations'])})</h2>
<table class="t"><thead><tr><th>Source</th><th>Observed</th><th>Collector</th><th>Evidence</th></tr></thead><tbody>{obs_rows}</tbody></table></div>
<div class="panel"><h2>Related events ({len(events)})</h2>
<table class="t"><thead><tr><th>Type</th><th>Change</th><th>Observed</th></tr></thead><tbody>{events_html}</tbody></table></div>
"""


# ------------------------------------------------------------------ changes


def render_changes(data: dict) -> str:
    rows = data["rows"]
    types = data["types"]
    applied = data["applied_type"]
    filter_html = ""
    if types:
        opts = ['<option value="">All types</option>'] + [
            f'<option value="{esc(t)}"{" selected" if t == applied else ""}>{esc(event_type_label(t))}</option>' for t in types
        ]
        filter_html = f'<form method="get" class="filters"><select name="event_type" onchange="this.form.submit()">{"".join(opts)}</select></form>'

    if not rows:
        body = f"""
<div class="empty">
  <div class="big">No post-baseline changes detected yet.</div>
  {data['product_count']} products are currently baselined. Baseline observations are not editorial events.
</div>"""
    else:
        row_html = "".join(
            f"""<tr class="clickable" onclick="location.href='/products/{e['product_id']}'">
<td>{_badge(event_type_label(e['event_type']), 'accent')}</td>
<td>{esc(e['manufacturer'])} {esc(e['name'])}</td>
<td>{esc(display_name(e['source_id']))}</td>
<td>{esc(e.get('old_value'))} → {esc(e.get('new_value'))}</td>
<td class="mono muted">{_fmt_time(e['observed_at'])}</td>
</tr>"""
            for e in rows
        )
        body = f"""<table class="t"><thead><tr><th>Type</th><th>Product</th><th>Source</th><th>Change</th><th>Observed</th></tr></thead>
<tbody>{row_html}</tbody></table>"""

    return f"""
<h1>Changes</h1>
<p class="page-sub">Post-baseline events only — distinct from initial baseline observations.</p>
{filter_html}
{body}
"""


# ------------------------------------------------------------------ sources


def render_sources(rows: list[dict], scope: str | None) -> str:
    title = {"production": "Production Sources", "experimental": "Experimental Sources"}.get(scope, "All Sources")
    row_html = "".join(
        f"""<tr>
<td><span class="source-name">{esc(display_name(r['id']))}</span><br><span class="source-id mono">{esc(r['id'])}</span></td>
<td>{esc(r['manufacturer'])}</td><td>{esc(r['region'])}</td>
<td>{_badge('production' if r['production'] else r['state'].lower(), 'accent' if r['production'] else 'muted')}</td>
<td>{_health_badge(r['health'])}</td>
<td class="mono muted">{_fmt_time(r['last_finished_at'])}</td>
<td class="mono muted">{_fmt_time(r['last_success_at'])}</td>
<td>{'<button class="btn collect-btn" data-source="' + esc(r['id']) + '">Collect Now</button>' if r['state'] == 'EXPERIMENTAL' else '<span class="muted">unavailable</span>'}</td>
</tr>"""
        for r in rows
    )
    return f"""
<h1>{esc(title)}</h1>
<p class="page-sub">{len(rows)} source(s). Membership (production/experimental) and current health are separate concepts.</p>
<table class="t"><thead><tr><th>Source</th><th>Manufacturer</th><th>Region</th><th>Membership</th><th>Health</th><th>Last run</th><th>Last success</th><th>Action</th></tr></thead>
<tbody>{row_html}</tbody></table>
<div id="collect-result"></div>
{_collect_script()}
"""


def render_source_health(rows: list[dict]) -> str:
    row_html = "".join(
        f"""<tr>
<td><span class="source-name">{esc(display_name(r['id']))}</span></td>
<td>{_health_badge(r['health'])}</td>
<td class="mono muted">{_fmt_time(r['last_finished_at'])}</td>
<td class="mono muted">{_fmt_time(r['last_success_at'])}</td>
<td class="mono">{r['last_item_count'] if r['last_item_count'] is not None else '—'}</td>
<td class="muted">{esc(r['last_error']) if r['last_error'] else '—'}</td>
</tr>"""
        for r in rows
    )
    return f"""
<h1>Source Health</h1>
<p class="page-sub">Derived from the most recent collector run per source.</p>
<table class="t"><thead><tr><th>Source</th><th>Health</th><th>Last run</th><th>Last success</th><th>Last item count</th><th>Note</th></tr></thead>
<tbody>{row_html}</tbody></table>
"""


# --------------------------------------------------------------- operations


def _collect_script() -> str:
    return """
<script>
(function() {
  var collecting = false;
  function bind() {
    document.querySelectorAll('.collect-btn').forEach(function(btn) {
      btn.addEventListener('click', function() { runCollect(btn.getAttribute('data-source')); });
    });
  }
  function runCollect(source) {
    if (collecting) return;
    collecting = true;
    document.querySelectorAll('.collect-btn').forEach(function(b) { b.disabled = true; });
    var box = document.getElementById('collect-result');
    var startedAt = new Date();
    var timer = setInterval(function() {
      var elapsed = ((new Date() - startedAt) / 1000).toFixed(0);
      box.innerHTML = '<div class="runbox running"><b>RUNNING</b> — ' + source + '<br>Elapsed ' + elapsed + 's</div>';
    }, 500);
    box.innerHTML = '<div class="runbox running"><b>RUNNING</b> — ' + source + '<br>Elapsed 0s</div>';
    fetch('/collect?source=' + encodeURIComponent(source), {method: 'POST'})
      .then(function(r) { return r.json().then(function(body) { return {ok: r.ok, status: r.status, body: body}; }); })
      .then(function(res) {
        clearInterval(timer);
        if (res.status === 409) {
          box.innerHTML = '<div class="runbox error"><b>ALREADY RUNNING</b><br>' + (res.body.detail || '') + '</div>';
        } else if (res.ok && res.body.status === 'success') {
          box.innerHTML = '<div class="runbox success"><b>SUCCESS</b><br>' + res.body.accepted + ' items observed &middot; ' +
            res.body.new + ' new &middot; ' + res.body.resighted + ' resighted &middot; ' + (res.body.duration_seconds || '?') + 's</div>';
        } else {
          box.innerHTML = '<div class="runbox error"><b>FAILED</b><br>' + (res.body.error || res.body.detail || 'unknown error') + '</div>';
        }
        setTimeout(function() { location.reload(); }, 1600);
      })
      .catch(function(err) {
        clearInterval(timer);
        box.innerHTML = '<div class="runbox error"><b>FAILED</b><br>request error: ' + err + '</div>';
        collecting = false;
        document.querySelectorAll('.collect-btn').forEach(function(b) { b.disabled = false; });
      });
  }
  bind();
})();
</script>"""


def _run_all_script() -> str:
    return """
<script>
(function() {
  var running = false;
  var btn = document.getElementById('run-all-btn');
  if (!btn) return;
  btn.addEventListener('click', function() {
    if (running) return;
    running = true;
    btn.disabled = true;
    document.querySelectorAll('.collect-btn').forEach(function(b) { b.disabled = true; });
    var box = document.getElementById('run-all-result');
    box.innerHTML = '<div class="runbox running">Running all finalized collectors…</div>';
    fetch('/collect/all', {method: 'POST'})
      .then(function(r) { return r.json().then(function(body) { return {ok: r.ok, status: r.status, body: body}; }); })
      .then(function(res) {
        if (res.status === 409) {
          box.innerHTML = '<div class="runbox error"><b>ALREADY RUNNING</b><br>' + (res.body.detail || '') + '</div>';
        } else if (res.ok) {
          var lines = (res.body.sources || []).map(function(s) { return s.source + ': ' + s.health; }).join('<br>');
          box.innerHTML = '<div class="runbox ' + (res.body.status === 'SUCCESS' ? 'success' : 'error') + '"><b>' + res.body.status + '</b><br>' + lines + '</div>';
        } else {
          box.innerHTML = '<div class="runbox error"><b>FAILED</b><br>' + (res.body.detail || res.body.error || 'unknown error') + '</div>';
        }
        setTimeout(function() { location.reload(); }, 1800);
      })
      .catch(function(err) {
        box.innerHTML = '<div class="runbox error">request error: ' + err + '</div>';
        running = false;
        btn.disabled = false;
        document.querySelectorAll('.collect-btn').forEach(function(b) { b.disabled = false; });
      });
  });
})();
</script>"""


def render_collect(rows: list[dict], empty: bool) -> str:
    if empty:
        body = """
<div class="empty">
  <div class="big">No tablet data collected yet.</div>
  Choose a source below to establish a local baseline.
</div>"""
    else:
        body = ""

    row_html = "".join(
        f"""<tr>
<td><span class="source-name">{esc(display_name(r['id']))}</span><br><span class="source-id mono">{esc(r['id'])}</span></td>
<td>{esc(r['manufacturer'])}</td><td>{esc(r['region'])}</td>
<td>{_badge('finalized', 'accent') if r['production'] else (_badge('soaking', 'muted') if r['state'] == 'EXPERIMENTAL' else _badge('retired', 'bad'))}</td>
<td>{_health_badge(r['health'])}</td>
<td class="mono muted">{_fmt_time(r['last_finished_at'])}</td>
<td>{'<button class="btn collect-btn" data-source="' + esc(r['id']) + '">Collect Now</button>' if r['state'] == 'EXPERIMENTAL' else '<span class="muted">unavailable</span>'}</td>
</tr>"""
        for r in rows
    )
    return f"""
<h1>Collect</h1>
<p class="page-sub">Live, single-source collection — mirrors the CLI's proven <span class="mono">collect &lt;source&gt; --live</span> path. Launching this GUI never runs a collector by itself.</p>
<div class="panel">
  <h2>Run all finalized collectors</h2>
  <p class="muted">Runs exactly the production-approved allowlist, serially, under the shared collection lock — mirrors <span class="mono">tablet-clank production</span>. Soaking/experimental and retired sources are never included, even by accident.</p>
  <button class="btn" id="run-all-btn">Run all finalized collectors</button>
  <div id="run-all-result"></div>
</div>
{body}
<table class="t"><thead><tr><th>Source</th><th>Manufacturer</th><th>Region</th><th>Maturity</th><th>Health</th><th>Last run</th><th>Action</th></tr></thead>
<tbody>{row_html}</tbody></table>
<div id="collect-result"></div>
{_collect_script()}
{_run_all_script()}
"""


def render_runs(rows: list[dict]) -> str:
    if not rows:
        body = '<div class="empty">No collector runs yet.</div>'
    else:
        row_html = "".join(
            f"""<tr>
<td>{esc(display_name(r['source_id']))}</td>
<td class="mono muted">{_fmt_time(r['started_at'])}</td>
<td class="mono muted">{_fmt_time(r['finished_at'])}</td>
<td class="mono">{r['duration_seconds'] if r['duration_seconds'] is not None else '—'}s</td>
<td>{_health_badge(r['health'])}</td>
<td class="mono">{r['accepted_count']}</td>
<td class="mono">{r['new_count']}</td>
<td class="muted">{esc(r['error']) if r['error'] else '—'}</td>
</tr>"""
            for r in rows
        )
        body = f"""<table class="t"><thead><tr><th>Source</th><th>Started</th><th>Finished</th><th>Duration</th><th>Status</th><th>Accepted</th><th>New</th><th>Error</th></tr></thead>
<tbody>{row_html}</tbody></table>"""
    return f"""
<h1>Run History</h1>
<p class="page-sub">{len(rows)} recorded run(s), most recent first.</p>
{body}
"""


# --------------------------------------------------------------------- about


def render_about(data: dict) -> str:
    sources_html = "".join(f"<li>{esc(display_name(s))} <span class='muted mono'>({esc(s)})</span></li>" for s in data["runtime_sources"])
    production_html = "".join(f"<li>{esc(display_name(s))}</li>" for s in data["production_allowlist"])
    return f"""
<h1>About</h1>
<div class="panel">
<div class="detail-grid">
<div><span class="k">Build revision</span><span class="v mono">{esc(data['build_revision'])}</span></div>
<div><span class="k">DB integrity</span><span class="v">{esc(data['integrity'])}</span></div>
<div><span class="k">Alerts enabled</span><span class="v">{esc(data['alerts_enabled'])}</span></div>
<div><span class="k">External delivery</span><span class="v">disabled</span></div>
<div><span class="k">Operation mode</span><span class="v">loopback-only field test</span></div>
</div>
</div>
<div class="panel"><h2>Production-approved sources</h2><ul>{production_html}</ul></div>
<div class="panel"><h2>All runtime sources</h2><ul>{sources_html}</ul></div>
"""
