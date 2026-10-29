# Manual D1 Tablet Discovery

Discovery is a separate, proposal-only inbox, **disabled by default**. It never
opens the catalogue, admits products, changes the source registry, or writes
catalogue observations/events/delivery queues. No startup or GET collects,
imports, reviews or sends anything. Legacy commands and default Windows launch
remain unchanged; do not use the ordinary dashboard's collection controls for
this integration.

## Shared producer prerequisite and identity

Obtain the accepted shared Discovery Core executable separately. It is not
vendored here and OEM Radar is not a runtime dependency. The consumer mechanics
(atomic generation pointer, append-only observations, owned evidence and separate
editorial labels) adapt OEM Radar merge
`f5a2379e0a2953a471850785648b7e058970cb2a`.

* Executable: unchanged `d1.py`, accepting `d1.profiles.v1`, producing `d1.lead.v2`.
* Executable SHA256:
  `eaac15eb9ad414b2bbdd63870b70bbc1a8b2d93d9f21f1308c43db3217c69bf1`.
* Profile: `config/d1-tablets.v1.json`, sole profile `tablets`, destination
  `tablet-clank:proposal-review`.
* Profile SHA256:
  `ff4f12a480bac78fd102a1e9dde74121bb0315a147ae9c9ba7889c1d904c2a0a`.
* Combined executable/profile identity:
  `4c838ff26a9f83725ba9256ef24e21793841aafa08a7c4d659a76f9dc96c271f`
  (SHA256 of the ASCII executable SHA, newline, then profile SHA, no final newline).
  This is a fixed release constant; both actual raw files must still match their pins.
* Stable consumer producer key: `tablet-d1-v1`. Pins are constants in
  `tablet_clank/discovery.py`, not derived from whichever operator config is
  supplied. A profile revision requires explicit code/pin review, not an in-place
  modification of OEM's `profiles.json`.

Python 3.11+ and its standard library are the only runtime dependencies. Tests
require pytest; the campaign interpreter is Python 3.12.10. The producer also uses
only stdlib. A settings file supplies **absolute** executable, tablet profile,
producer-evidence and consumer-store paths. There are no personal-path defaults.
Use a dedicated consumer directory, never a catalogue or OEM runtime directory.

## Profile scope and source limitations

The profile has exactly two third-party sources:

| ID | Publisher | Feed | Interpretation |
|---|---|---|---|
| gizmochina | Gizmochina | https://www.gizmochina.com/feed/ | English-language technology reports, not official manufacturer verification |
| ithome | IT Home | https://www.ithome.com/rss/ | Simplified-Chinese technology reports, not official manufacturer verification |

Feed publication time, producer observation/collection/first-observation time and
consumer import time are separate clocks. Feed dates do not establish launch
dates. Missing/ambiguous dates are retained as uncertainty; brand/model stay
null. Publisher assertions do not establish manufacturer identity. A feed may
omit article prose, provide only a headline, omit tablets entirely, or change
its format. Copied capture evidence is the feed, not a fetched full article.

Configured terms cover tablets, iPad/MatePad and Pad/Tab product phrases, including
Android/iPadOS/Windows/ChromeOS, detachable, rugged/gaming and regional launches.
No OEM roster is used. Negative rules operate on **titles**, not incidental body
mentions. Relevance first admits explicit tablet-primary headlines despite incidental
phone/laptop/accessory comparisons. Without such a headline, fallback evidence
must describe a tablet as the subject, definition or apposition in the **first
sentence**, within 320 leading characters. A preceding phone/controller/power-bank/
laptop/watch subject blocks that fallback. Later related-article links, device
lists, compatibility claims and sales statistics are not tablet-primary evidence.
Unknown-brand documents with a clear leading tablet definition can still reach
research, as can genuinely ambiguous tablet forms; no manufacturer/model roster
is used. Title exclusions cover primary gaming controllers and power banks,
including Chinese terms, while a tablet supporting controllers/keyboard remains
eligible. Routine English/Chinese subsidy, coupon, discount and digital-sales
statistics titles are excluded, not ordinary launch-price statements. These
conservative lexical rules can miss genuine tablet documents whose introductions
omit or delay clear subject evidence; they cannot resolve every mixed subject or
pronoun reference. Primary phones/watches/laptops/convertibles/accessories/e-readers,
reviews and deals are excluded. Positive event rules require a tablet title and
announcement/availability language; rumors and ambiguous forms may remain research.
These lexical rules are fallible, not a universal form-factor classifier. Mixed
product announcement headlines and named tablet accessories remain boundary cases
for human review. Unresolved counts overlap main/research and include missing
evidence or an unresolved event; null identity is disclosed for every proposal.

Endpoint/profile selection is not source qualification. Public generic tests do
not prove source accessibility, publisher accuracy, frozen16 recovery/noise, live
collection, or independent review clearance. Those are parent/reviewer work; no
A–E or overall milestone verdict is implied by passing tests.

## Explicit manual commands

Commands below assume the repository environment's Python and illustrative,
non-personal Windows paths; substitute your own **absolute** paths. The example
`config/d1-discovery.settings.example.json` is disabled and contains no secrets.
Create the isolated producer-state directory before configure/import. Never put
outputs under read-only producer inputs.

