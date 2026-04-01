# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
pip install -r requirements.txt
python app.py
# Apri http://127.0.0.1:5000
```

The server binds exclusively to `127.0.0.1:5000` — never change it to `0.0.0.0`.

## Architecture

This is a local reverse-proxy web app for exploring Dynatrace APIs.

**`app.py`** — Flask backend (single file, ~150 lines):
- Receives requests from the browser on `localhost:5000`
- Stores the Dynatrace API token **only in the Flask server-side session** (`session['token']`); it is never returned to the browser, never logged, never put in a URL
- Proxies all API calls to the real Dynatrace environment, injecting `Authorization: Api-Token {token}` server-side
- `POST /api/connect` validates the URL (must start with `https://`), tests connectivity via `GET /api/v2/metrics?pageSize=1`, then saves `token` + `base_url` to session
- `GET|POST|PUT|DELETE|PATCH /api/proxy` forwards the request; the `path` query param names the Dynatrace API path (e.g. `/api/v2/problems`); all other query params are forwarded to Dynatrace
- Responses are capped at 10 MB (`MAX_RESPONSE_SIZE`); if truncated, `X-Response-Truncated: true` is set
- Werkzeug access logging is suppressed to avoid accidentally capturing token values from request bodies

**`static/index.html`** — Single-file frontend (vanilla JS, no build step):
- CSS Grid layout: sidebar (230px) + main area (request builder + response panel) + history bar
- Connection panel: SaaS mode builds `https://{env-id}.live.dynatrace.com`; Managed mode accepts a full URL. The token input (`type="password"`) is cleared immediately after `POST /api/connect` returns
- Request builder: method selector, path input, dynamic query-param table (`paramRows` array), JSON body editor (shown only for POST/PUT/PATCH)
- Response panel: colour-coded HTTP status badge, response time from `X-Response-Time-Ms` header, inline JSON syntax highlighter (no CDN)
- History: stored in `localStorage` under key `dt_api_v1_history`; max 50 entries; **token is never stored** — only method, path, params, status, timestamp
- `QUICK_ACCESS` array at the top of the script defines the sidebar shortcuts with pre-populated paths and params

## Supported Dynatrace environments

| Type | URL pattern |
|---|---|
| SaaS | `https://{env-id}.live.dynatrace.com` |
| Managed | `https://{domain}/e/{env-id}` |

Both classic APIs (`/api/v1/*`, `/api/v2/*`) and platform APIs (`/platform/*`) are supported — the proxy is path-agnostic.

## Git workflow

Commit after every meaningful code change so the user can roll back to any previous version:

```bash
git add <files modificati>
git commit -m "descrizione breve della modifica"
```

Per tornare a una versione precedente:
```bash
git log --oneline          # lista dei commit
git checkout <hash> -- .   # ripristina tutti i file a quel commit
# oppure per un singolo file:
git checkout <hash> -- static/index.html
```

## Token security invariants

- `session['token']` is write-only from the browser's perspective
- `/api/status` returns only `{connected: bool, base_url: str|null}`
- `app.secret_key = os.urandom(32)` regenerates on every server start, invalidating all sessions
- `BLOCKED_HEADERS` strips `authorization` from browser-sent headers before forwarding, then re-injects the server-side token
