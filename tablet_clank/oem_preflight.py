"""Manual, bounded OEM catalogue preflight; never run by collectors or schedules.

Only the three fixed public URLs in the source registry are supported. No
redirects, cookies, credentials, retries, raw response storage, or DB writes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

from .collectors.oem_catalogues import OEMTabletCatalogueCollector
from .sources.registry import SOURCES

SOURCE_IDS = ("alldocube_global_tablets", "teclast_global_tablets", "blackview_zeno_tablets")
USER_AGENT = "TabletClank/0.1 (+research; contact unavailable)"
MAX_BYTES = 2_000_000
TIMEOUT = 15


class Stop(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_once(opener, url, requests):
    """Count attempts, including failed and redirected requests; never follow."""
    entry = {"url": url, "status": None}
    requests.append(entry)
    try:
        response = opener.open(urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT, "Accept": "text/html,text/plain,application/xhtml+xml"
        }), timeout=TIMEOUT)
    except urllib.error.HTTPError as error:
        entry["status"] = error.code
        # This is not an instruction to retry automatically.
        retry = error.headers.get("Retry-After")
        if retry and len(retry) <= 80 and "\n" not in retry and "\r" not in retry:
            entry["retry_after"] = retry
        error.close()
        raise Stop("HTTP status; stopped without retry or redirect") from None
    except (OSError, ValueError):
        raise Stop("network error or timeout") from None
    with response:
        entry["status"] = response.status
        if response.status != 200:
            raise Stop("non-200 response")
        content_type = response.headers.get_content_type()
        entry["content_type"] = content_type
        try:
            body = response.read(MAX_BYTES + 1)
        except OSError:
            raise Stop("network error or timeout while reading") from None
        if len(body) > MAX_BYTES:
            raise Stop("response exceeds size limit")
        entry["bytes"] = len(body)
        entry["sha256"] = hashlib.sha256(body).hexdigest()
        return body, content_type


def preflight(source_id, opener):
    source = SOURCES[source_id]
    parts = urlsplit(source.url)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("source URL is not a fixed clean HTTPS URL")
    robots_url = urlunsplit(("https", parts.netloc, "/robots.txt", "", ""))
    result = {"source_id": source_id, "started_utc": datetime.now(timezone.utc).isoformat(),
              "requests": [], "result": "stopped"}
    try:
        robots, kind = request_once(opener, robots_url, result["requests"])
        if kind != "text/plain":
            raise Stop("unexpected robots content type")
        try:
            lines = robots.decode("utf-8", errors="strict").splitlines()
        except UnicodeDecodeError:
            raise Stop("robots is not valid UTF-8") from None
        # Require an actual policy, not an empty or error document.
        if not any(line.strip().lower().startswith("user-agent:") for line in lines):
            raise Stop("robots lacks a user-agent policy")
        policy = urllib.robotparser.RobotFileParser()
        policy.parse(lines)
        if not policy.can_fetch(USER_AGENT, source.url):
            raise Stop("robots disallows catalogue")
        body, kind = request_once(opener, source.url, result["requests"])
        if kind not in ("text/html", "application/xhtml+xml"):
            raise Stop("unexpected catalogue content type")
        try:
            document = body.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise Stop("catalogue is not valid UTF-8") from None
        try:
            candidates = OEMTabletCatalogueCollector(source).parse_live(document)
        except RuntimeError:
            raise Stop("catalogue completeness guard failed") from None
        result["candidate_count"] = len(candidates)
        result["identifiers"] = sorted(c.source_identifier for c in candidates)
        result["result"] = "parsed"
    except Stop as error:
        result["reason"] = str(error)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_id", choices=SOURCE_IDS)
    parser.add_argument("--terms-reviewed", action="store_true",
                        help="attest that current site terms and robots were reviewed for this run")
    parser.add_argument("--output", required=True, help="new private JSON report path (never overwritten)")
    args = parser.parse_args(argv)
    if not args.terms_reviewed:
        parser.error("review current terms and robots first; pass --terms-reviewed")
    # Reserve before any network request. Never follow an output symlink or
    # overwrite an existing file; chmod is independent of the process umask.
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        result = preflight(args.source_id, urllib.request.build_opener(NoRedirect()))
        json.dump(result, output, indent=2, sort_keys=True)
        output.write("\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] == "parsed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
