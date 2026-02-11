import os
import sys

# Ensure the calendar_read_api package root is on sys.path so that
# `import app.xxx` works from within tests/.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set env vars before any app module is imported
os.environ.setdefault("GOOGLE_OAUTH_CLIENT_SECRET_PATH", "./fake_secret.json")
os.environ.setdefault("BASE_URL", "http://localhost:8000")
os.environ.setdefault("DEFAULT_TIMEZONE", "America/Denver")
