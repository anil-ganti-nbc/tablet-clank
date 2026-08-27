# Tablet Clank Windows local launcher

`launcher.py` starts the same stdlib-only dashboard as `native/macos/webapp.py`
(shared module, not a fork) bound to loopback only, on an OS-assigned
ephemeral port. State (database, logs, runtime marker) lives under
`%LOCALAPPDATA%\Tablet Clank\` unless `TABLET_CLANK_FIELD_TEST_HOME` overrides
it. Set `TABLET_CLANK_NO_BROWSER=1` to skip auto-opening the default browser.

Run it with the project virtualenv active:

```powershell
python native\windows\launcher.py
```

Launching this only starts the HTTP server. No collector runs until a human
clicks "Collect Now" (single source) or "Run all finalized collectors"
(production allowlist only) in the GUI, or invokes the CLI directly. No
Windows Task Scheduler entry is created by this launcher or by any other part
of this repository.
