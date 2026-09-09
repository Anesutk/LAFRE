# LAFRE Backend — Render + PostgreSQL Ready

Django/DRF backend for the separated Student, Citizen, Admin and Lawyer modules.

This version preserves the existing app modules and switches the deployment path to PostgreSQL for Render. SQLite is no longer the default database. Use `LAFRE_ALLOW_SQLITE=1` only for emergency offline tests.

## Local development with PostgreSQL

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
# source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Create a local PostgreSQL database, then edit `.env`:

```env
DATABASE_URL=postgres://lafre:lafre_password@127.0.0.1:5432/lafre_dev
```

Run:

```bash
python manage.py migrate
python manage.py create_lafre_admin --email admin@example.com --password "ChangeMe123!" --name "LAFRE Admin" --staff
python manage.py runserver
```

Test these URLs:

- `http://127.0.0.1:8000/health/`
- `http://127.0.0.1:8000/api/`
- `http://127.0.0.1:8000/api/health/`

## Render deployment

Render values:

- Root Directory: `backend` if your GitHub repository contains a top-level backend folder.
- Build Command: `./build.sh`
- Start Command: `./start.sh`
- Health Check Path: `/health/`

Required Render environment variables:

```env
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=<generate in Render>
DATABASE_URL=<Render Postgres internal database URL>
FRONTEND_BASE_URL=https://your-frontend-domain.com
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-frontend-domain.com
```

AWS/Bedrock/Knowledge Base variables are optional until you connect the real knowledge base:

```env
AWS_REGION=us-east-1
AWS_KB_ID=<your knowledge base id>
AWS_BEDROCK_MODEL_ID=<your model id or ARN>
BEDROCK_FAST_MODEL_ID=<optional fast model>
BEDROCK_SMART_MODEL_ID=<optional detailed model>
AWS_ACCESS_KEY_ID=<Render env var only>
AWS_SECRET_ACCESS_KEY=<Render env var only>
```

After the first deploy, open Render Shell and create/confirm your admin user if needed:

```bash
python manage.py create_lafre_admin --email admin@example.com --password "ChangeMe123!" --name "LAFRE Admin" --staff
```

For real API integration testing, create approved accounts with linked profiles:

```bash
python manage.py create_test_student
python manage.py create_test_citizen
python manage.py create_test_lawyer
```

The default test emails are `test.student@example.test`, `test.citizen@example.test`, and `test.lawyer@example.test`; all use `TestPass!2026`. You can override `--email`, `--name`, or `--password`.

## Frontend connection

## Gmail SMTP email delivery

Set these variables in Render to send lawyer credentials and password-reset emails from `lafrebox@gmail.com`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=1
EMAIL_USE_SSL=0
EMAIL_TIMEOUT=20
EMAIL_HOST_USER=lafrebox@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-google-app-password
DEFAULT_FROM_EMAIL=lafrebox@gmail.com
```

`EMAIL_HOST_PASSWORD` must be a Google App Password. Do not use the normal Gmail password and do not commit the App Password to Git.

## Fictional demo data

To populate a local or staging database with coherent fictional records for testing:

```bash
python manage.py seed_demo_data
```

The command is repeatable and uses `demo.*` accounts and `demo-` slugs. It does not run automatically during deployment. To remove and recreate only these seeded records:

```bash
python manage.py seed_demo_data --reset
```

All seeded accounts use the password `DemoPass!2026`; the records use `example.test` email addresses and are not real people.

In Vercel/your deployed frontend, set:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-render-service.onrender.com/api
```

The frontend can also use its Settings page runtime override, but production should use the env var.

## Important media note

PostgreSQL stores records and extracted text, but uploaded files live in `MEDIA_ROOT`. Render web service storage is ephemeral unless you attach a Render Disk or later configure S3. For source/document viewing to survive redeploys, attach a Render Disk and set `RENDER_DISK_PATH`, or move media to S3 later.
