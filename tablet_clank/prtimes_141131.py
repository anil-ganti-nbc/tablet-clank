"""Fail-closed, offline-only issuer check before any future 141131 D1 replay.

This does not retain or reconstruct the deleted November feed, authorize a GET,
or establish legal/OEM identity. D1's RSS1 parser does not carry dc:corp into
LeadProposal, so verify that source field on the original authorized bytes
before giving a future capture to the pinned producer.
"""
from datetime import datetime
import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
RSS1 = 'http://purl.org/rss/1.0/'
DC = 'http://purl.org/dc/elements/1.1/'
MAX_CAPTURE = 524288


def inspect_capture(raw):
    """Return only a count; refuse mixed issuers/unknown dates/unsafe XML."""
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_CAPTURE:
        raise ValueError('Invalid bounded PR TIMES capture')
    if re.search(br'<!\s*(?:DOCTYPE|ENTITY)\b', raw, re.I):
        raise ValueError('DTD/entity declarations prohibited')
    root = ET.fromstring(raw)
    if root.tag != '{' + RDF + '}RDF' or len(root.findall('{' + RSS1 + '}channel')) != 1:
        raise ValueError('Expected one RSS1 RDF channel')
    items = root.findall('{' + RSS1 + '}item')
    if not 1 <= len(items) <= 250:
        raise ValueError('Expected bounded RSS1 items')
    for item in items:
        corp = (item.findtext('{' + DC + '}corp') or '').strip()
        link = (item.findtext('{' + RSS1 + '}link') or '').strip()
        original_date = (item.findtext('{' + DC + '}date') or '').strip()
        if not re.search(r'(?i)alldocube|アルドキューブ|酷比魔方', corp):
            raise ValueError('Issuer field does not assert Alldocube')
        parts = urlsplit(link)
        if (parts.scheme != 'https' or parts.hostname != 'prtimes.jp' or
                parts.username is not None or parts.password is not None or
                parts.port is not None or parts.query or parts.fragment or
                not re.fullmatch(r'/main/html/rd/p/[0-9]+\.000141131\.html', parts.path)):
            raise ValueError('Article link outside exact 141131 issuer path')
        try:
            date = datetime.fromisoformat(original_date.replace('Z', '+00:00'))
        except ValueError as exc:
            raise ValueError('Unparseable issuer article date') from exc
        if date.tzinfo is None or date.utcoffset() is None:
            raise ValueError('Issuer article date must include timezone')
    return len(items)
