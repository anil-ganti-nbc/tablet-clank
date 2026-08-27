"""Field-test dashboard HTTP server for the Tablet Clank Finder launcher.

Deliberately outside the `tablet_clank` package: the core library stays
dependency-free per its own HANDOFF.md invariant. This is a thin,
stdlib-only http.server layer bolted on for the packaged macOS client only.

"Collect Now" mirrors the CLI's already-proven `collect <source> --live`
path exactly: same collector-class selection, same SoakLock manual-collect
lock domain, same pipeline.process() call, live network. No production
cycle, no scheduler, no alerts - ALERTS_ENABLED is never touched here.
"""

from __future__ import annotations

import json
import re
import sys
import time
import traceback
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import dash_data  # noqa: E402
import dash_render  # noqa: E402
from tablet_clank.collectors.apple_store import AppleStoreIPadProCollector  # noqa: E402
from tablet_clank.collectors.honor_cn import HonorCNTabletsCollector  # noqa: E402
from tablet_clank.collectors.html_catalogue import HtmlCatalogueCollector  # noqa: E402
from tablet_clank.collectors.tcl_global import TCLGlobalTabletsCollector  # noqa: E402
from tablet_clank.collectors.xml_sitemap import XmlSitemapCollector  # noqa: E402
from tablet_clank.pipeline import process  # noqa: E402
from tablet_clank.production import run_production  # noqa: E402
from tablet_clank.soak import SoakLock, SoakLockError, lock_path_for_db  # noqa: E402
from tablet_clank.sources.registry import SOURCES, runtime_source_ids  # noqa: E402
from tablet_clank.storage.db import Database  # noqa: E402
from tablet_clank.storage.qc_archive import QC_DECISIONS, AlreadyDecided, qc_path_for_db  # noqa: E402

APP_NAME = "Tablet Clank"

PRODUCT_DETAIL_RE = re.compile(r"^/products/(\d+)$")
QUEUE_ITEM_RE = re.compile(r"^/queue/(\d+)$")


def _collector_class(source):
    if source.manufacturer == "Honor":
        return HonorCNTabletsCollector
    if source.manufacturer == "TCL":
        return TCLGlobalTabletsCollector
    if "Apple Store" in source.kind:
        return AppleStoreIPadProCollector
    return XmlSitemapCollector if "XML" in source.kind else HtmlCatalogueCollector


