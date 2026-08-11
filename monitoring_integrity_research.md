# Monitoring Integrity Research

**Scope and purpose.** This is a defensive research report on the current desktop
app's monitoring engine: what it can and can't see, which common input-automation
techniques would defeat it, and what could realistically be added to this codebase
to detect or reduce that risk. It intentionally contains **no working bypass code,
scripts, or build instructions** for any of the techniques discussed — only
conceptual explanations (at the level of publicly documented OS input APIs) and
countermeasure analysis. The goal is to help decide what, if anything, is worth
building next, and to be honest about what client-side monitoring fundamentally
cannot guarantee.

## How the current engine actually works

Grounded in the real implementation, not a general description:

- **Input presence, not content.** [`KeyboardMonitor`](monitoring/keyboard_monitor.py)
  and [`MouseMonitor`](monitoring/mouse_monitor.py) use `pynput` global listeners
  (OS-level input hooks). On every keypress, mouse move, or click, they call
  `idle_detector.reset_activity()`. No keystrokes, key content, or click targets
  are recorded — only "an input event happened."
- **Idle detection is a pure time-since-last-input threshold.**
  [`IdleDetector`](monitoring/idle_detector.py) polls once a second; if
  `now - last_activity >= idle_threshold` (300s by default), it flips to idle and
  dispatches `"Idle Started"`. `reset_activity()` only dispatches `"Active Again"`
  on the idle→active *transition* — it has no concept of "how much" or "what kind"
  of activity occurred, just whether any occurred recently.
- **Screenshot capture is on its own independent timer**, not gated by idle
  state. [`ScreenshotService`](monitoring/screenshot_service.py) fires every
  `screenshot_interval_seconds` (300s by default) via `mss`, regardless of
  whether the idle detector currently thinks the user is active or idle.
- **Everything is client-reported.** Local events are saved to `monitor.db` and
  pushed to the backend via [`sync_service.py`](sync_service.py) using a Bearer
  token. The backend has no independent way to verify that a reported "Active"
  state, or a screenshot, reflects genuine human activity — it trusts what this
  process sends it.

That last point matters for every technique below: this system's trust boundary
is the client machine itself. Anything able to inject standard OS-level input
events on that machine is, by construction, indistinguishable from a real user
to `pynput` — this isn't a bug in this codebase, it's the nature of any
activity-presence monitor that observes input at the OS level rather than
verifying the human behind it.

---

## Mouse movement software

**How it works, conceptually.** Utility programs that periodically reposition or
nudge the cursor using standard OS input APIs (the same category of API used to
programmatically move a cursor for accessibility tools, testing frameworks, etc.).

**Bypass assessment.** Full bypass of idle detection. `pynput`'s mouse listener
hooks the same low-level input stream a physical mouse generates, so a
programmatic move is observably identical to `MouseMonitor._on_move` — it calls
`reset_activity()` exactly as a real move would. Screenshot capture isn't gated
by idle state at all, so this doesn't affect screenshots either way; it only
keeps the *active/idle split* looking continuously active.

**Possible detection in this codebase.** `MouseMonitor._on_move` currently
discards the actual `(x, y)` coordinates — it only triggers a timestamp reset.
Capturing and analyzing those coordinates would let `IdleDetector` flag
*suspiciously constrained* movement (e.g., oscillating within a tiny fixed pixel
radius, or firing at exact periodic intervals) as a secondary, soft
"activity looks synthetic" signal surfaced to admins rather than acted on
automatically.

**Limitations.** This is a heuristic, not proof. Any jiggler sophisticated enough
to randomize its movement pattern defeats it, and the false-positive cost is
real — a person who works mostly via keyboard shortcuts or reads for long
stretches with minimal mouse movement would look "suspicious" under the same
heuristic. It should never be the basis for an automated penalty, only a
data point a human reviews alongside everything else.

## Automatic mouse jigglers — software

**How it works, conceptually.** Functionally the same category as "mouse
movement software" above — background utilities specifically marketed for
keeping a machine's status looking active, typically doing small periodic cursor
nudges via the same standard OS input APIs.

**Bypass assessment.** Same as above: full bypass of idle detection, no effect on
screenshot cadence. Worth noting explicitly since this is the most common,
lowest-effort tool in this category that someone would actually reach for.

**Possible detection in this codebase.** Same coordinate-pattern heuristic as
above. Additionally, because screenshots keep flowing on their own timer
regardless of activity state, a screenshot-content check (see the shared
mitigation note at the end of this report) is a more informative signal here
than the movement heuristic alone — a jiggler keeps "Active" true, but it can't
make the screen show anything other than whatever's actually on it.

**Limitations.** Same as above — pattern-based detection is an arms race, and a
jiggler with randomized timing/offsets is trivial to build once someone knows a
detector is looking for regularity.

