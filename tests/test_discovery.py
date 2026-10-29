"""Public generic controls, not source qualification or private live evidence."""
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import threading
import urllib.error
import urllib.request

import pytest

from tablet_clank import discovery as d
from tablet_clank.discovery_cli import load, save
from tablet_clank.discovery_dashboard import create_server, render_discovery


def settings(tmp_path):
    return d.Settings('tablet-d1-v1', tmp_path / 'd1.py', tmp_path / 'profile.json',
                      tmp_path / 'input', tmp_path / 'consumer', False)


def test_settings_and_strict_json(tmp_path):
    cfg = settings(tmp_path)
    save(tmp_path / 'settings.json', cfg)
    assert load(tmp_path / 'settings.json') == cfg
    for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":1e999}'):
        with pytest.raises(ValueError):
            d.strict_json(raw)
    with pytest.raises(ValueError, match='absolute'):
        load('relative.json')
    with pytest.raises(ValueError):
        replace(cfg, enabled='yes')
    with pytest.raises(ValueError):
        replace(cfg, producer_id='other-consumer')


def test_pin_refusal_before_execution(tmp_path):
    cfg = settings(tmp_path)
    cfg.producer.write_text('raise AssertionError("executed")')
    cfg.profiles.write_text('{}')
    with pytest.raises(ValueError, match='pin mismatch'):
        d.authenticate(cfg)
    assert not cfg.data_dir.exists()


def test_atomic_disable_and_paths(tmp_path, monkeypatch):
    cfg = settings(tmp_path)
    cfg.evidence_root.mkdir()
    with pytest.raises(ValueError):
        d.checked_path(cfg.evidence_root, str(tmp_path / 'outside'))
    first, conn = d.new_generation(cfg)
    d.publish(cfg, first, conn)
    pointer = (cfg.data_dir / 'CURRENT').read_bytes()
    second, conn = d.new_generation(cfg)
    def interrupted(*args):
        raise OSError('interrupted')
    monkeypatch.setattr(d.os, 'replace', interrupted)
    with pytest.raises(OSError):
        d.publish(cfg, second, conn)
    assert (cfg.data_dir / 'CURRENT').read_bytes() == pointer
    assert d.read_inbox(cfg) == []
    with pytest.raises(ValueError, match='disabled'):
        d.import_export(cfg, 'never-read')
    with pytest.raises(ValueError, match='disabled'):
        d.review(cfg, 'lead', 'editorial_keep')


def test_empty_view_no_writes_and_http_authority(tmp_path):
    cfg = settings(tmp_path)
    assert '0 retained proposals' in render_discovery(cfg)
    assert not cfg.data_dir.exists()
    server = create_server(cfg, port=0)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        base = 'http://127.0.0.1:' + str(server.server_address[1])
        for route in ('/', '/discovery', '/health', '/api/discovery'):
            with urllib.request.urlopen(base + route) as response:
                assert response.status == 200
        for route, method, code in (('/collect', 'POST', 405), ('/collect/all', 'POST', 405),
                                    ('/collect', 'GET', 404), ('/discovery/review', 'GET', 404)):
            with pytest.raises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(urllib.request.Request(base + route, method=method))
            assert error.value.code == code
        assert not cfg.data_dir.exists()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_cli_routed_before_catalogue(tmp_path, monkeypatch, capsys):
    from tablet_clank import cli
    def forbidden(*args, **kwargs):
        raise AssertionError('catalogue opened')
    monkeypatch.setattr(cli, 'Database', forbidden)
    cfg = settings(tmp_path)
    path = tmp_path / 'settings.json'
    save(path, cfg)
    assert cli.main(['discovery', '--settings', str(path), 'list']) == 0
    assert json.loads(capsys.readouterr().out)['total'] == 0
    assert cli.main(['discovery', '--settings', str(path), 'disable']) == 0
    assert not load(path).enabled
    assert not cfg.data_dir.exists()