def create_server(db_path: Path, build_revision: str) -> ThreadingHTTPServer:
    qc_path = qc_path_for_db(db_path)

    def topbar():
        db = Database(str(db_path))
        try:
            integrity = db.integrity()
        finally:
            db.close()
        return {"build_revision": build_revision, "integrity": integrity, "alerts_enabled": False}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # noqa: A003 - stdlib signature
            pass

        # ---------------------------------------------------------- GET

        def do_GET(self):
            path, _, query = self.path.partition("?")
            params = parse_qs(query)

            try:
                if path == "/health":
                    self._send_json(200, {"status": "ok", "app": APP_NAME})
                    return
                if path in ("/", "/overview"):
                    self._page("overview", "Overview", dash_render.render_overview(dash_data.overview(db_path)))
                    return
                if path == "/queue":
                    self._page("queue", "Active Queue", dash_render.render_queue(dash_data.active_queue(db_path, qc_path)))
                    return
                queue_match = QUEUE_ITEM_RE.match(path)
                if queue_match:
                    item = dash_data.queue_item(db_path, qc_path, int(queue_match.group(1)))
                    if item is None:
                        self.send_response(404)
                        self.end_headers()
                        return
                    self._page("queue", f"Event #{queue_match.group(1)}", dash_render.render_queue_item(item))
                    return
                if path == "/qc/recent":
                    self._page("qc-recent", "Recently QCed", dash_render.render_qc_recent(dash_data.qc_recent(qc_path)))
                    return
                if path == "/discoveries":
                    self._page("discoveries", "Latest Discoveries", dash_render.render_discoveries(dash_data.latest_discoveries(db_path)))
                    return
                if path == "/products":
                    data = dash_data.products(
                        db_path,
                        manufacturer=_first(params, "manufacturer"),
                        source_id=_first(params, "source"),
                        region=_first(params, "region"),
                        membership=_first(params, "membership"),
                    )
                    self._page("products", "Products", dash_render.render_products(data))
                    return
                match = PRODUCT_DETAIL_RE.match(path)
                if match:
                    detail = dash_data.product_detail(db_path, int(match.group(1)))
                    if detail is None:
                        self.send_response(404)
                        self.end_headers()
                        return
                    self._page("products", detail["product"]["name"], dash_render.render_product_detail(detail))
                    return
                if path == "/changes":
                    data = dash_data.changes(db_path, event_type=_first(params, "event_type"))
                    self._page("changes", "Changes", dash_render.render_changes(data))
                    return
                if path == "/sources":
                    scope = _first(params, "scope")
                    active = {"production": "sources-production", "experimental": "sources-experimental"}.get(scope, "sources-all")
                    self._page(active, "Sources", dash_render.render_sources(dash_data.sources_list(db_path, scope), scope))
                    return
                if path == "/sources/health":
                    self._page("source-health", "Source Health", dash_render.render_source_health(dash_data.source_health(db_path)))
                    return
                if path == "/collect":
                    rows = dash_data.source_health(db_path)
                    empty = dash_data.counts(db_path)["products"] == 0
                    self._page("collect", "Collect", dash_render.render_collect(rows, empty))
                    return
                if path == "/runs":
                    self._page("runs", "Run History", dash_render.render_runs(dash_data.run_history(db_path)))
                    return
                if path == "/about":
                    self._page("about", "About", dash_render.render_about(dash_data.about(db_path, build_revision)))
                    return
                self.send_response(404)
                self.end_headers()
            except Exception:
                self._send_json(500, {"error": "render_failed", "trace": traceback.format_exc()})

        # --------------------------------------------------------- POST

        def do_POST(self):
            path, _, query_str = self.path.partition("?")
            query = parse_qs(query_str)

            if path == "/qc":
                self._handle_qc(query)
                return
            if path == "/collect/all":
                self._handle_collect_all()
                return
            if path != "/collect":
                self.send_response(404)
                self.end_headers()
                return
            source_id = (query.get("source") or [""])[0]
            if source_id not in runtime_source_ids():
                self._send_json(400, {"error": "unknown_or_disabled_source", "source": source_id})
                return
            started_at = datetime.now(timezone.utc).isoformat()
            started_monotonic = time.monotonic()
            try:
                source = SOURCES[source_id]
                db = Database(str(db_path))
                try:
                    with SoakLock(lock_path_for_db(db_path), role="manual-collect"):
                        result = process(db, _collector_class(source)(source, fixture_mode=False), fixture_mode=False)
                finally:
                    db.close()
                self._send_json(
                    200,
                    {
                        "source": source_id,
                        "status": result.status,
                        "raw": result.raw_count,
                        "accepted": result.accepted_count,
                        "new": result.new_count,
                        "resighted": result.resighted_count,
                        "error": result.error,
                        "started_at": started_at,
                        "duration_seconds": round(time.monotonic() - started_monotonic, 2),
                    },
                )
            except SoakLockError as exc:
                self._send_json(409, {"error": "locked", "detail": str(exc)})
            except Exception as exc:  # defensive: never crash the server on a bad cycle
                self._send_json(500, {"error": "collect_failed", "detail": str(exc), "trace": traceback.format_exc()})

        # ------------------------------------------------------- QC / run-all

        def _handle_qc(self, query: dict):
            event_id_raw = (query.get("event_id") or [""])[0]
            decision = (query.get("decision") or [""])[0]
            if not event_id_raw.isdigit():
                self._send_json(400, {"error": "invalid_event_id"})
                return
            if decision not in QC_DECISIONS:
                self._send_json(400, {"error": "unknown_decision", "decision": decision})
                return
            try:
                snapshot = dash_data.submit_qc(db_path, qc_path, int(event_id_raw), decision)
            except AlreadyDecided as exc:
                self._send_json(409, {"error": "already_decided", "detail": str(exc)})
                return
            except Exception as exc:
                self._send_json(500, {"error": "qc_failed", "detail": str(exc)})
                return
            if snapshot is None:
                self.send_response(404)
                self.end_headers()
                return
            self._send_json(200, {"event_id": int(event_id_raw), "decision": decision})

        def _handle_collect_all(self):
            try:
                report = run_production(str(db_path))
                self._send_json(200, report)
            except SoakLockError as exc:
                self._send_json(409, {"error": "locked", "detail": str(exc)})
            except Exception as exc:  # defensive: never crash the server on a bad cycle
                self._send_json(500, {"error": "run_all_failed", "detail": str(exc), "trace": traceback.format_exc()})

        # ------------------------------------------------------- helpers

        def _page(self, active: str, title: str, content: str):
            body = dash_render.layout(active, title, content, topbar())
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, status: int, payload: dict):
            body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return ThreadingHTTPServer(("127.0.0.1", 0), Handler)


def _first(params: dict, key: str):
    values = params.get(key)
    return values[0] if values and values[0] else None
