from datetime import datetime
from repositories.event_repository import get_events_for_session
from repositories.screenshot_repository import get_screenshots_for_session

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
