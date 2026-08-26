# LAFRE — Frontend

Next.js 14 (App Router) frontend for LAFRE, covering the **student**, **citizen**, **lawyer**, and **admin** modules.

## Local development

```bash
npm install
npm run dev:local   # http://localhost:3000, expects a backend on http://localhost:8000
# or
npm run dev         # binds 0.0.0.0, useful for testing from a phone on the same network
```

By default the frontend looks for a backend API at:
- `http://localhost:8000/api` when running on `localhost`
- `/api` (same-origin) otherwise, unless overridden (see below)

## Connecting a backend

You have two ways to point the frontend at a backend:

1. **Build-time (recommended for production):** set `NEXT_PUBLIC_API_BASE_URL` in your environment
   (see `.env.example`), e.g. `NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com/api`.
2. **Runtime override (no rebuild needed):** open the app, go to **Student → Settings → Backend
   connection**, and enter a backend URL there. This is handy while you don't have a backend deployed
   yet, or want to point at a staging server temporarily. It's stored in the browser only
   (`localStorage`) and takes priority over the build-time env var.

If the backend can't be reached, the app shows a clear in-app error message (not a blank screen or
raw stack trace) naming the URL it tried, and a "Test connection" button on the Settings page lets you
check reachability directly.

## Deploying to Vercel

1. Push this folder to a GitHub repository.
2. In Vercel, "Add New Project" → import the repo. Vercel auto-detects Next.js — no extra config needed.
3. If you already have a backend, add an environment variable in the Vercel project settings:
   `NEXT_PUBLIC_API_BASE_URL=https://your-backend-host/api`
4. Deploy. If you don't have a backend yet, deploy anyway — the app will show a friendly "can't reach
   backend" message on data-dependent pages, and you can add the URL later via Settings or by adding the
   env var and redeploying.

## Notes

- `next.config.mjs` is the single Next.js config file (a duplicate `next.config.js` previously shipped
  alongside it, which Next.js does not allow — it has been removed).
- `package-lock.json` was regenerated against the public npm registry; the one originally bundled
  referenced an internal/private registry mirror and would fail to install outside that environment.