```text
python -m tablet_clank.cli discovery --settings C:/TabletDiscovery/settings.json configure --producer-id tablet-d1-v1 --producer C:/DiscoveryCore/d1.py --profiles C:/TabletDiscovery/config/d1-tablets.v1.json --evidence-root C:/TabletDiscovery/producer-state --data-dir C:/TabletDiscovery/consumer-state
python -m tablet_clank.cli discovery --settings C:/TabletDiscovery/settings.json enable

# Explicit LIVE refresh: only run after owner/source qualification approval.
python -m tablet_clank.cli discovery --settings C:/TabletDiscovery/settings.json refresh

# Or import an existing export with evidence below the configured evidence root.
python -m tablet_clank.cli discovery --settings C:/TabletDiscovery/settings.json import C:/TabletDiscovery/producer-state/leads.jsonl
python -m tablet_clank.cli discovery --settings C:/TabletDiscovery/settings.json list
python -m tablet_clank.cli discovery --settings C:/TabletDiscovery/settings.json show LEAD_ID
python -m tablet_clank.cli discovery --settings C:/TabletDiscovery/settings.json review LEAD_ID --label editorial_keep
python -m tablet_clank.cli discovery --settings C:/TabletDiscovery/settings.json review LEAD_ID --label editorial_research
python -m tablet_clank.cli discovery --settings C:/TabletDiscovery/settings.json review LEAD_ID --label editorial_dismiss
python -m tablet_clank.cli discovery --settings C:/TabletDiscovery/settings.json disable
```

Configure never enables automatically. Enable changes only the local enabled
flag, not a scheduler/service. Disable refuses import/refresh/review while
preserving every proposal, observation, evidence blob and editorial history.
List/show/GET remain read-only and usable while disabled. Producer review state
and consumer editorial state are independent; neither is product admission.

### Discovery-only view

```text
python native/windows/launcher.py --discovery-only --settings C:/TabletDiscovery/settings.json --port 8789
# Direct CLI alternative, no browser or runtime marker:
python -m tablet_clank.cli discovery --settings C:/TabletDiscovery/settings.json serve --port 8789
```

Both bind only `127.0.0.1`. Open `http://127.0.0.1:8789/discovery`.
Ports 8765 and 8787 are refused by this Discovery server. The Windows mode uses
the existing thread/readiness/signal pattern but branches before ordinary state
configuration, `Database`, and legacy webapp imports. Its marker is
`DATA_DIR/runtime/discovery-dashboard.json`; stopping removes it. Set
`TABLET_CLANK_NO_BROWSER=1` to avoid browser opening. No service is installed or
restarted. All retained proposals are rendered (no hidden result cap), and
`/api/discovery` returns all records and histories. At pilot scale this deliberately
uses a full page, not pagination. Editorial review is CLI-only. POST/PUT/PATCH/
DELETE are refused; `/collect` and all other legacy routes are absent.

## Persistence, failures and rollback

Each import is fully validated before consumer writes. Unknown versions/profiles,
wrong tablet destination/source metadata, duplicate IDs, unsafe evidence paths,
changed evidence hashes, and nonliteral passages refuse intake. Computing/watch
proposals are explicitly excluded. Missing evidence is retained as
`unavailable/quarantined`, never silently verified. Text and raw capture are
copied by SHA into consumer-owned evidence; links remain valid after restart and
changed cwd. Evidence responses are text/plain, nosniff and sandboxed. HTML fields
and passages are escaped.

The consumer reuses generation publication: a SQLite sidecar plus matching JSONL
export are written under `versions/GENERATION`; `CURRENT` is replaced atomically
only after preparation succeeds. Changed observations append, identical imports
are suppressed, omitted leads remain, and review history is separate. Failed
refresh or publication leaves the previous CURRENT usable. Refresh invokes the
pinned executable with explicit tablet config and a new isolated state below
`DATA_DIR/refresh-staging`, refusing non-COMPLETE reports. Staging retains producer
run reports/evidence for inspection, not an unattended job. Fresh producer clocks
can append observations even when article prose is unchanged. Export replay with
identical clocks deduplicates. Do not interpret every observation as a new launch.

Operate one manual writer at a time (import/refresh/review); there is no scheduler.
Do not edit store files or CURRENT while a command is running. Retained generations
and staging have no automatic garbage collection; disk usage grows. Filesystem
atomic replace protects ordinary process failures, not a guarantee against disk
failure or sudden power loss. Settings and store locations are operator-trusted;
this loopback view has no remote authentication and must not be proxy-exposed.

For rollback, disable first and stop only the Discovery-only process. Preserve the
entire consumer directory and settings as an offline backup. To select an older
snapshot with all writers stopped, atomically replace CURRENT with the previous
32-hex generation directory name (keep its SQLite/JSONL pair and owned evidence).
Review changes newer than that snapshot will not be visible; retain their newer
generations for recovery. Never substitute or restore the catalogue database.
Removing this integration's code/config is a source rollback, not permission to
restart legacy collectors, change OEM Radar, or activate delivery.

## Offline tests and external producer selection

```text
python -m pytest -rA
# Windows cmd examples; use equivalent environment syntax for your shell:
set TABLET_D1_ROOT=C:/DiscoveryCore
set TABLET_D1_FIXTURE=generic
python -m pytest tests/test_discovery_external.py -rA -s
```

Public storage/view controls are explicitly synthetic and run without producer
captures. External tests execute the actual pinned producer's replay/proposal/
validator code. `generic` selects public synthetic RSS, never fake private
publisher evidence. Alternatively set `TABLET_D1_FIXTURE` to an **absolute** private
D1 capture-manifest JSON path with one entry per configured source. Inputs are
read-only; pytest output belongs to its separate temporary directory. Only an
unset `TABLET_D1_ROOT` skips external tests; invalid configured roots/manifests or
pin mismatches fail. Run all tests with network denial (allow only loopback HTTP
controls). In the bounded campaign the parent-supplied `guards` directory is on
PYTHONPATH; no guard or private captures are publication payload. No live or paid
requests are needed for the suite.
