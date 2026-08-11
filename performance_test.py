"""
Resource usage measurement for the Activity Monitor desktop app.

Finds the running app by matching python processes whose command line
launches this project's main.py, then samples CPU/memory/disk/network/
thread metrics for it (plus its child processes, since pywebview embeds
a WebView2 renderer as a separate OS process -- watching main.py alone
would undercount real memory/CPU usage of "the app" as a user experiences
it).

IMPORTANT CAVEAT ON NETWORK BYTES: psutil has no per-process network I/O
counter on Windows (Process.io_counters() covers disk only). The
net_sent_bytes_delta / net_recv_bytes_delta columns are therefore
SYSTEM-WIDE deltas (psutil.net_io_counters()) sampled around the same
window, not traffic isolated to this process. Treat them as a rough
proxy, not a precise measurement -- this is called out again in the
summary output so it isn't misread as per-process data.

Usage (see bottom of file / --help for the full list):
    python performance_test.py idle
    python performance_test.py active
    python performance_test.py screenshot
    python performance_test.py upload_screenshot
    python performance_test.py upload_event
    python performance_test.py continuous
    python performance_test.py compare --process chrome.exe
    python performance_test.py summary
"""

import argparse
import csv
import os
import time
from datetime import datetime

import psutil

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PY = os.path.join(ROOT_DIR, "main.py")
CSV_PATH = os.path.join(ROOT_DIR, "performance_results.csv")

CSV_FIELDS = [
    "timestamp",
    "scenario",
    "target_pids",
    "process_count",
    "cpu_percent",
    "memory_mb",
    "disk_read_bytes",
    "disk_write_bytes",
    "net_sent_bytes_delta_system_wide",
    "net_recv_bytes_delta_system_wide",
    "thread_count",
]

SCENARIOS = {
    "idle": dict(duration=15, interval=1,
                 instructions="Have the app open with monitoring NOT started (no 'Start Work' click)."),
    "active": dict(duration=20, interval=1,
                   instructions="Click 'Start Work' in the app first, then run this."),
    "screenshot": dict(duration=15, interval=0.5,
                        instructions=(
                            "Monitoring must already be started. This scenario needs a screenshot to fire "
                            "during the sampling window -- either wait for the natural interval "
                            "(app_settings.json: screenshot_interval_seconds), or temporarily lower it "
                            "before running so a capture happens within ~15s."
                        )),
    "upload_screenshot": dict(duration=10, interval=0.5,
                               instructions=(
                                   "Run this immediately after a screenshot was just captured (see 'screenshot' "
                                   "scenario) -- the upload fires asynchronously right after capture."
                               )),
    "upload_event": dict(duration=10, interval=0.5,
                          instructions=(
                              "Monitoring must already be started. Move the mouse or press a key right as this "
                              "starts so an Idle/Active event fires and triggers its background upload."
                          )),
    "continuous": dict(duration=1800, interval=30,
                        instructions="Monitoring should be started and left running for the full 30 minutes."),
}


def find_app_processes():
    """Return every process whose command line launches this project's
    main.py, plus all of their live children (recursively). pywebview
    spawns at least one child python.exe for its own event loop, and the
    edgechromium backend spawns a separate msedgewebview2.exe renderer
    tree -- matching only "the first hit" would silently undercount
    real app resource usage, so this collects the whole set and dedupes
    by pid."""
    def _launches_this_main_py(proc):
        cmdline = proc.info.get("cmdline") or []
        # cmdline args are whatever the caller typed (often the relative
        # "main.py", not an absolute path), so match on basename and
        # disambiguate by the process's working directory.
        if not any(os.path.basename(str(part)).lower() == "main.py" for part in cmdline):
            return False
        try:
            return os.path.normcase(proc.cwd()) == os.path.normcase(ROOT_DIR)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return True  # can't verify cwd -- fall back to the basename match

    matches = [proc for proc in psutil.process_iter(["pid", "name", "cmdline"]) if _launches_this_main_py(proc)]

    if not matches:
        return []

    procs = list(matches)
    for proc in matches:
        try:
            procs.extend(proc.children(recursive=True))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    seen = set()
    unique = []
    for p in procs:
        if p.pid not in seen and p.is_running():
            seen.add(p.pid)
            unique.append(p)
    return unique


def find_process_by_name(name):
    """Generic lookup for comparison runs (e.g. chrome.exe, Teams.exe).
    Returns every matching process plus its children, since apps like
    Chrome/Teams also run as a tree of processes."""
    matches = [p for p in psutil.process_iter(["pid", "name"])
               if (p.info.get("name") or "").lower() == name.lower()]
    procs = list(matches)
    for p in matches:
        try:
            procs.extend(p.children(recursive=True))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    seen = set()
    unique = []
    for p in procs:
        if p.pid not in seen and p.is_running():
            seen.add(p.pid)
            unique.append(p)
    return unique


def _prime_cpu_percent(procs):
    for p in procs:
        try:
            p.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def _sample(procs):
    cpu = mem_mb = 0.0
    read_b = write_b = 0
    threads = 0
    alive_pids = []
    for p in procs:
        try:
            cpu += p.cpu_percent(interval=None)
            mem_mb += p.memory_info().rss / (1024 * 1024)
            io = p.io_counters()
            read_b += io.read_bytes
            write_b += io.write_bytes
            threads += p.num_threads()
            alive_pids.append(p.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return cpu, mem_mb, read_b, write_b, threads, alive_pids


def _ensure_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="") as f:
            csv.DictWriter(f, fieldnames=CSV_FIELDS).writeheader()


