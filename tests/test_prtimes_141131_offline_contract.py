"""Metadata contract only: no source capture, editorial gold, or native replay."""
from dataclasses import replace
import os
from pathlib import Path

import pytest

from tablet_clank import discovery as d
from tablet_clank import prtimes_141131
from tablet_clank.discovery_cli import load, save

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / 'config/d1-prtimes-141131.offline.v1.json'
CURRENT = ROOT / 'config/d1-tablets.v1.json'


@pytest.fixture
def producer():
    external = os.environ.get('TABLET_D1_ROOT')
    if not external:
        pytest.skip('Pinned external D1 source unavailable; contract test NOT_RUN')
    path = Path(external) / 'd1.py'
    assert path.is_absolute() and d.digest(path.read_bytes()) == d.CODE_SHA
    return path


def test_issuer_profile_contract_is_separate_and_disabled(tmp_path, producer):
    cfg = d.prtimes_141131_offline_settings(producer, PROFILE,
                                            tmp_path / 'evidence', tmp_path / 'sidecar')
    assert not cfg.enabled and cfg.producer_id != d.PRODUCER_ID
    assert d.digest(PROFILE.read_bytes()) == d.PRTIMES_141131_PROFILES_SHA
    module, raw = d.authenticate(cfg)
    sources = module.load_config(PROFILE)
    assert len(sources) == 1
    assert sources[0][1]['id'] == 'prtimes_141131'
    assert sources[0][1]['url'] == 'https://prtimes.jp/companyrdf.php?company_id=141131'
    assert len(raw['profiles']) == 1 and len(raw['profiles'][0]['sources']) == 1
    assert not cfg.evidence_root.exists() and not cfg.data_dir.exists()
    with pytest.raises(ValueError, match='offline-only'):
        d.refresh(replace(cfg, enabled=True))
    with pytest.raises(ValueError, match='cannot be configured by CLI'):
        save(tmp_path / 'experimental-settings.json', cfg)
    assert not (tmp_path / 'experimental-settings.json').exists()
    with pytest.raises(ValueError, match='pin mismatch'):
        d.authenticate(replace(cfg, profiles=CURRENT))
    assert not cfg.evidence_root.exists() and not cfg.data_dir.exists()


def test_existing_pinned_two_source_cli_shape_unchanged(tmp_path, producer):
    cfg = d.Settings(d.PRODUCER_ID, producer, CURRENT,
                     tmp_path / 'accepted-evidence', tmp_path / 'accepted-sidecar')
    module, raw = d.authenticate(cfg)
    assert len(module.load_config(CURRENT)) == 2
    assert [s['id'] for s in raw['profiles'][0]['sources']] == ['gizmochina', 'ithome']
    assert d.digest(CURRENT.read_bytes()) == d.PROFILES_SHA
    with pytest.raises(ValueError, match='pin mismatch'):
        d.authenticate(replace(cfg, profiles=PROFILE))
    settings = tmp_path / 'accepted-settings.json'
    save(settings, cfg)
    assert load(settings) == cfg
    assert 'prtimes_141131_profile_sha' not in settings.read_text(encoding='utf8')


def test_no_deleted_capture_substitution_and_unsafe_xml_refused():
    with pytest.raises(ValueError, match='Invalid bounded'):
        prtimes_141131.inspect_capture(b'')
    with pytest.raises(ValueError, match='DTD/entity'):
        prtimes_141131.inspect_capture(b'<!DOCTYPE rss><rss/>')
    with pytest.raises(ValueError, match='Expected one RSS1'):
        prtimes_141131.inspect_capture(b'<rss/>')