def test_launcher_routes_discovery_without_legacy(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location('tablet_windows_launcher',
        Path(__file__).resolve().parents[1] / 'native/windows/launcher.py')
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    seen = []
    monkeypatch.setattr(launcher, 'launch_discovery', lambda args: seen.append(args) or 0)
    monkeypatch.setattr(launcher, 'configure_environment', lambda *_: pytest.fail('legacy environment'))
    assert launcher.main(['--discovery-only', '--settings', str(tmp_path / 'settings.json')]) == 0
    assert seen[0].port == 8789


def test_profile_contract_and_title_only_negatives():
    import re
    profile = json.loads((Path(__file__).resolve().parents[1] / 'config/d1-tablets.v1.json').read_text(encoding='utf8'))
    assert profile['schema_version'] == 'd1.profiles.v1'
    p, = profile['profiles']
    assert p['id'] == 'tablets'
    assert p['destination'] == 'tablet-clank:proposal-review'
    assert {s['id'] for s in p['sources']} == {'gizmochina', 'ithome'}
    assert d.digest((Path(__file__).resolve().parents[1] / 'config/d1-tablets.v1.json').read_bytes()) == d.PROFILES_SHA
    negatives = lambda title: any(re.search(pattern, title, re.I) for pattern in p['negative'])
    for title in ('New smartphone launches with tablet connectivity', 'iPad keyboard case launches',
                  'Tablet sale: save $100', 'Laptop convertible announced', 'New e-reader launches',
                  'Watch launched alongside tablet', 'iPad review', '新款手机发布，支持平板互联'):
        assert negatives(title), title
    for title in ('Rugged Android tablet launched', 'New detachable Windows tablet unveiled',
                  'MatePad Pro 平板发布', 'Gaming Tab launches in India', 'iPad announced with keyboard support'):
        assert not negatives(title), title


def test_public_store_controls_with_explicit_prepared_rows(tmp_path, monkeypatch):
    """Synthetic prepared rows test storage/view only, never producer authenticity."""
    from tablet_clank.discovery_dashboard import evidence_bytes
    cfg = replace(settings(tmp_path), enabled=True)
    raw = b'<script>not executable evidence</script>'
    name = d.digest(raw)
    payload = dict(source_title='<script>headline</script>', source_url='https://example.com/tablet',
                   supporting_passage=raw.decode(), publisher='Public test publisher', source_descriptor='Synthetic control',
                   source_published_at=None, source_published_at_original=None,
                   observed_at='2026-10-29T10:00:00+00:00', collected_at='2026-10-29T10:00:00+00:00',
                   first_observed_at='2026-10-29T10:00:00+00:00', review_state='unreviewed',
                   decision='research', event_hint='unresolved', uncertainties=['Synthetic control only'])
    prepared = [(dict(payload, lead_id='generic-' + str(n)), {'text': (name, raw)}, []) for n in range(125)]
    monkeypatch.setattr(d, 'prepare', lambda *_: (prepared, dict(parsed=len(prepared), accepted=len(prepared), excluded={})))
    assert d.import_export(cfg, 'synthetic-prepared-only')['inserted'] == 125
    assert d.import_export(cfg, 'synthetic-prepared-only')['unchanged'] == 125
    d.review(cfg, 'generic-0', 'editorial_research')
    prepared[0][0]['supporting_passage'] = 'Changed prepared observation'
    assert d.import_export(cfg, 'synthetic-prepared-only')['changed'] == 1
    row = next(r for r in d.read_inbox(cfg) if r['lead_id'] == 'generic-0')
    assert row['consumer_review'] == 'editorial_research'
    assert len(row['history']) == 2
    assert len(row['review_history']) == 1
    page = render_discovery(cfg)
    assert '125 retained proposals' in page and 'generic-124' in page
    assert '<script>headline</script>' not in page
    assert '&lt;script&gt;headline&lt;/script&gt;' in page
    assert evidence_bytes(cfg, name) == raw
    server = create_server(cfg, port=0)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        url = 'http://127.0.0.1:' + str(server.server_address[1])
        with urllib.request.urlopen(url + '/discovery/evidence/' + name) as response:
            assert response.headers['Content-Type'] == 'text/plain; charset=utf-8'
            assert response.headers['X-Content-Type-Options'] == 'nosniff'
            assert 'sandbox' in response.headers['Content-Security-Policy']
            assert response.read() == raw
        with urllib.request.urlopen(url + '/api/discovery') as response:
            assert len(json.load(response)) == 125
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    pointer = (cfg.data_dir / 'CURRENT').read_bytes()
    monkeypatch.setattr(d.os, 'replace', lambda *_: (_ for _ in ()).throw(OSError('interrupted publication')))
    prepared[0][0]['observed_at'] = '2026-10-29T11:00:00+00:00'
    with pytest.raises(OSError):
        d.import_export(cfg, 'synthetic-prepared-only')
    assert (cfg.data_dir / 'CURRENT').read_bytes() == pointer
    assert len(d.read_inbox(cfg)) == 125
    assert evidence_bytes(cfg, name) == raw


def test_launcher_real_readiness_marker_and_cleanup(tmp_path, monkeypatch):
    from argparse import Namespace
    from tablet_clank.storage import db
    spec = importlib.util.spec_from_file_location('discovery_real_launcher',
        Path(__file__).resolve().parents[1] / 'native/windows/launcher.py')
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    cfg = settings(tmp_path)
    path = tmp_path / 'settings.json'
    save(path, cfg)
    monkeypatch.setenv('TABLET_CLANK_NO_BROWSER', '1')
    monkeypatch.setattr(db, 'Database', lambda *_: pytest.fail('catalogue opened'))
    def stop_after_ready(sig, callback):
        marker = cfg.data_dir / 'runtime/discovery-dashboard.json'
        assert json.loads(marker.read_text())['mode'] == 'discovery-only'
        callback()
    monkeypatch.setattr(launcher.signal, 'signal', stop_after_ready)
    assert launcher.launch_discovery(Namespace(settings=str(path), port=0)) == 0
    assert not (cfg.data_dir / 'CURRENT').exists()
    assert not (cfg.data_dir / 'runtime/discovery-dashboard.json').exists()
