# Operations

## Environment

The project requires Python 3.11+ and pytest for tests. A portable local environment can be created with:

```text
python -m venv .venv
```

Activate it using the host shell, then install the project and test dependency if network/package installation is available:

```text
python -m pip install -e ".[test]"
```

The runtime itself has no third-party dependency.

## Tests

```text
python -m pytest -q -rA
```

Canonical tests are fixture-only and do not require internet access.

The Lenovo PSREF fixture is an offline parser probe only. It is exercised by the canonical test suite and is not available through `tablet-clank collect`; Lenovo is not registered as a runtime source.

The Legion cross-check also remains offline-only. Do not attempt live Lenovo collection until Lenovo exposes a reliably retrievable official model-table/export surface; browser automation and access-control bypass are out of scope.

## Sources and collection

```text
python -m tablet_clank.cli sources
python -m tablet_clank.cli collect apple_us_ipad_pro_store
python -m tablet_clank.cli collect apple_in_ipad_pro_store
python -m tablet_clank.cli collect samsung_us_sitemap
python -m tablet_clank.cli collect honor_cn_tablets_catalogue
python -m tablet_clank.cli collect honor_cn_tablets_comparison
python -m tablet_clank.cli collect tcl_global_tablets
python -m tablet_clank.cli collect --all
```

These commands use offline fixtures. Controlled live runs require the explicit flag:

```text
python -m tablet_clank.cli collect apple_us_ipad_pro_store --live
python -m tablet_clank.cli collect apple_in_ipad_pro_store --live
python -m tablet_clank.cli collect samsung_us_sitemap --live
python -m tablet_clank.cli collect honor_cn_tablets_catalogue --live
python -m tablet_clank.cli collect honor_cn_tablets_comparison --live
python -m tablet_clank.cli collect tcl_global_tablets --live

## Bounded experimental soak

```text
python -m tablet_clank.cli soak --check
python -m tablet_clank.cli soak --cycles 12 --interval-seconds 7200
```

The runner is serial, bounded and locked against overlapping manual collection. It writes reports to `var/logs/soak.jsonl`, stops on database-integrity or duplicate-identity failure, isolates source failures, and never sends alerts or promotes sources. Full operating semantics are documented in `docs/SOAK_OPERATIONS.md`.
```

## Bounded production execution (Promotion Wave 1)

```text
python -m tablet_clank.cli production --check
python -m tablet_clank.cli production
```

The production runner resolves exactly the sources in `PRODUCTION_ALLOWLIST` (currently `honor_cn_tablets_catalogue`, `honor_cn_tablets_comparison`, `tcl_global_tablets`), intersected with current `EXPERIMENTAL` state via `production_source_ids()`. It is serial, bounded to one cycle per invocation, shares the same `var/tablet_clank.soak.lock` locking domain as soak and manual `collect` (so runs cannot overlap), isolates source failures, and reuses the same identity/baseline semantics as soak and manual collection. It writes reports to `var/logs/production.jsonl`. There is no scheduler; production execution is on-demand only, same as manual collection. It never sends alerts (`ALERTS_ENABLED = False`, enforced in `readiness_check`) and never promotes additional sources.

## Health and database

```text
python -m tablet_clank.cli status
python -m tablet_clank.cli health
python -m tablet_clank.cli db-integrity
```

Schema version is read from `schema_migrations`; the current migration reference is `migrations/001_initial.sql`. Runtime state lives under `var/` and is ignored by Git.

## Current live caveat

Apple’s live navigation sitemap returned 372 raw links but, after the identifier-quality fix, 0 accepted candidates and failed closed. Corrected Apple Store runs for both US and IN returned 48 raw/validated/accepted configurations and then 48 resighted configurations. Samsung’s replacement XML sitemap returned 4 raw URLs, 3 accepted product candidates and 1 rejected generic category URL, then resighted the 3 accepted identities. Apple US/IN and Samsung are not production validated; Honor and TCL are (Promotion Wave 1).

The Xiaomi Mi Mall Pad 7/Pad 8 probe is offline-only. Its current fixtures intentionally fail closed because the requested numeric IDs resolve to unrelated products. Do not register or live-collect Xiaomi until a reliable public product/variant identity surface is proven.

## Post-soak state

The frozen six-source roster completed its 12-cycle soak on 2026-08-13 (see `docs/SOAK_READINESS.md` and `docs/SOAK_OPERATIONS.md` for the conceptual model). The soak service (`tablet-clank-soak.service`) is disabled/inactive and was not restarted for this promotion; its old roster now intentionally refuses to run (`resolve_soak_sources` raises, since 3 of its sources are production-allowlisted). `apple_in_sitemap` is retired and disabled; it remains historical evidence but cannot be selected by runtime collection or production. Alerts remain disabled; production allowlisting is now non-empty (Promotion Wave 1) but scheduling remains absent.