## Automatic mouse jigglers — hardware (USB)

**How it works, conceptually.** A physical USB device that either mechanically
moves an actual mouse, or presents itself as a HID input device and injects
movement reports directly at the USB/driver level.

**Bypass assessment.** Full bypass, and structurally the hardest variant to do
anything about. From the OS driver's perspective — and therefore from
`pynput`'s perspective, which sits above that layer — this is indistinguishable
from a human hand. Unlike software jigglers, it doesn't require running any
unauthorized process on the machine, so it isn't visible to anything this
Python application could inspect at all.

**Possible detection in this codebase.** None, realistically. There is no signal
available at the application layer that separates "physical HID device moving
the cursor because a person is using it" from "physical HID device moving the
cursor because it's a jiggler." Any real mitigation for this category lives
outside this codebase entirely — endpoint/USB device management (e.g. Windows
Group Policy or MDM restrictions on unrecognized HID composite devices) or
physical asset spot-checks.

**Limitations.** Worth stating plainly rather than gesturing at a code fix that
doesn't exist: this is a genuine blind spot for any software-only monitoring
approach, and it's out of scope for changes to this repository.

## Keyboard auto-press software

**How it works, conceptually.** The keyboard equivalent of mouse-move software —
utilities that send synthetic keypress events via standard OS input APIs on a
timer or pattern.

**Bypass assessment.** Full bypass of idle detection, for the same structural
reason as mouse automation: `KeyboardMonitor._on_press` only checks that *a* key
event occurred, never which key or what it produced, so even a script pressing
a single harmless key (e.g. a modifier key with no visible effect) repeatedly
is sufficient to keep the session "Active" indefinitely.

**Possible detection in this codebase.** `_on_press` currently receives the
`key` object and discards it. Similar to the mouse case, logging *which* key
(not its content-bearing effect, just identity/frequency) could support a
regularity heuristic — e.g., the same single key firing at suspiciously exact
intervals — as a soft signal.

**Limitations.** Same caveats as the mouse pattern heuristic: easy to randomize
around, and real workers who lean on a small set of shortcut keys repeatedly
could trigger false positives. This is not, and shouldn't become, keystroke
content logging — that would be a significant privacy/trust change to what this
app discloses to employees (see [`StatusView.jsx`](frontend/src/StatusView.jsx)),
and is out of scope for a detection mechanism this narrow.

## Macro tools

**How it works, conceptually.** General-purpose record/replay or scripted-action
tools that combine mouse and keyboard automation, often with configurable
randomization (variable delays, non-linear cursor paths, varied key choice)
specifically to look less mechanical than a simple jiggler.

**Bypass assessment.** Full bypass, and a strictly stronger version of the two
techniques above — since this engine's idle detection only asks "was there any
input," a macro tool doesn't need any sophistication to defeat it; the
randomization features only matter once (if) a regularity-based heuristic like
the ones proposed above is actually in place.

**Possible detection in this codebase.** Nothing beyond what's already listed for
mouse/keyboard automation. Because macro tools can be built to defeat a
regularity heuristic specifically, they're a good illustration of why
input-timing heuristics are a soft, secondary signal at best.

**Limitations.** This is the clearest case of the underlying arms-race dynamic:
detection sophistication and evasion sophistication escalate together, and a
timing/pattern-based detector has no upper bound on how well it can be defeated.

## Scripted input (e.g. AutoHotkey-style automation)

**How it works, conceptually.** Scripting environments that let a user author
custom input-automation logic (mouse, keyboard, or both) rather than using a
pre-built tool. Functionally this is the same category as "macro tools" above —
the distinction is authorship (custom script vs. off-the-shelf utility), not
mechanism.

**Bypass assessment.** Identical to macro tools: full bypass of idle detection,
no interaction with screenshot cadence.

**Possible detection / limitations.** Same as macro tools. Worth noting for
completeness that because these are general-purpose scripting environments (not
single-purpose jiggler apps), there's no fixed "signature" to look for even in
principle — a custom script's behavior is whatever its author wrote.

## Remote desktop considerations

**How it works.** Someone connects to the monitored machine's session over
RDP (or similar remote-access protocol) and interacts with it from elsewhere.

**Bypass assessment — more nuanced than the categories above.** This isn't a
single bypass technique so much as a different threat shape, and it cuts both
ways against this engine:

- If a *different* person (not the employee) drives the machine over RDP while
  the employee is physically elsewhere, their real input generates real
  low-level input events in that session — `pynput` generally still sees them,
  so the engine reports genuinely "Active" activity that isn't actually the
  employee. This isn't spoofed input at all; it's a substitution-of-operator
  problem the input layer has no way to see.
