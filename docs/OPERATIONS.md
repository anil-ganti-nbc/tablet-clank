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
python -m tablet_clank.cli collect samsung_us_sitemap
python -m tablet_clank.cli collect --all
```

These commands use offline fixtures. Controlled live runs require the explicit flag:

```text
python -m tablet_clank.cli collect apple_in_sitemap --live
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

Apple’s live navigation sitemap returned 372 raw links and 23 accepted candidates in one run. Samsung’s configured URL returned HTTP 404. Neither source is production validated.
