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

## Frontend connection

In Vercel/your deployed frontend, set:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-render-service.onrender.com/api
```

The frontend can also use its Settings page runtime override, but production should use the env var.

## Important media note

PostgreSQL stores records and extracted text, but uploaded files live in `MEDIA_ROOT`. Render web service storage is ephemeral unless you attach a Render Disk or later configure S3. For source/document viewing to survive redeploys, attach a Render Disk and set `RENDER_DISK_PATH`, or move media to S3 later.
