# Calendar Read API v1

Read-only FastAPI service for Google Calendar. Returns normalized JSON for events, free/busy blocks, and daily snapshots (with conflict/gap detection).

## Prerequisites

- Python 3.11+
- A Google Cloud project with the Calendar API enabled
- An OAuth 2.0 Client ID (type: Web application)

## Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or select an existing one).
3. Enable the **Google Calendar API** under APIs & Services > Library.
4. Go to APIs & Services > Credentials and create an **OAuth 2.0 Client ID** (Application type: Web application).
5. Add the following **Authorized redirect URIs**:
   - Local development: `http://localhost:8000/auth/callback`
   - Deployed: `${BASE_URL}/auth/callback`
6. Download the client secret JSON and save it (e.g. `client_secret.json`).

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and fill in values:

```bash
cp .env.example .env
```

At minimum, set:

```
GOOGLE_OAUTH_CLIENT_SECRET_PATH=./client_secret.json
```

## Running

```bash
cd calendar_read_api
uvicorn app.main:app --reload
```

The server starts at `http://localhost:8000`.

## Authorization

1. Visit `http://localhost:8000/auth/start` in a browser.
2. Sign in with your Google account and grant calendar read permissions.
3. You will be redirected back to `/auth/callback` and see a success message.
4. Check status: `GET /auth/status`

## API Endpoints

### Auth

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/start` | Redirects to Google OAuth consent |
| GET | `/auth/callback` | Handles OAuth callback |
| GET | `/auth/status` | Returns authorization status |
| POST | `/auth/revoke` | Clears stored tokens |

### Calendar (v1)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/calendars` | List accessible calendars |
| GET | `/v1/events` | Get events in a time window |
| POST | `/v1/freebusy` | Get free/busy blocks |
| GET | `/v1/snapshot` | Get compact day summary with conflicts and gaps |

### Time Window Parameters

All calendar endpoints accept either:

- **Preset**: `preset=today`, `preset=next_7_days`, etc.
- **Explicit**: `time_min=2025-01-15T00:00:00-07:00&time_max=2025-01-16T00:00:00-07:00`

Available presets: `today`, `tomorrow`, `next_7_days`, `next_14_days`, `this_week`, `next_week`, `morning_brief_today`

## Example Requests

### Get today's events

```bash
curl "http://localhost:8000/v1/events?preset=today"
```

### Get events with explicit time range

```bash
curl "http://localhost:8000/v1/events?time_min=2025-01-15T00:00:00-07:00&time_max=2025-01-16T00:00:00-07:00"
```

### Get daily snapshot

```bash
curl "http://localhost:8000/v1/snapshot?preset=morning_brief_today&workday_start=08:00&workday_end=18:00"
```

### Get free/busy

```bash
curl -X POST "http://localhost:8000/v1/freebusy" \
  -H "Content-Type: application/json" \
  -d '{"preset": "today", "calendar_ids": ["primary"]}'
```

## Redaction

By default, events with `visibility: "private"` have their summary replaced with `"Busy"` and location cleared. Pass `redact_private=false` to disable.

Attendee emails are never returned — only `attendees_count`.

## Token Storage

In development, tokens are stored in a local JSON file (`./token.json` by default). Set `TOKEN_STORE_TYPE` and `TOKEN_STORE_PATH` in your `.env` to customize.

## Range Guardrails

The API enforces lookback/lookahead limits (default 30 days each). If `ALLOW_CLAMPING=false` (the default), out-of-range requests return HTTP 400. If `ALLOW_CLAMPING=true`, the range is silently clamped and the response includes `clamped: true` with a `clamp_reason`.

## Tests

```bash
cd calendar_read_api
pytest tests/ -v
```

All tests use mocks — no Google API calls are made.
