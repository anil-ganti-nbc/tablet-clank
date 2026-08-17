import argparse
import json
from .collectors.html_catalogue import HtmlCatalogueCollector
from .collectors.xml_sitemap import XmlSitemapCollector
from .collectors.apple_store import AppleStoreIPadProCollector
from .collectors.honor_cn import HonorCNTabletsCollector
from .collectors.tcl_global import TCLGlobalTabletsCollector
from .sources.registry import SOURCES, PRODUCTION_ALLOWLIST, runtime_source_ids, production_source_ids
from .storage.db import Database
from .soak import SoakLock, SoakLockError, lock_path_for_db, readiness_check, run_bounded
from .production import readiness_check as production_readiness_check, run_production
from .pipeline import process

def main(argv=None):
    parser=argparse.ArgumentParser(prog="tablet-clank"); sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("collect"); p.add_argument("source",nargs="?"); p.add_argument("--all",action="store_true"); p.add_argument("--live",action="store_true"); p.add_argument("--db",default="var/tablet_clank.db")
    p=sub.add_parser("soak"); p.add_argument("--cycles",type=int,default=12); p.add_argument("--interval-seconds",type=float,default=7200); p.add_argument("--db",default="var/tablet_clank.db"); p.add_argument("--check",action="store_true")
    p=sub.add_parser("production"); p.add_argument("--db",default="var/tablet_clank.db"); p.add_argument("--check",action="store_true")
    sub.add_parser("sources"); sub.add_parser("health"); sub.add_parser("status"); sub.add_parser("db-integrity")
    args=parser.parse_args(argv); db=Database(getattr(args,"db","var/tablet_clank.db"))
    if args.command=="sources":
        for s in SOURCES.values():
            membership = "production" if s.id in production_source_ids() else ("experimental" if s.state == "EXPERIMENTAL" else "disabled")
            print(f"{s.id}\t{s.manufacturer}\t{s.region}\t{s.state}\t{membership}")
    elif args.command=="collect":
        ids=list(runtime_source_ids()) if args.all else [args.source]
        with SoakLock(lock_path_for_db(args.db), role="manual-collect"):
            for sid in ids:
                if sid not in SOURCES: parser.error(f"unknown source: {sid}")
                s=SOURCES[sid]
                if s.state != "EXPERIMENTAL": parser.error(f"source is disabled: {sid}")
                if s.manufacturer == "Honor": collector_class = HonorCNTabletsCollector
                elif s.manufacturer == "TCL": collector_class = TCLGlobalTabletsCollector
                elif "Apple Store" in s.kind: collector_class = AppleStoreIPadProCollector
                else: collector_class = XmlSitemapCollector if "XML" in s.kind else HtmlCatalogueCollector
                result=process(db,collector_class(s,fixture_mode=not args.live),fixture_mode=not args.live)
                print(result)
    elif args.command=="soak":
        try:
            if args.check:
                with SoakLock(lock_path_for_db(args.db), role="soak-check"):
                    print(readiness_check(db))
            else:
                db.close()
                for report in run_bounded(args.db, cycles=args.cycles, interval_seconds=args.interval_seconds): print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        except (SoakLockError, RuntimeError, ValueError) as exc:
            print(f"soak refused: {exc}")
            db.close()
            return 2
    elif args.command=="production":
        try:
            if args.check:
                with SoakLock(lock_path_for_db(args.db), role="production-check"):
                    print(production_readiness_check(db))
            else:
                db.close()
                report = run_production(args.db)
                print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        except (SoakLockError, RuntimeError, ValueError) as exc:
            print(f"production refused: {exc}")
            db.close()
            return 2
    elif args.command=="db-integrity": print(db.integrity())
    elif args.command in ("health","status"):
        for row in db.conn.execute("SELECT s.id,s.manufacturer,ss.baseline_complete,ss.consecutive_healthy_runs,MAX(r.finished_at) last_run FROM sources s LEFT JOIN source_state ss ON ss.source_id=s.id LEFT JOIN collector_runs r ON r.source_id=s.id GROUP BY s.id"):
            print(dict(row))
    db.close()

if __name__ == "__main__":
    raise SystemExit(main() or 0)
