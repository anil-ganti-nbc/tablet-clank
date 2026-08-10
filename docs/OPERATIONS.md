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

## Sources and collection

```text
python -m tablet_clank.cli sources
python -m tablet_clank.cli collect apple_in_sitemap
python -m tablet_clank.cli collect apple_us_ipad_pro_store
python -m tablet_clank.cli collect apple_in_ipad_pro_store
python -m tablet_clank.cli collect samsung_us_sitemap
python -m tablet_clank.cli collect --all
```

These commands use offline fixtures. Controlled live runs require the explicit flag:

```text
python -m tablet_clank.cli collect apple_in_sitemap --live
python -m tablet_clank.cli collect apple_us_ipad_pro_store --live
python -m tablet_clank.cli collect apple_in_ipad_pro_store --live
python -m tablet_clank.cli collect samsung_us_sitemap --live
```

## Health and database

```text
python -m tablet_clank.cli status
python -m tablet_clank.cli health
python -m tablet_clank.cli db-integrity
```

Schema version is read from `schema_migrations`; the current migration reference is `migrations/001_initial.sql`. Runtime state lives under `var/` and is ignored by Git.

## Current live caveat

Apple’s live navigation sitemap returned 372 raw links but, after the identifier-quality fix, 0 accepted candidates and failed closed. Corrected Apple Store runs for both US and IN returned 48 raw/validated/accepted configurations and then 48 resighted configurations. Samsung’s replacement XML sitemap returned 4 raw URLs, 3 accepted product candidates and 1 rejected generic category URL, then resighted the 3 accepted identities. No source is production validated.
