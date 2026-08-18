"""Minimal read-only field-test dashboard for the Tablet Clank Finder launcher.

Deliberately outside the `tablet_clank` package: the core library stays
dependency-free and dashboard-free (see HANDOFF.md). This is a thin,
stdlib-only HTTP layer bolted on for the packaged macOS client only.

"Collect Now" mirrors the CLI's already-proven `collect <source> --live`
path exactly: same collector-class selection, same SoakLock manual-collect
lock domain, same pipeline.process() call, live network. No production
cycle, no scheduler, no alerts — ALERTS_ENABLED is never touched here.
"""

from __future__ import annotations

import json
import sys
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tablet_clank.collectors.apple_store import AppleStoreIPadProCollector  # noqa: E402
from tablet_clank.collectors.honor_cn import HonorCNTabletsCollector  # noqa: E402
from tablet_clank.collectors.html_catalogue import HtmlCatalogueCollector  # noqa: E402
from tablet_clank.collectors.tcl_global import TCLGlobalTabletsCollector  # noqa: E402
from tablet_clank.collectors.xml_sitemap import XmlSitemapCollector  # noqa: E402
from tablet_clank.pipeline import process  # noqa: E402
from tablet_clank.soak import SoakLock, SoakLockError, lock_path_for_db  # noqa: E402
from tablet_clank.sources.registry import ALERTS_ENABLED, PRODUCTION_ALLOWLIST, SOURCES, runtime_source_ids  # noqa: E402
from tablet_clank.storage.db import Database  # noqa: E402

APP_NAME = "Tablet Clank"


def _collector_class(source):
    if source.manufacturer == "Honor":
        return HonorCNTabletsCollector
    if source.manufacturer == "TCL":
        return TCLGlobalTabletsCollector
    if "Apple Store" in source.kind:
        return AppleStoreIPadProCollector
    return XmlSitemapCollector if "XML" in source.kind else HtmlCatalogueCollector


def _dashboard_data(db_path: Path) -> dict:
    db = Database(str(db_path))
    try:
        counts = {
            "products": db.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "observations": db.conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0],
            "change_events": db.conn.execute("SELECT COUNT(*) FROM change_events").fetchone()[0],
            "collector_runs": db.conn.execute("SELECT COUNT(*) FROM collector_runs").fetchone()[0],
        }
        rows = []
        for source_id in runtime_source_ids():
            source = SOURCES[source_id]
            run = db.conn.execute(
                "SELECT status, finished_at FROM collector_runs WHERE source_id=? ORDER BY id DESC LIMIT 1",
                (source_id,),
            ).fetchone()
            rows.append(
                {
                    "id": source_id,
                    "manufacturer": source.manufacturer,
                    "region": source.region,
                    "production": source_id in PRODUCTION_ALLOWLIST,
                    "last_status": run["status"] if run else "never run",
                    "last_finished_at": run["finished_at"] if run else None,
                }
            )
        integrity = db.integrity()
        return {"counts": counts, "sources": rows, "integrity": integrity, "alerts_enabled": ALERTS_ENABLED}
    finally:
        db.close()


def _render_html(db_path: Path, build_revision: str) -> bytes:
    data = _dashboard_data(db_path)
    rows_html = "".join(
        f"<tr><td>{r['id']}</td><td>{r['manufacturer']}</td><td>{r['region']}</td>"
        f"<td>{'production' if r['production'] else 'experimental'}</td>"
        f"<td>{r['last_status']}</td><td>{r['last_finished_at'] or '—'}</td></tr>"
        for r in data["sources"]
    )
    options_html = "".join(f'<option value="{r["id"]}">{r["id"]}</option>' for r in data["sources"])
    html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{APP_NAME} — field test</title>
<style>
body {{ font-family: -apple-system, sans-serif; margin: 2rem; color: #1a1a1a; }}
table {{ border-collapse: collapse; margin-top: 1rem; }}
td, th {{ border: 1px solid #ccc; padding: 0.4rem 0.8rem; text-align: left; font-size: 0.9rem; }}
.banner {{ background: #eef; padding: 0.6rem 1rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.85rem; }}
.counts span {{ margin-right: 1.5rem; font-size: 0.9rem; }}
select, button {{ padding: 0.5rem 0.8rem; font-size: 1rem; }}
button {{ cursor: pointer; }}
#result {{ white-space: pre-wrap; font-family: monospace; font-size: 0.8rem; margin-top: 1rem; background: #f6f6f6; padding: 0.8rem; border-radius: 6px; }}
</style></head>
<body>
<h2>{APP_NAME} — field test</h2>
<div class="banner">Loopback-only field test build. Revision: {build_revision}. Alerts enabled: {data['alerts_enabled']}. DB integrity: {data['integrity']}.</div>
<div class="counts">
<span><b>{data['counts']['products']}</b> products</span>
<span><b>{data['counts']['observations']}</b> observations</span>
<span><b>{data['counts']['change_events']}</b> change events</span>
<span><b>{data['counts']['collector_runs']}</b> collector runs</span>
</div>
<table><tr><th>source</th><th>manufacturer</th><th>region</th><th>membership</th><th>last status</th><th>last finished</th></tr>
{rows_html}
</table>
<p>
<select id="source">{options_html}</select>
<button id="collect">Collect Now</button> (live network, single chosen source)
</p>
<div id="result"></div>
<script>
document.getElementById('collect').addEventListener('click', async () => {{
  const btn = document.getElementById('collect');
  const out = document.getElementById('result');
  const source = document.getElementById('source').value;
  btn.disabled = true; btn.textContent = 'Collecting…';
  out.textContent = '';
  try {{
    const resp = await fetch('/collect?source=' + encodeURIComponent(source), {{method: 'POST'}});
    const body = await resp.json();
    out.textContent = JSON.stringify(body, null, 2);
  }} catch (err) {{
    out.textContent = 'request failed: ' + err;
  }} finally {{
    setTimeout(() => location.reload(), 1200);
  }}
}});
</script>
</body></html>"""
    return html.encode("utf-8")


def create_server(db_path: Path, build_revision: str) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # noqa: A003 - stdlib signature
            pass

        def do_GET(self):
            if self.path == "/health":
                self._send_json(200, {"status": "ok", "app": APP_NAME})
                return
            if self.path in ("/", ""):
                body = _render_html(db_path, build_revision)
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_response(404)
            self.end_headers()

        def do_POST(self):
            if not self.path.startswith("/collect"):
                self.send_response(404)
                self.end_headers()
                return
            query = parse_qs(self.path.partition("?")[2])
            source_id = (query.get("source") or [""])[0]
            if source_id not in runtime_source_ids():
                self._send_json(400, {"error": "unknown_or_disabled_source", "source": source_id})
                return
            try:
                source = SOURCES[source_id]
                db = Database(str(db_path))
                try:
                    with SoakLock(lock_path_for_db(db_path), role="manual-collect"):
                        result = process(db, _collector_class(source)(source, fixture_mode=False), fixture_mode=False)
                finally:
                    db.close()
                self._send_json(200, {"source": source_id, "status": result.status, "raw": result.raw_count, "accepted": result.accepted_count, "new": result.new_count, "resighted": result.resighted_count, "error": result.error})
            except SoakLockError as exc:
                self._send_json(409, {"error": "locked", "detail": str(exc)})
            except Exception as exc:  # defensive: never crash the server on a bad cycle
                self._send_json(500, {"error": "collect_failed", "detail": str(exc), "trace": traceback.format_exc()})

        def _send_json(self, status: int, payload: dict):
            body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return ThreadingHTTPServer(("127.0.0.1", 0), Handler)
