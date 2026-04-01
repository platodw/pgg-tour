# CLAUDE.md

PGG Tour: Flask web app and data backend for the PGG Tour garage golf simulator league. Tracks scores, leaderboards, player rosters, event schedules, awards, and a hole-in-one pot.

## Tech Stack

- Python 3.11, Flask 2.3, Jinja2 templates
- SQLite locally, PostgreSQL (via psycopg2) in production
- BeautifulSoup + lxml for course list scraping
- Gunicorn for production serving
- Deployed on Heroku (Procfile + runtime.txt)
- PWA support (manifest.json, service worker in static/)

## Running Locally

```
pip install -r requirements.txt
python app.py
```

Runs on port 5000 by default. Uses SQLite (`golf_scores.db`) when `DATABASE_URL` is not set.

## Environment Variables

- `DATABASE_URL`: Postgres connection string (Heroku sets this automatically). When absent, falls back to local SQLite.
- `PORT`: Server port (default 5000).
- `FLASK_ENV`: Set to `development` for debug mode.

Note: `app.secret_key` and `ADMIN_PASSWORD` are hardcoded in `app.py`. Admin password is `pgg2024`.

## Project Structure

```
app.py              Main Flask app (~1600 lines). All routes, all logic.
db_helper.py        Database abstraction layer. PostgresCursor and PostgresConnection
                    wrappers translate SQLite syntax (? placeholders, GROUP_CONCAT,
                    date('now')) to Postgres equivalents automatically.
templates/          Jinja2 templates (base.html layout, page templates)
static/             Logo, favicon, PWA manifest, service worker, course_list.json, icons/
players.txt         Seed list of player names (migrated into DB on setup)
```

Setup/migration scripts (run once, not part of the running app):
- `db_setup.py`, `setup_awards_table.py`, `setup_schedule_tables.py`, `setup_hole_in_one_tables.py`: Create tables
- `migrate_to_postgres.py`, `migrate_all_data.py`, `import_sql_to_postgres.py`: SQLite-to-Postgres migration
- `check_*.py`, `debug_*.py`: Diagnostic/inspection scripts

## Database Tables

- `scores`: Per-hole scores (9 holes), date, course, nine (front/back), player_name, mulligan, winner
- `players`: Name, email, phone, active status
- `events` + `event_participants`: Scheduled matches with RSVP tracking
- `awards`: Season awards by category and player
- `hole_in_one_pot`: Per-player balance tracking ($1/round contribution)
- `hole_in_one_history`: Recorded hole-in-ones with course/hole/pot amount
- `pot_contributions`: Individual contribution records

## Key Routes

Public: `/` (landing), `/clubhouse-entry` (password gate)

Behind auth (`require_auth` decorator, session-based):
- `/home`: Dashboard with recent matches and ticker
- `/scorecard`: Live score entry with undo support
- `/leaderboard`: Season standings
- `/stats`: Player statistics, score import
- `/schedule`: Event calendar, create events
- `/roster`: Player management (add/edit/delete)
- `/awards`: Season awards CRUD
- `/hole-in-one`: Pot tracker, record aces, upload balances

API endpoints: `/api/live-match-status`, `/api/update-live-scorecard`, `/api/debug-session`

## Conventions and Patterns

- Single-file architecture: everything lives in `app.py`. No blueprints, no separate route modules.
- The `db_helper.py` abstraction means all SQL in `app.py` is written in SQLite dialect. The wrapper handles Postgres translation at runtime. When writing new queries, use `?` placeholders and SQLite function names.
- Season boundaries are November 1 through October 31 (the `get_season_label` function). A round played in November 2024 belongs to the "2025 Season."
- Auth is a simple session flag set after entering the admin password at `/clubhouse-entry`. No user accounts.
- Templates were originally edited with Pinegrow (templates/pinegrow.json, _pgbackup, _pginfo directories are artifacts of that).
- Course list is a static JSON file at `static/course_list.json`, scraped via `scrape_courses.py`.

## Known Quirks

- The `db_helper.py` Postgres wrapper only adds `RETURNING id` to simple single-line INSERTs (3 lines or fewer). Complex INSERT...SELECT statements won't get auto-RETURNING.
- `scores.db` is in the repo but empty (0 bytes). The actual dev DB file is `golf_scores.db` (gitignored).
- Twilio SMS integration was removed; references remain as comments. Manual texting is preferred.
- The `app.secret_key` is not pulled from an env var. It's a static string in source.
- Many one-off migration/debug scripts in the root. They're historical artifacts, not part of the running application.
