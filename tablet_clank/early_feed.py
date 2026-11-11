"""Offline QC preview for retained Japanese feed metadata; never fetches or imports.

This is NOT a D1 producer or a source admission. The accepted D1 profile pins only
Gizmochina and IT Home; Japanese sources must not be impersonated as either one.
"""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha256
from urllib.parse import parse_qs, urlparse

FEED = 'https://phablet.jp/?feed=rss2'
TABLET_WORDS = ('タブレット', '平板', 'tablet', 'ipad', 'matepad', 'iplay', 'pad x10')
NOISE_WORDS = ('セール', '割引', 'クーポン', '期間限定', 'sale', 'discount', 'coupon', 'ベンチマーク', 'ランキング', 'review', 'レビュー')
ANNOUNCEMENT_WORDS = ('発表', 'announced', 'unveiled')
AVAILABILITY_WORDS = ('発売', '予約', 'on sale', 'preorder')


def _clock(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError('Publication clock must be a string or null')
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError) as exc:
        raise ValueError('Invalid publication clock') from exc
    if parsed.tzinfo is None:
        raise ValueError('Publication clock lacks timezone')
    return parsed.astimezone(timezone.utc).isoformat()


def preview_retained(metadata):
    """Return read-only review rows, not valid d1.lead.v2 export records."""
    if metadata.get('provenance', {}).get('feed_url') != FEED or not isinstance(metadata.get('items'), list):
        raise ValueError('Expected exact retained research feed metadata')
    rows, seen = [], set()
    for item in metadata['items']:
        if not isinstance(item, dict):
            raise ValueError('Feed item must be an object')
        title, link, guid = (item.get(key) for key in ('title', 'link', 'guid'))
        if not all(isinstance(value, str) and value for value in (title, link, guid)):
            raise ValueError('Missing article title/link/GUID')
        parts = urlparse(link)
        if (parts.scheme != 'https' or parts.netloc != 'phablet.jp' or parts.path != '/'
                or parts.fragment or not parts.query.startswith('p=')
                or parse_qs(parts.query) != {'p': [parts.query[2:]]}
                or not parts.query[2:].isdigit()):
            raise ValueError('Unexpected article origin')
        if guid != link:
            raise ValueError('Unverified GUID/link relationship')
        if guid in seen:
            continue  # One article, one preview; never a second launch claim.
        seen.add(guid)
        categories = item.get('categories')
        if not isinstance(categories, list) or not all(isinstance(x, str) for x in categories):
            raise ValueError('Invalid feed categories')
        published_original = item.get('pubDate')
        published_utc = _clock(published_original)
        lowered = title.casefold()
        tablet = any(word in lowered for word in TABLET_WORDS) or 'タブレット' in categories or '中華タブレット' in categories
        noise = any(word in lowered for word in NOISE_WORDS) or 'セール情報' in categories
        decision = 'research' if tablet and not noise else 'excluded'
        event_hint = ('announcement' if any(x in lowered for x in ANNOUNCEMENT_WORDS) else
                      'availability' if any(x in lowered for x in AVAILABILITY_WORDS) else 'unresolved')
        rows.append({
            'article_id': sha256(guid.encode('utf8')).hexdigest(),
            'source_url': link, 'source_guid': guid, 'source_title': title,
            'source_published_at_original': published_original,
            'source_published_at': published_utc,
            'source_clock_is_launch_clock': False,
            'publisher': 'phablet.jp', 'provenance_role': 'secondary_editorial',
            'feed_url': FEED, 'categories': categories,
            'decision': decision, 'event_hint': event_hint if decision == 'research' else 'unresolved',
            'brand': None, 'model': None, 'region': None, 'availability_at': None,
            'observation_at': None, 'global_novelty': 'UNKNOWN',
            'uncertainties': ['Unverified manufacturer/model and Japan/global lifecycle',
                              'Feed date is article publication, not OEM announcement or availability',
                              'Recurring source policy and D1 source/profile pins HOLD'],
        })
    return rows