- Conversely, Windows RDP session topology can also produce **false idle
  readings**: connecting remotely can disconnect the local console session, and
  depending on which session this app's process (and its `pynput` hooks) is
  running in relative to where the OS delivers input, activity from a
  legitimate remote worker could go unseen by the low-level hooks — the mirror
  image problem to a bypass.
- Screenshots in either case show whatever is actually rendered in that
  session, which is a genuinely useful cross-check the input-timing signal
  doesn't have on its own.

**Possible detection in this codebase.** `pywin32` is already a project
dependency (used elsewhere in this app). Its `win32ts` module can query
whether the current session is a console session or a remote (RDP) session.
Recording that as metadata alongside the existing heartbeat (`session_type:
console | rdp`) is a concrete, implementable addition that gives admins
context they currently have no visibility into at all — not a verdict, just a
label that changes how "Active" should be interpreted for that stretch of time.

**Limitations.** Session-type detection tells you *how* the machine was
accessed, not *by whom* or *whether that's a problem* — remote work over RDP is
often completely legitimate, so this needs a policy decision (is RDP allowed at
all, for which roles) before the signal is actionable, not just a code change.

## Virtual machines (high level)

**How it works, at a conceptual level.** Two distinct scenarios worth
separating:

1. Running this monitoring app *inside* a VM while real work happens somewhere
   else (the host, or a different, unmonitored VM/machine). The app faithfully
   reports whatever does or doesn't happen inside its own VM — this is really
   "the app isn't installed where the work occurs," not a bypass of its logic.
2. Using hypervisor-level guest-input-injection tooling to simulate activity
   *inside* the monitored VM from outside it, without a human present in the
   guest. This is mechanically the same category as software mouse/keyboard
   automation (synthetic input arriving at the guest's OS input layer), just
   originating from the host/hypervisor rather than a process running inside
   the guest — which can make it even less visible to anything running in the
   guest, including this app.

**Bypass assessment.** Scenario 1 isn't really a bypass of the monitoring
*logic* — it's a deployment/asset-tracking gap (is the monitored install
actually where the work happens). Scenario 2 is a genuine bypass, structurally
identical to the software-jiggler case, just delivered from a layer this
process can't observe at all.

**Possible detection in this codebase.** For scenario 1, a one-time
"is this machine a VM" check at startup is cheap and already feasible with the
existing `pywin32` dependency (e.g. reading `Win32_ComputerSystem.Model` via
WMI for known hypervisor signatures) and could be surfaced as employee/machine
metadata on the dashboard. For scenario 2, there is no meaningful detection
available at this app's layer, for the same reason as the hardware-jiggler
case — the injected input is indistinguishable from genuine input once it
reaches the guest OS.

**Limitations.** VM presence alone proves nothing — plenty of legitimate setups
(managed corporate VM images, VDI) run this kind of monitoring inside a VM on
purpose. Like the RDP signal, this is only useful paired with a policy decision
about what's actually allowed, and it does nothing against scenario 2.

---

## Cross-cutting notes

**A screenshot-content check is the one mitigation that helps across several
categories at once.** Every technique above targets the *idle/active
classification* specifically — none of them can alter what the screen actually
shows, because screenshot capture already runs on its own independent timer
regardless of idle state (see "How the current engine actually works," above).
A lightweight check for near-identical consecutive screenshots (simple
pixel-diff or perceptual hash — no new dependency needed, `Pillow` is already
used in `image_processing.py`) would be a soft, cross-referenced signal: "Active"
status alongside a screen that hasn't visibly changed across several capture
intervals is worth a human glance. It's not proof either — someone reading a
static document, or watching content on a second monitor while this monitor's
screen doesn't change, would trigger the same signal.

**The fundamental limitation, stated plainly.** Everything proposed in this
report is a client-side heuristic layered on top of a system that already
trusts the client to self-report honestly. None of it addresses the deeper
problem: anyone with sufficient access to the monitored machine to run
input-automation tooling in the first place typically also has enough access to
inspect, patch, or replace this application's own code, at which point no
amount of heuristic detection *inside that code* is meaningful — that's a
client-integrity/tamper-resistance problem, which is a different (and much
larger) undertaking than anything covered here, and isn't something this report
recommends pursuing given the trust-based nature of the current architecture.

**Recommended priority, if any of this gets built.** In rough order of
implementation cost vs. signal value: (1) screenshot near-duplicate check —
cheap, reuses existing dependencies, cross-cuts several bypass categories; (2)
RDP session-type tagging via `pywin32` — cheap, adds real context currently
missing entirely; (3) VM-presence tagging — cheap, low value alone, more useful
paired with (2); (4) input regularity heuristics on mouse/keyboard — genuinely
useful as a soft signal, but the highest false-positive risk and the easiest
for a motivated user to defeat, so lowest priority of the four.
