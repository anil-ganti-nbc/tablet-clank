import argparse
import json
from pathlib import Path
from .sources.registry import SOURCES, PRODUCTION_ALLOWLIST, runtime_source_ids, production_source_ids
from .storage.db import Database
from .soak import SoakLock, SoakLockError, lock_path_for_db, readiness_check, run_bounded, collector_for
from .campaign import CampaignError, build_manifest, load_manifest, preflight_campaign, run_campaign
from .production import readiness_check as production_readiness_check, run_production
from .pipeline import process

def _soak_campaign_command(args, parser):
    try:
        if args.init:
            if not args.campaign or not args.sources:
                parser.error("--init requires --campaign and --sources")
            manifest = build_manifest(
                args.campaign,
                [sid.strip() for sid in args.sources.split(",") if sid.strip()],
                cycles=args.cycles, interval_seconds=args.interval_seconds,
                canonical_db=args.canonical_db, campaign_db=args.campaign_db,
                report_path=args.report_path,
            )
            path = Path(args.manifest)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
            return 0
        if args.check:
            print(json.dumps(preflight_campaign(load_manifest(args.manifest)), ensure_ascii=False, sort_keys=True))
            return 0
        for report in run_campaign(args.manifest, fixture_mode=not args.live):
            print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    except (SoakLockError, CampaignError, RuntimeError, ValueError) as exc:
        print(f"campaign refused: {exc}")
        return 2


def main(argv=None):
    parser=argparse.ArgumentParser(prog="tablet-clank"); sub=parser.add_subparsers(dest="command",required=True)
    p=sub.add_parser("collect"); p.add_argument("source",nargs="?"); p.add_argument("--all",action="store_true"); p.add_argument("--live",action="store_true"); p.add_argument("--db",default="var/tablet_clank.db")
    p=sub.add_parser("soak"); p.add_argument("--cycles",type=int,default=12); p.add_argument("--interval-seconds",type=float,default=7200); p.add_argument("--db",default="var/tablet_clank.db"); p.add_argument("--check",action="store_true")
    p=sub.add_parser("production"); p.add_argument("--db",default="var/tablet_clank.db"); p.add_argument("--check",action="store_true")
    p=sub.add_parser("backup"); p.add_argument("output"); p.add_argument("--db",default="var/tablet_clank.db"); p.add_argument("--force",action="store_true")
    p=sub.add_parser("db-integrity"); p.add_argument("--db",default="var/tablet_clank.db")
    p=sub.add_parser("soak-campaign"); p.add_argument("--manifest",required=True); p.add_argument("--check",action="store_true"); p.add_argument("--live",action="store_true"); p.add_argument("--init",action="store_true"); p.add_argument("--campaign"); p.add_argument("--sources"); p.add_argument("--cycles",type=int,default=12); p.add_argument("--interval-seconds",type=float,default=7200); p.add_argument("--canonical-db",default="var/tablet_clank.db"); p.add_argument("--campaign-db"); p.add_argument("--report-path")
    sub.add_parser("sources"); sub.add_parser("health"); sub.add_parser("status")
    args=parser.parse_args(argv)
    # Handled before any Database() construction: the campaign runner owns
    # its isolated DB paths and must never open the default-path database.
    if args.command=="soak-campaign":
        return _soak_campaign_command(args,parser)
    db=Database(getattr(args,"db","var/tablet_clank.db"))
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
                # Single routing authority: soak.collector_for. The CLI must
                # not keep a second collector table — that is exactly how
                # honor_uk_tablets silently fell through to the wrong
                # collector class during Wave 2 deployment (failed honestly,
                # nothing persisted).
                result=process(db,collector_for(s,fixture_mode=not args.live),fixture_mode=not args.live)
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
    elif args.command=="backup":
        # Recovery points are writer-coordinated like every other mutation
        # (Fleet Law 7): the snapshot shares the soak lock domain.
        try:
            with SoakLock(lock_path_for_db(args.db), role="backup"):
                report=db.backup_to(args.output, overwrite=args.force)
            print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        except (SoakLockError, FileExistsError, RuntimeError) as exc:
            print(f"backup refused: {exc}")
            db.close()
            return 2
    elif args.command=="db-integrity": print(db.integrity())
    elif args.command in ("health","status"):
        for row in db.conn.execute("SELECT s.id,s.manufacturer,ss.baseline_complete,ss.consecutive_healthy_runs,MAX(r.finished_at) last_run FROM sources s LEFT JOIN source_state ss ON ss.source_id=s.id LEFT JOIN collector_runs r ON r.source_id=s.id GROUP BY s.id"):
            print(dict(row))
    db.close()

if __name__ == "__main__":
    raise SystemExit(main() or 0)
