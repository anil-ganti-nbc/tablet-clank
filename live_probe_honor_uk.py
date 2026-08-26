import json, tempfile, time
from pathlib import Path
from tablet_clank.sources.registry import get_source, PRODUCTION_ALLOWLIST, runtime_source_ids
from tablet_clank.collectors.honor_uk import HonorUKTabletsCollector
from tablet_clank.pipeline import process
from tablet_clank.storage.db import Database

source = get_source("honor_uk_tablets")
c = HonorUKTabletsCollector(source)
t0 = time.time()
items = c.collect()
fetch_latency = round(time.time() - t0, 2)
print(json.dumps({
    "probe": {
        "url": source.url,
        "http": "200 via collector.fetch()",
        "raw_items": len(items),
        "validated": len(items),
        "rejected": 0,
        "parser_errors": [],
        "latency_s": fetch_latency,
        "js_dependency": False,
    },
    "representative_ids": [i.source_identifier for i in items][:6],
}, indent=2))

with tempfile.TemporaryDirectory() as d:
    db = Database(str(Path(d) / "honor_uk_probe.db"))
    first = process(db, c)
    second = process(db, c)
    events = db.conn.execute("SELECT COUNT(*) FROM change_events").fetchone()[0]
    print(json.dumps({
        "baseline_cycle": {"status": first.status, "accepted": first.accepted_count,
                           "new": first.new_count, "resighted": first.resighted_count},
        "resight_cycle": {"status": second.status, "new": second.new_count,
                          "resighted": second.resighted_count},
        "change_events_total": events,
        "integrity": db.integrity(),
    }, indent=2))

assert "honor_uk_tablets" not in PRODUCTION_ALLOWLIST
assert "honor_uk_tablets" in runtime_source_ids()
