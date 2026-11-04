"""Hermetic tests for the manually invoked OEM preflight."""
from email.message import Message
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from tablet_clank import oem_preflight as probe
from tablet_clank.sources.registry import SOURCES

SOURCE = "alldocube_global_tablets"


class Response(BytesIO):
    def __init__(self, body, content_type):
        super().__init__(body)
        self.status = 200
        self.headers = Message()
        self.headers["Content-Type"] = content_type


class Opener:
    def __init__(self, replies):
        self.replies = iter(replies)
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request.full_url, timeout))
        reply = next(self.replies)
        if isinstance(reply, Exception):
            raise reply
        return reply


def robots(text=b"User-agent: *\nAllow: /\n"):
    return Response(text, "text/plain")


def catalogue():
    return Response(Path(SOURCES[SOURCE].fixture).read_bytes(), "text/html")


def test_success_has_two_requests_digest_and_guarded_identifiers():
    opener = Opener([robots(), catalogue()])
    result = probe.preflight(SOURCE, opener)
    assert result["result"] == "parsed"
    assert len(result["requests"]) == len(opener.calls) == 2
    assert result["candidate_count"] == 5
    assert "iplay80miniturbo" in result["identifiers"]
    assert len(result["requests"][1]["sha256"]) == 64
    assert all(call[1] == probe.TIMEOUT for call in opener.calls)


def test_disallowed_robots_stops_before_catalogue():
    opener = Opener([robots(b"User-agent: *\nDisallow: /\n")])
    result = probe.preflight(SOURCE, opener)
    assert result["result"] == "stopped"
    assert len(opener.calls) == len(result["requests"]) == 1
    assert "disallows" in result["reason"]


@pytest.mark.parametrize("status", [301, 403, 429])
def test_status_stops_without_follow_or_retry(status):
    headers = Message()
    headers["Retry-After"] = "120"
    error = HTTPError("https://www.alldocube.com/robots.txt", status, "no", headers, None)
    opener = Opener([error])
    result = probe.preflight(SOURCE, opener)
    assert result["result"] == "stopped"
    assert result["requests"][0]["status"] == status
    assert len(opener.calls) == 1


def test_timeout_and_completeness_fail_closed():
    opener = Opener([URLError("timeout")])
    assert probe.preflight(SOURCE, opener)["result"] == "stopped"
    opener = Opener([robots(), Response(b"<html>Access denied</html>", "text/html")])
    result = probe.preflight(SOURCE, opener)
    assert result["result"] == "stopped"
    assert "completeness" in result["reason"]


def test_oversize_and_invalid_robots_stop():
    opener = Opener([Response(b"x" * (probe.MAX_BYTES + 1), "text/plain")])
    assert probe.preflight(SOURCE, opener)["result"] == "stopped"
    opener = Opener([robots(b'<html>blocked</html>')])
    assert probe.preflight(SOURCE, opener)['result'] == 'stopped'
    assert len(opener.calls) == 1


def test_read_timeout_is_reported_without_retry():
    class ReadTimeout(Response):
        def read(self, size=-1):
            raise TimeoutError("timeout")
    opener = Opener([robots(), ReadTimeout(b"", "text/html")])
    result = probe.preflight(SOURCE, opener)
    assert result["result"] == "stopped"
    assert "timeout" in result["reason"]
    assert len(opener.calls) == len(result["requests"]) == 2


def test_cli_requires_terms_before_network_or_output(tmp_path, monkeypatch):
    monkeypatch.setattr(probe.urllib.request, "build_opener",
                        lambda *args: pytest.fail("must not construct opener"))
    output = tmp_path / "report.json"
    with pytest.raises(SystemExit):
        probe.main([SOURCE, "--output", str(output)])
    assert not output.exists()


def test_cli_refuses_existing_output_before_network(tmp_path, monkeypatch):
    output = tmp_path / "report.json"
    output.write_text("keep", encoding="utf-8")
    monkeypatch.setattr(probe.urllib.request, "build_opener",
                        lambda *args: pytest.fail("must not construct opener"))
    with pytest.raises(FileExistsError):
        probe.main([SOURCE, "--terms-reviewed", "--output", str(output)])
    assert output.read_text(encoding="utf-8") == "keep"


def test_redirect_handler_never_follows():
    handler = probe.NoRedirect()
    assert handler.redirect_request(None, None, 302, "", {}, "https://example.invalid") is None