def run_measurement(procs, scenario_label, duration, interval):
    if not procs:
        print(f"[performance_test] No matching process found for scenario '{scenario_label}'. Aborting.")
        return []

    _ensure_csv()
    _prime_cpu_percent(procs)
    net_before = psutil.net_io_counters()
    time.sleep(min(interval, 1))

    rows = []
    elapsed = 0.0
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        while elapsed < duration:
            procs = [p for p in procs if p.is_running()]
            if not procs:
                print(f"[performance_test] Target process exited mid-run at t={elapsed:.0f}s.")
                break

            cpu, mem_mb, read_b, write_b, threads, pids = _sample(procs)
            net_after = psutil.net_io_counters()
            row = {
                "timestamp": datetime.now().isoformat(),
                "scenario": scenario_label,
                "target_pids": ";".join(str(pid) for pid in pids),
                "process_count": len(pids),
                "cpu_percent": round(cpu, 2),
                "memory_mb": round(mem_mb, 2),
                "disk_read_bytes": read_b,
                "disk_write_bytes": write_b,
                "net_sent_bytes_delta_system_wide": net_after.bytes_sent - net_before.bytes_sent,
                "net_recv_bytes_delta_system_wide": net_after.bytes_recv - net_before.bytes_recv,
                "thread_count": threads,
            }
            writer.writerow(row)
            f.flush()
            rows.append(row)
            net_before = net_after

            time.sleep(interval)
            elapsed += interval

    return rows


def print_scenario_summary(scenario_label, rows):
    if not rows:
        print(f"\n[{scenario_label}] no samples recorded.")
        return
    cpu_vals = [r["cpu_percent"] for r in rows]
    mem_vals = [r["memory_mb"] for r in rows]
    print(f"\n[{scenario_label}] {len(rows)} samples")
    print(f"  CPU%    avg={sum(cpu_vals)/len(cpu_vals):.1f}  max={max(cpu_vals):.1f}")
    print(f"  Mem MB  avg={sum(mem_vals)/len(mem_vals):.1f}  max={max(mem_vals):.1f}")
    print(f"  Disk    read={rows[-1]['disk_read_bytes'] - rows[0]['disk_read_bytes']:+d}B  "
          f"write={rows[-1]['disk_write_bytes'] - rows[0]['disk_write_bytes']:+d}B (cumulative over window)")
    print("  Net     (system-wide proxy, not process-isolated -- see module docstring)")


def print_full_summary():
    if not os.path.exists(CSV_PATH):
        print("No performance_results.csv yet -- run a scenario first.")
        return

    by_scenario = {}
    with open(CSV_PATH, newline="") as f:
        for row in csv.DictReader(f):
            by_scenario.setdefault(row["scenario"], []).append(row)

    print("\n" + "=" * 78)
    print(f"{'Scenario':<20}{'Samples':>8}{'CPU% avg':>10}{'CPU% max':>10}{'Mem MB avg':>12}{'Mem MB max':>12}")
    print("-" * 78)
    for scenario, rows in by_scenario.items():
        cpu_vals = [float(r["cpu_percent"]) for r in rows]
        mem_vals = [float(r["memory_mb"]) for r in rows]
        print(f"{scenario:<20}{len(rows):>8}{sum(cpu_vals)/len(cpu_vals):>10.1f}"
              f"{max(cpu_vals):>10.1f}{sum(mem_vals)/len(mem_vals):>12.1f}{max(mem_vals):>12.1f}")
    print("=" * 78)
    print(f"Full data: {CSV_PATH}")
    print("Note: net_*_delta columns are system-wide, not isolated to the measured process(es).")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    for name, cfg in SCENARIOS.items():
        p = sub.add_parser(name, help=cfg["instructions"])
        p.add_argument("--duration", type=float, default=cfg["duration"], help=f"seconds (default {cfg['duration']})")
        p.add_argument("--interval", type=float, default=cfg["interval"], help=f"seconds (default {cfg['interval']})")

    compare_p = sub.add_parser("compare", help="Measure a different process by name for comparison (e.g. chrome.exe)")
    compare_p.add_argument("--process", required=True, help="Process name, e.g. chrome.exe or Teams.exe")
    compare_p.add_argument("--duration", type=float, default=60)
    compare_p.add_argument("--interval", type=float, default=1)

    sub.add_parser("summary", help="Print a summary table across everything recorded in performance_results.csv")

    args = parser.parse_args()

    if args.command == "summary":
        print_full_summary()
        return

    if args.command == "compare":
        procs = find_process_by_name(args.process)
        if not procs:
            print(f"No running process named '{args.process}' found.")
            return
        label = f"comparison:{args.process}"
        print(f"Measuring {args.process} ({len(procs)} process(es), pids={[p.pid for p in procs]}) "
              f"for {args.duration:.0f}s...")
        rows = run_measurement(procs, label, args.duration, args.interval)
        print_scenario_summary(label, rows)
        return

    cfg = SCENARIOS[args.command]
    print(f"Scenario '{args.command}': {cfg['instructions']}")
    procs = find_app_processes()
    if not procs:
        print("\nCould not find a running 'python main.py' process for this project.")
        print("Start the app first (from this folder): python main.py")
        return
    print(f"Tracking {len(procs)} process(es) (pids={[p.pid for p in procs]}) for {args.duration:.0f}s, "
          f"sampling every {args.interval:.1f}s...")
    rows = run_measurement(procs, args.command, args.duration, args.interval)
    print_scenario_summary(args.command, rows)
    print(f"\nAppended {len(rows)} rows to {CSV_PATH}")


if __name__ == "__main__":
    main()
