import os

# Every module that talks to the backend imports this instead of hardcoding
# its own copy -- on any machine other than a dev box, the backend isn't
# running on localhost, so this has to be settable per-deployment rather
# than baked into the source. Falls back to localhost so nothing changes
# for local development.
BACKEND_URL = os.environ.get("ACTIVITY_MONITOR_BACKEND_URL", "http://127.0.0.1:8000")
