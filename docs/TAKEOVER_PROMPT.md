# Tablet Clank takeover prompt

You are taking over an existing project with no previous conversation context. Repository state is authoritative.

1. Read `docs/PROJECT_STATE.md`.
2. Read `HANDOFF.md`.
3. Read `docs/ARCHITECTURE.md`.
4. Read `docs/SOURCE_INVENTORY.md`.
5. Inspect Git status and recent log.
6. Run the canonical tests.
7. Verify database state and integrity where the database exists.
8. Compare repository reality against the documentation and report discrepancies before modifying code.
9. Continue only the documented `NEXT_ACTION`.

Do not perform speculative refactors. Do not expand OEM/source scope unless explicitly instructed. Do not promote experimental sources automatically. Do not enable production or alerts automatically. Preserve evidence and failure isolation. Run tests before and after meaningful changes. Update `HANDOFF.md` and `docs/PROJECT_STATE.md` before ending the session.
