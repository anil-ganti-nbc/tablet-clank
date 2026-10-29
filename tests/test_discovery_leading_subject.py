"""Public leading-subject controls, not private live publisher evidence."""
import pytest

from test_discovery_primary_subject import classifier


@pytest.mark.parametrize(('title', 'body', 'expected'), [
    ('Maker launches new gaming controller',
     'The new controller fits smaller tablets and phones.', 'excluded'),
    ('Maker releases a new power bank',
     'The power bank charges tablets over USB-C.', 'excluded'),
    ('厂商推出全新游戏手柄', '新手柄可连接平板电脑和手机。', 'excluded'),
    ('全新移动电源发布', '移动电源可以为平板充电。', 'excluded'),
    ('New tablet launches with detachable controllers',
     'The gaming tablet supports modular controllers and a keyboard.', 'main'),
    ('新款平板发布，支持游戏手柄与键盘', '该平板支持手柄和键盘。', 'main'),
    ('Windows detachable tablet unveiled',
     'The tablet detaches from its keyboard and compares with laptops.', 'main'),
    ('Maker introduces a portable device',
     'The new device is a lightweight Android tablet with a detachable keyboard.', 'research'),
    ('Maker discusses a portable concept',
     'It may be a tablet-first detachable or another ambiguous form factor.', 'research'),
    ('陌生品牌推出新设备', '这是一款安卓平板电脑，可连接手机和分离式键盘。', 'research'),
    ('A new device is described',
     'The tablet pairs with laptops and a controller; no form factor is confirmed.', 'research'),
    ('New device announced',
     'A gaming controller supports a tablet and phones.', 'excluded'),
    ('PaperBook Pro launched',
     'After an iPad announcement, the maker unveiled its new notebook. Related: Android tablet.', 'excluded'),
    ('New laptop family announced',
     'A notebook ships with an OLED screen. Related reading: new tablet launched.', 'excluded'),
    ('Device price and availability listed',
     'The maker opened preorders for its notebook. Also read: Android tablet.', 'excluded'),
    ('New device goes on sale',
     'Open sale has started for the latest smartphone. Related: tablet launch.', 'excluded'),
    ('Device maker fined over gaming claims',
     'A regulator found deceptive marketing practices. Related: gaming tablet unveiled.', 'excluded'),
    ('Devices updated to a new operating system',
     'The update is available for several phones. Supported devices also include a tablet.', 'excluded'),
    ('Digital sales statistics released',
     'Phones, tablets and other digital products saw sales growth.', 'excluded'),
    ('数码产品销量同比增长', '平板和手机销量同比增长。', 'excluded'),
    ('平板 Pro 国补后仅需 999 元', '这款平板可以领取消费券。', 'excluded'),
    ('Tablet subsidy discount: save today', 'The tablet is an existing product.', 'excluded'),
    ('新款平板发布，定价 1999 元起', '新款平板搭载移动处理器。', 'main'),
    ('New tablet announced with keyboard support',
     'The tablet has launch pricing; a phone and laptop are comparisons.', 'main'),
    ('New research device described',
     'A small screen device has unusual controls. Also read: Android tablet.', 'excluded'),
    ('Unfamiliar device announced',
     'The maker has officially launched its latest rugged tablet for field work.', 'research'),
])
def test_leading_primary_subject_family(classifier, title, body, expected):
    assert classifier(title, body) == expected


def test_release_pins_authenticate_actual_profile_bytes():
    import hashlib
    from pathlib import Path
    from tablet_clank import discovery as d
    raw = (Path(__file__).resolve().parents[1] / 'config/d1-tablets.v1.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == d.PROFILES_SHA
    assert hashlib.sha256((d.CODE_SHA + '\n' + d.PROFILES_SHA).encode('ascii')).hexdigest() == d.IDENTITY
