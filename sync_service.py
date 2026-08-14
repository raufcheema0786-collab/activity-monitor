import os
from dataclasses import dataclass
from typing import Optional

import requests

from auth_storage import get_active_employee_id, load_token
from backend_config import BACKEND_URL
from repositories.pending_upload_repository import queue_upload
from sync_health import mark_sync_auth_failed, clear_sync_auth_failed


@dataclass
class SyncResult:
    success: bool
    # True if the failure is transient (network error, timeout, 5xx) and
    # worth retrying later. False if the server rejected the request
    # (4xx) and retrying it unchanged would just fail again.
    retryable: bool
    status_code: Optional[int] = None
    data: Optional[dict] = None
    error: Optional[str] = None


def get_auth_headers():
    token_data = load_token()
    if not token_data:
        return None
    return {"Authorization": f"Bearer {token_data['access_token']}"}


def _request(method, path, json_payload=None, form_data=None, files=None, timeout=5):
    headers = get_auth_headers()
    if not headers:
        mark_sync_auth_failed()
        return SyncResult(success=False, retryable=False, error="not authenticated")

    try:
        if files is not None:
            response = requests.request(
                method, f"{BACKEND_URL}{path}", data=form_data, files=files, headers=headers, timeout=timeout
            )
        else:
            response = requests.request(
                method, f"{BACKEND_URL}{path}", json=json_payload, headers=headers, timeout=timeout
            )
    except requests.exceptions.RequestException as e:
        return SyncResult(success=False, retryable=True, error=str(e))

    if response.status_code >= 500:
        return SyncResult(
            success=False, retryable=True, status_code=response.status_code,
            error=f"HTTP {response.status_code}: {response.text[:300]}",
        )
    if response.status_code == 401:
        # The stored token is invalid (expired, or the employee record it
        # points at no longer exists). Retrying with the same token will
        # never succeed, and every sync call from here on will silently
        # fail the same way until the app is re-activated -- surface that
        # instead of letting local and server data quietly drift apart.
        mark_sync_auth_failed()
        return SyncResult(
            success=False, retryable=False, status_code=response.status_code,
            error=f"HTTP {response.status_code}: {response.text[:300]}",
        )
    if 400 <= response.status_code < 500:
        return SyncResult(
            success=False, retryable=False, status_code=response.status_code,
            error=f"HTTP {response.status_code}: {response.text[:300]}",
        )

    clear_sync_auth_failed()
    try:
        data = response.json()
    except ValueError:
        data = None
    return SyncResult(success=True, retryable=False, status_code=response.status_code, data=data)


# --- Raw attempt functions -------------------------------------------------
# These make exactly one HTTP call and never touch the queue. They're used
# both by the "live" send_* functions below (which queue on retryable
# failure) and by retry_service (which re-attempts already-queued items and
# must not re-queue them as new rows).

def _attempt_heartbeat(payload, timeout=5):
    return _request("POST", "/heartbeat", json_payload=payload, timeout=timeout)


def _attempt_session_start(payload, timeout=5):
    return _request("POST", "/sessions", json_payload=payload, timeout=timeout)


def _attempt_session_end(payload, timeout=5):
    return _request("POST", "/sessions/end", json_payload=payload, timeout=timeout)


def _attempt_event(payload, timeout=5):
    return _request("POST", "/event", json_payload=payload, timeout=timeout)


def _attempt_screenshot(payload, timeout=5):
    image_path = payload.get("image_path")
    if not image_path or not os.path.exists(image_path):
        return SyncResult(success=False, retryable=False, error=f"local screenshot file missing: {image_path}")

    form_data = {"session_id": str(payload["session_id"]), "created_at": payload["created_at"]}
    if payload.get("client_event_id"):
        form_data["client_event_id"] = payload["client_event_id"]

    with open(image_path, "rb") as f:
        files = {"file": (os.path.basename(image_path), f, "image/png")}
        return _request("POST", "/screenshots", form_data=form_data, files=files, timeout=timeout)


# Keyed by the same upload_type string stored in pending_uploads.upload_type.
ATTEMPT_HANDLERS = {
    "heartbeat": _attempt_heartbeat,
    "session_start": _attempt_session_start,
    "session_end": _attempt_session_end,
    "event": _attempt_event,
    "screenshot": _attempt_screenshot,
}


def _queue_if_retryable(upload_type, payload, result, client_ref):
    if result.success:
        return
    if result.retryable:
        queue_upload(upload_type, payload, client_ref=client_ref, employee_id=get_active_employee_id())
        print(f"[sync] queued {upload_type} (client_ref={client_ref}) for retry: {result.error}")
    else:
        print(f"[sync] dropped {upload_type} (client_ref={client_ref}), not retryable: {result.error}")


# --- Public API used by the live monitoring code ----------------------------

def send_heartbeat(client_ref, timeout=5):
    payload = {"client_event_id": client_ref}
    result = _attempt_heartbeat(payload, timeout)
    _queue_if_retryable("heartbeat", payload, result, client_ref)
    return result.success


def get_settings():
    result = _request("GET", "/settings/employee", timeout=5)
    if result.success:
        print(f"Fetched monitoring settings from backend: {result.data}")
        return result.data
    print(f"Warning: failed to fetch settings from backend ({result.error}); using defaults")
    return None


def start_remote_session(client_ref, timeout=5):
    payload = {"client_event_id": client_ref}
    result = _attempt_session_start(payload, timeout)
    _queue_if_retryable("session_start", payload, result, client_ref)
    if result.success and result.data:
        return result.data.get("id")
    return None


def end_remote_session(remote_session_id, client_ref, timeout=5):
    payload = {"session_id": remote_session_id, "client_ref": client_ref}
    result = _attempt_session_end(payload, timeout)
    _queue_if_retryable("session_end", payload, result, client_ref)
    return result.success


def send_event(session_id, session_client_ref, event_type, timestamp, metadata=None, client_ref=None, timeout=5):
    payload = {
        "session_id": session_id,
        "session_client_ref": session_client_ref,
        "type": event_type,
        "timestamp": timestamp,
        "metadata": metadata,
        "client_event_id": client_ref,
    }
    result = _attempt_event(payload, timeout)
    _queue_if_retryable("event", payload, result, client_ref)
    return result.success


def send_screenshot(session_id, session_client_ref, image_path, created_at, client_ref=None, timeout=5):
    payload = {
        "session_id": session_id,
        "image_path": image_path,
        "created_at": created_at,
        "client_event_id": client_ref,
    }
    result = _attempt_screenshot(payload, timeout)
    _queue_if_retryable("screenshot", payload, result, client_ref)
    return result.success
