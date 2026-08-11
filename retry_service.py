import json
import threading
import time

from auth_storage import get_active_employee_id
from repositories.pending_upload_repository import (
    MAX_RETRY_ATTEMPTS,
    get_pending_uploads,
    mark_upload_failed,
    mark_upload_succeeded,
)
from sync_service import ATTEMPT_HANDLERS

RETRY_INTERVAL_SECONDS = 30

_loop_lock = threading.Lock()
_loop_started = False


def _process_one(upload):
    upload_id = upload["id"]
    upload_type = upload["upload_type"]
    attempt = ATTEMPT_HANDLERS.get(upload_type)

    if attempt is None:
        print(f"[retry] unknown upload_type '{upload_type}' for queued item id={upload_id}; abandoning")
        mark_upload_failed(upload_id, "unknown upload_type", abandon=True)
        return

    payload = json.loads(upload["payload"])
    try:
        result = attempt(payload)
    except Exception as e:
        print(f"[retry] unexpected error retrying {upload_type} id={upload_id}: {e}")
        result = None

    if result is not None and result.success:
        mark_upload_succeeded(upload_id)
        print(f"[retry] {upload_type} id={upload_id} succeeded after {upload['retry_count'] + 1} attempt(s)")
        return

    # A non-retryable (4xx) failure on a retry means the request itself is
    # bad and re-sending it unchanged will never succeed - stop immediately
    # rather than burning through the attempt budget.
    if result is not None and not result.retryable:
        mark_upload_failed(upload_id, result.error, abandon=True)
        print(f"[retry] {upload_type} id={upload_id} ABANDONED - server rejected it permanently: {result.error}")
        return

    new_count = upload["retry_count"] + 1
    error = result.error if result is not None else "unexpected exception during retry"
    if new_count >= MAX_RETRY_ATTEMPTS:
        mark_upload_failed(upload_id, error, abandon=True)
        print(
            f"[retry] {upload_type} id={upload_id} ABANDONED after {new_count} failed attempts "
            f"- needs manual attention: {error}"
        )
    else:
        mark_upload_failed(upload_id, error, abandon=False)
        print(f"[retry] {upload_type} id={upload_id} attempt {new_count}/{MAX_RETRY_ATTEMPTS} failed, will retry later: {error}")


def process_pending_uploads():
    for upload in get_pending_uploads(employee_id=get_active_employee_id()):
        try:
            _process_one(upload)
        except Exception as e:
            # A bug in one item's retry must never stop the rest of the
            # queue (or the loop) from being processed.
            print(f"[retry] failed to process queued upload id={upload.get('id')}: {e}")


def start_retry_loop(interval_seconds=RETRY_INTERVAL_SECONDS):
    global _loop_started
    with _loop_lock:
        if _loop_started:
            return None
        _loop_started = True

    def _loop():
        while True:
            try:
                process_pending_uploads()
            except Exception as e:
                print(f"[retry] retry loop iteration crashed, will try again next tick: {e}")
            time.sleep(interval_seconds)

    thread = threading.Thread(target=_loop, daemon=True, name="sync-retry-loop")
    thread.start()
    print(f"[retry] background retry loop started (every {interval_seconds}s, max {MAX_RETRY_ATTEMPTS} attempts per item)")
    return thread
