from datetime import datetime
from repositories.event_repository import get_events_for_session
from repositories.screenshot_repository import get_screenshots_for_session
from repositories.session_repository import get_all_sessions

def calculate_statistics(session_id):
    events = get_events_for_session(session_id)
    screenshots = get_screenshots_for_session(session_id)
    if not events:
        return {
            "duration": 0,
            "active_time": 0,
            "idle_time": 0,
            "event_count": 0,
            "screenshot_count": len(screenshots),
        }

    start = datetime.fromisoformat(events[0]["timestamp"])
    end = datetime.fromisoformat(events[-1]["timestamp"])
    total_duration = int((end - start).total_seconds())

    idle_time = 0
    idle_start = None
    for event in events:
        timestamp = datetime.fromisoformat(event["timestamp"])
        if event["event_type"] == "Idle Started":
            idle_start = timestamp
        elif event["event_type"] == "Active Again" and idle_start:
            idle_time += int((timestamp - idle_start).total_seconds())
            idle_start = None

    active_time = total_duration - idle_time
    return {
        "duration": total_duration,
        "active_time": active_time,
        "idle_time": idle_time,
        "event_count": len(events),
        "screenshot_count": len(screenshots),
    }


def get_today_totals(employee_id, current_session_id=None):
    """Sum active/idle seconds across every session that started today
    FOR THE GIVEN EMPLOYEE. Completed sessions use their stored totals;
    the in-progress session (if any) is computed live so "today" includes
    work still happening.

    employee_id=None means "we don't know who's using this machine" (not
    yet activated) -- returns (0, 0) rather than falling back to summing
    every session in monitor.db, which would silently mix in whichever
    other employee last used this machine."""
    if employee_id is None:
        return 0, 0

    today = datetime.now().strftime("%Y-%m-%d")
    active_total = 0
    idle_total = 0
    for session in get_all_sessions(employee_id=employee_id):
        if not (session.get("start_time") or "").startswith(today):
            continue
        if session["id"] == current_session_id:
            live = calculate_statistics(session["id"])
            active_total += live["active_time"]
            idle_total += live["idle_time"]
        else:
            active_total += session.get("active_time") or 0
            idle_total += session.get("idle_time") or 0
    return active_total, idle_total
