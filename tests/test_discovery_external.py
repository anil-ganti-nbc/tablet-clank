"""Real unchanged external D1 contract controls (not private source qualification).

TABLET_D1_ROOT must point to the external directory containing d1.py.
TABLET_D1_FIXTURE=generic (default) uses clearly synthetic public RSS controls.
An absolute manifest path selects authentic private replay inputs instead.
Only unset external root skips; configured invalid inputs fail.
"""
from argparse import Namespace
from dataclasses import replace
import json
import os
from pathlib import Path
import sqlite3

import pytest

from tablet_clank import discovery as d
from tablet_clank.discovery_dashboard import evidence_bytes, render_discovery

PROFILE = Path(__file__).resolve().parents[1] / 'config/d1-tablets.v1.json'


@pytest.fixture
def external(tmp_path):
    root = os.environ.get('TABLET_D1_ROOT')
    if root is None:
        pytest.skip('TABLET_D1_ROOT absent: external pinned producer not supplied')
    root = Path(root)
    assert root.is_absolute() and (root / 'd1.py').is_file(), 'Invalid configured TABLET_D1_ROOT'
    state = tmp_path / 'producer-state'
    state.mkdir()
    cfg = d.Settings(d.PRODUCER_ID, root / 'd1.py', PROFILE, state, tmp_path / 'consumer', True)
    module, profiles = d.authenticate(cfg)
    selector = os.environ.get('TABLET_D1_FIXTURE', 'generic')
    if selector == 'generic':
        sources = []
        for source, title in zip(profiles['profiles'][0]['sources'],
                                 ('Rugged Android tablet launched in India', '全新 MatePad 平板发布')):
            raw = ('<rss version="2.0"><channel><title>Public generic control</title><item><title>' + title +
                   '</title><link>https://example.com/' + source['id'] +
                   '</link><pubDate>Thu, 29 Oct 2026 10:00:00 GMT</pubDate>'
                   '<description>Public test only: tablet launched with keyboard support; phone and laptop comparisons are incidental body words.</description>'
                   '</item></channel></rss>').encode()
            capture = tmp_path / (source['id'] + '.xml')
            capture.write_bytes(raw)
            sources.append(dict(source_id=source['id'], url=source['url'], capture_file=str(capture),
                                collected_at='2026-10-29T10:05:00+00:00', http_status=200))
        manifest = tmp_path / 'generic-manifest.json'
        manifest.write_text(json.dumps({'sources': sources}), encoding='utf8')
    else:
        manifest = Path(selector)
        assert manifest.is_absolute() and manifest.is_file(), 'Invalid configured TABLET_D1_FIXTURE'
    assert module.run(Namespace(config=str(PROFILE), state=str(state), replay=str(manifest))) == 0
    return cfg, module


def test_external_real_replay_intake_and_history(external, tmp_path, monkeypatch):
    cfg, module = external
    export = cfg.evidence_root / 'leads.jsonl'
    result = d.import_export(cfg, export)
    rows = d.read_inbox(cfg)
    assert result['inserted'] == len(rows) > 0
    assert all(row['payload']['category_profile'] == 'tablets' for row in rows)
    assert all(row['payload']['brand'] is None and row['payload']['model'] is None for row in rows)
    assert all(row['evidence_status'] == 'verified' for row in rows)
    original = rows[0]
    lead = original['lead_id']
    d.review(cfg, lead, 'editorial_keep')
    assert d.import_export(cfg, export)['unchanged'] == len(rows)
    # A changed producer observation appends; editorial label/history is independent.
    payloads = [json.loads(line) for line in export.read_text(encoding='utf8').splitlines()]
    next(p for p in payloads if p['lead_id'] == lead)['observed_at'] = '2026-10-29T11:05:00+00:00'
    export.write_text(''.join(json.dumps(p) + '\n' for p in payloads), encoding='utf8')
    assert d.import_export(cfg, export)['changed'] == 1
    retained = next(r for r in d.read_inbox(cfg) if r['lead_id'] == lead)
    assert retained['consumer_review'] == 'editorial_keep'
    assert len(retained['history']) == 2
    assert retained['review_history'][0]['label'] == 'editorial_keep'
    export.write_text('', encoding='utf8')
    d.import_export(cfg, export)
    assert len(d.read_inbox(cfg)) == len(rows), 'omissions retained'
    text = original['copied']['text']
    wanted = evidence_bytes(cfg, text)
    monkeypatch.chdir(tmp_path)
    assert evidence_bytes(replace(cfg), text) == wanted
    assert original['payload']['source_title'] in render_discovery(cfg)
    # All evidence is now consumer-owned; producer loss cannot break reads.
    for path in cfg.evidence_root.rglob('*'):
        if path.is_file() and path.suffix in ('.txt', '.xml'):
            path.unlink()
    assert evidence_bytes(replace(cfg, enabled=False), text) == wanted
    assert len(d.read_inbox(replace(cfg, enabled=False))) == len(rows)


