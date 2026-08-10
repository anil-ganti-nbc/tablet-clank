import argparse
from .collectors.html_catalogue import HtmlCatalogueCollector
from .sources.registry import SOURCES, PRODUCTION_ALLOWLIST
from .storage.db import Database
from .pipeline import process

def main(argv=None):
    parser=argparse.ArgumentParser(prog="tablet-clank"); sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("collect"); p.add_argument("source",nargs="?"); p.add_argument("--all",action="store_true"); p.add_argument("--live",action="store_true")
    sub.add_parser("sources"); sub.add_parser("health"); sub.add_parser("status"); sub.add_parser("db-integrity")
    args=parser.parse_args(argv); db=Database()
    if args.command=="sources":
        for s in SOURCES.values(): print(f"{s.id}\t{s.manufacturer}\t{s.region}\t{s.state}\t{'production' if s.id in PRODUCTION_ALLOWLIST else 'experimental'}")
    elif args.command=="collect":
        ids=list(SOURCES) if args.all else [args.source]
        for sid in ids:
            if sid not in SOURCES: parser.error(f"unknown source: {sid}")
            s=SOURCES[sid]; result=process(db,HtmlCatalogueCollector(s,fixture_mode=not args.live),fixture_mode=not args.live)
            print(result)
    elif args.command=="db-integrity": print(db.integrity())
    elif args.command in ("health","status"):
        for row in db.conn.execute("SELECT s.id,s.manufacturer,ss.baseline_complete,ss.consecutive_healthy_runs,MAX(r.finished_at) last_run FROM sources s LEFT JOIN source_state ss ON ss.source_id=s.id LEFT JOIN collector_runs r ON r.source_id=s.id GROUP BY s.id"):
            print(dict(row))
    db.close()

if __name__ == "__main__":
    main()
