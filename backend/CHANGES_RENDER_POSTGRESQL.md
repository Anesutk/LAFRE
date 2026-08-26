# Changes made for Render + PostgreSQL

## Preserved

- Student module chat, streaming endpoint, documents, flashcards, chat history, access request, and prompts endpoints.
- Citizen matter/lending/document workflow endpoints.
- Admin user approvals, dashboard, lawyers, templates, reviews, knowledge-base admin endpoints.
- Lawyer dashboard/review endpoints.
- Existing database models and migrations.

## Changed/fixed

- Switched default database configuration from SQLite to PostgreSQL.
- Added `DATABASE_URL` support for Render PostgreSQL and local PostgreSQL.
- Kept `LAFRE_ALLOW_SQLITE=1` only as an emergency/offline test switch.
- Added Render deployment scripts: `build.sh`, `start.sh`, `render.yaml`, `runtime.txt`.
- Added production-safe Render host handling with `RENDER_EXTERNAL_HOSTNAME` and `.onrender.com` support.
- Added CORS/CSRF environment support for the deployed frontend.
- Added `/`, `/health/`, `/api/`, and `/api/health/` health/API root endpoints.
- Made Bedrock/Knowledge Base IDs environment-first instead of hardcoded.
- Added `BEDROCK_FAST_MODEL_ID` and `BEDROCK_SMART_MODEL_ID` environment variables for your model choices.
- Added `RENDER_DISK_PATH`/`MEDIA_ROOT` support for persistent media if you attach a Render Disk.
- Updated `.env.example`, README, and PostgreSQL migration guide.
- Added `.gitignore` so `.env`, virtualenvs, SQLite files, static collection output, media, and caches are not committed.

## Validation performed

- Python compile check passed.
- `python manage.py check` passed.
- `makemigrations --check --dry-run` found no missing model migrations.
- `collectstatic --noinput` completed.
- Fresh migration run completed in emergency SQLite validation mode.
- Health/API root endpoints returned 200.
- Admin creation/login, student registration/approval/login, and student ask endpoint smoke-tested.