def test_external_refusal_routing_and_quarantine(external):
    cfg, module = external
    export = cfg.evidence_root / 'leads.jsonl'
    payloads = [json.loads(line) for line in export.read_text(encoding='utf8').splitlines()]
    d.import_export(cfg, export)
    pointer = (cfg.data_dir / 'CURRENT').read_bytes()
    base = payloads[0]
    for key, value in (('schema_version', 'd1.lead.v999'), ('category_profile', 'unknown'),
                       ('suggested_consumer', 'computing-clank:proposal-review'),
                       ('publisher', 'Invented publisher')):
        changed = dict(base, **{key: value})
        if key == 'category_profile':
            changed['lead_id'] = module.lead_id(value, changed['source_url'])
        export.write_text(json.dumps(changed) + '\n', encoding='utf8')
        with pytest.raises(ValueError):
            d.import_export(cfg, export)
        assert (cfg.data_dir / 'CURRENT').read_bytes() == pointer
    for profile in ('computing', 'watches'):
        changed = dict(base, category_profile=profile, lead_id=module.lead_id(profile, base['source_url']))
        export.write_text(json.dumps(changed) + '\n', encoding='utf8')
        result = d.import_export(cfg, export)
        assert result['accepted'] == 0 and sum(result['excluded'].values()) == 1
    export.write_text(json.dumps(base) + '\n', encoding='utf8')
    Path(base['evidence']['capture_file']).unlink()
    assert d.import_export(cfg, export)['changed'] == 1
    row = next(r for r in d.read_inbox(cfg) if r['lead_id'] == base['lead_id'])
    assert row['evidence_status'] == 'unavailable/quarantined'
    assert row['limitations']
    bad = dict(base, evidence=dict(base['evidence'], text_file=str(cfg.evidence_root / '..' / 'outside')))
    export.write_text(json.dumps(bad) + '\n', encoding='utf8')
    with pytest.raises(ValueError):
        d.import_export(cfg, export)


def test_external_refresh_argv_and_failure_retains_current(external, monkeypatch):
    cfg, _ = external
    d.import_export(cfg, cfg.evidence_root / 'leads.jsonl')
    pointer = (cfg.data_dir / 'CURRENT').read_bytes()
    seen = []
    def failed(argv, **kwargs):
        seen.append((argv, kwargs))
        return Namespace(returncode=1, stdout='{"status":"PARTIAL"}')
    monkeypatch.setattr(d.subprocess, 'run', failed)
    with pytest.raises(ValueError, match='previous generation retained'):
        d.refresh(cfg)
    argv, kwargs = seen[0]
    assert argv[3:7] == [str(cfg.producer), 'run', '--config', str(cfg.profiles)]
    assert kwargs['shell'] is False
    assert '--state' in argv
    assert (cfg.data_dir / 'CURRENT').read_bytes() == pointer


def test_external_frozen_profile_generic_classification(external):
    cfg, module = external
    profile = module.load_config(PROFILE)[0][0]
    cases = [
        ('New iPad tablet announced', 'main'),
        ('Windows detachable tablet unveiled', 'main'),
        ('ChromeOS tablet launches in Europe', 'main'),
        ('Gaming Tab 9 launched in India', 'main'),
        ('新款 MatePad 平板上市', 'main'),
        ('iPad rumor could launch soon', 'research'),
        ('Ambiguous tablet form factor concept', 'research'),
        ('New smartphone launches with tablet support', 'excluded'),
        ('Tablet review: old model revisited', 'excluded'),
        ('iPad keyboard case launches', 'excluded'),
        ('iPad Pro keyboard launched', 'excluded'),
        ('Android tablet goes on sale in India', 'main'),
        ('Android tablet launched with laptop connectivity', 'main'),
        ('Rocket launch pad announced', 'excluded'),
    ]
    for title, wanted in cases:
        doc = dict(title=title, content='Generic research control; no event asserted.', url='https://example.com/control',
                   source_published_at_original='2026-10-29T10:00:00+00:00')
        assert module.classify(profile, doc)[0] == wanted, title


def test_external_process_restart_and_cli_history(external, tmp_path):
    """Separate interpreter invocations, changed cwd, never a live command."""
    import subprocess
    import sys
    from tablet_clank.discovery_cli import save
    cfg, _ = external
    path = tmp_path / 'settings.json'
    save(path, cfg)
    def invoke(*arguments):
        argv = [sys.executable, '-B', '-m', 'tablet_clank.cli', 'discovery',
                '--settings', str(path), *arguments]
        result = subprocess.run(argv, cwd=tmp_path, capture_output=True, text=True,
                                encoding='utf8', timeout=30, shell=False)
        print(d.dumps({'argv': argv, 'returncode': result.returncode}))
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)
    assert invoke('import', str(cfg.evidence_root / 'leads.jsonl'))['inserted'] > 0
    listing = invoke('list')
    lead = listing['proposals'][0]['lead_id']
    assert invoke('review', lead, '--label', 'editorial_keep')['consumer_review'] == 'editorial_keep'
    assert invoke('show', lead)['consumer_review'] == 'editorial_keep'
    assert invoke('disable')['enabled'] is False
    assert invoke('show', lead)['review_history'][0]['label'] == 'editorial_keep'
    assert not (tmp_path / 'var').exists()


def test_external_refresh_success_uses_real_offline_producer(external, monkeypatch):
    """The subprocess boundary is replaced only to force real D1 replay, not live I/O."""
    import contextlib
    import io
    cfg, module = external
    manifest = cfg.evidence_root / 'capture_manifest.json'
    seen = []
    def offline_run(argv, **kwargs):
        seen.append(argv)
        assert argv[3:7] == [str(cfg.producer), 'run', '--config', str(cfg.profiles)]
        state = Path(argv[argv.index('--state') + 1])
        assert state.is_relative_to(cfg.data_dir / 'refresh-staging')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = module.run(Namespace(config=str(cfg.profiles), state=str(state), replay=str(manifest)))
        return Namespace(returncode=code, stdout=output.getvalue())
    monkeypatch.setattr(d.subprocess, 'run', offline_run)
    result = d.refresh(cfg)
    assert result['inserted'] > 0 and seen
    assert all(r['evidence_status'] == 'verified' for r in d.read_inbox(cfg))
