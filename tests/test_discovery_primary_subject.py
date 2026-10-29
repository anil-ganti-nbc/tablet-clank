"""Generic primary-subject regressions; no publisher captures or model rosters.

Use the actual unchanged external D1 classifier. These are development controls,
not additional frozen qualification labels or a blind benchmark.
"""
from pathlib import Path
import os

import pytest

from tablet_clank import discovery as d


@pytest.fixture
def classifier(tmp_path):
    supplied = os.environ.get('TABLET_D1_ROOT')
    if supplied is None:
        pytest.skip('TABLET_D1_ROOT absent: external pinned producer not supplied')
    root = Path(supplied)
    assert root.is_absolute() and (root / 'd1.py').is_file(), 'Invalid configured TABLET_D1_ROOT'
    config = Path(__file__).resolve().parents[1] / 'config/d1-tablets.v1.json'
    cfg = d.Settings(d.PRODUCER_ID, root / 'd1.py', config, tmp_path / 'evidence', tmp_path / 'consumer')
    module, profiles = d.authenticate(cfg)
    profile, = profiles['profiles']
    return lambda title, body: module.classify(profile, {
        'title': title, 'content': body, 'url': 'https://example.com/generic-device',
        'source_published_at_original': '2026-10-29T10:00:00+00:00',
    })[0]


@pytest.mark.parametrize(('title', 'body', 'expected'), [
    ('Unfamiliar Aurora 9 unveiled',
     'The phone runs a new processor. It can locate nearby tablets and watches.', 'excluded'),
    ('Unfamiliar Aurora 9 unveiled',
     'This smartphone has a fast display and can connect to a tablet.', 'excluded'),
    ('A new compact device announced',
     'The maker introduced a new smartphone. Nearby tablets can be located from its screen.', 'excluded'),
    ('新款星云九号发布',
     '该手机搭载全新芯片，并支持查找附近的平板电脑。', 'excluded'),
    ('新款便携设备亮相',
     '厂商发布了一款智能手机，支持与平板互联。', 'excluded'),
    ('Unfamiliar Pad Pro debuts',
     'The new gaming tablet feels closer to a big phone than a regular tablet.', 'main'),
    ('New gaming tablet launched',
     'This tablet uses the same processor as a phone. The phone runs a companion app.', 'main'),
    ('新款游戏平板发布',
     '平板采用移动芯片，与手机使用相同处理器。', 'main'),
    ('Unfamiliar tablet form factor concept',
     'A detachable device blurs tablet and laptop boundaries; no launch is verified.', 'research'),
    ('Unfamiliar maker unveils Aurora 9',
     'The new device is an Android tablet with a detachable keyboard.', 'research'),
    ('Unfamiliar maker unveils Aurora 9',
     'The rugged tablet pairs with phones and laptops for file transfer.', 'research'),
    ('陌生品牌发布星云九号',
     '这是一款安卓平板电脑，支持分离式键盘和手机互联。', 'research'),
    ('Unfamiliar maker describes a new device',
     'It may be a tablet-first detachable or another ambiguous form factor.', 'research'),
    ('Unfamiliar Aurora 9 unveiled',
     'The phone runs a new processor with a large display, but no tablet evidence.', 'excluded'),
])
def test_primary_subject_family(classifier, title, body, expected):
    assert classifier(title, body) == expected
