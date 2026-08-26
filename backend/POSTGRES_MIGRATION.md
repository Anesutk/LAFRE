# PostgreSQL migration checklist

## What changed

The backend now defaults to PostgreSQL. SQLite is disabled unless you explicitly set:

```env
LAFRE_ALLOW_SQLITE=1
```

Do not use that setting on Render.

## Local PostgreSQL

1. Install PostgreSQL.
2. Create a database and user, for example:

```sql
CREATE DATABASE lafre_dev;
CREATE USER lafre WITH PASSWORD 'lafre_password';
GRANT ALL PRIVILEGES ON DATABASE lafre_dev TO lafre;
```

3. In `backend/.env` set:

```env
DATABASE_URL=postgres://lafre:lafre_password@127.0.0.1:5432/lafre_dev
```

4. Run:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check
```

## Render PostgreSQL

1. Create a Render PostgreSQL database in the same region as the backend.
2. Copy the **Internal Database URL**.
3. Set it as `DATABASE_URL` on the backend web service.
4. Set `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `FRONTEND_BASE_URL`, `CORS_ALLOWED_ORIGINS`, and `DJANGO_CSRF_TRUSTED_ORIGINS`.
5. Build command: `./build.sh`.
6. Start command: `./start.sh`.
7. Health path: `/health/`.

`build.sh` installs requirements, collects static files, and runs migrations automatically.
