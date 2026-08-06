# Frontend

Next.js App Router foundation for the SaaS platform.

## Run

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

App: `http://localhost:3000`

## Environment

```bash
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=
```

| Variable | Description |
| -------- | ----------- |
| `NEXT_PUBLIC_APP_URL` | Frontend origin used for auth redirect URLs |
| `NEXT_PUBLIC_API_URL` | Backend API base URL |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Supabase publishable key |

## Supabase configuration

Configure these values in the Supabase dashboard before testing auth.

### 1. Project API keys

In **Project Settings → API**:

- Copy **Project URL** → `NEXT_PUBLIC_SUPABASE_URL`
- Copy **Publishable key** (or legacy anon key) → `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`

### 2. URL configuration

In **Authentication → URL Configuration**:

| Setting | Local development value |
| ------- | ----------------------- |
| Site URL | `http://localhost:3000` |
| Redirect URLs | `http://localhost:3000/auth/callback` |

Add the redirect URL exactly as shown. Email verification links must return to
`/auth/callback` so the app can exchange the PKCE code and establish a session.

### 3. Email confirmation

In **Authentication → Providers → Email**:

- Enable **Confirm email** if you want verification before first login
- Keep the default confirmation email template, or ensure the CTA link uses the
  configured redirect URL

### 4. Backend pairing

The backend also needs Supabase values in `backend/.env`:

```bash
DATABASE_URL=postgresql+asyncpg://...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=your-publishable-key
```

`SUPABASE_URL` should match `NEXT_PUBLIC_SUPABASE_URL`.
`SUPABASE_PUBLISHABLE_KEY` should match `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`.

## Structure

```text
frontend/
|-- app/
|   |-- (public)/
|   |-- (auth)/auth/login/
|   |-- (auth)/auth/register/
|   |-- (dashboard)/dashboard/
|   |-- (dashboard)/onboarding/
|   `-- api/
|-- components/
|   |-- ui/
|   |-- layout/
|   |-- common/
|   `-- providers/
|-- lib/
|   |-- api/
|   |-- auth/
|   |-- organizations/
|   |-- supabase/
|   |-- utils/
|   `-- constants/
|-- hooks/
|-- services/
|-- store/
|-- types/
|-- styles/
|-- proxy.ts
|-- package.json
`-- README.md
```

## Auth routes

- `/` — landing page
- `/auth/login` — sign in
- `/auth/register` — create account (email verification required)
- `/auth/callback` — email verification return URL
- `/onboarding` — create organization when the user has none
- `/dashboard` — temporary authenticated dashboard (shows organization name)
- `/dashboard/members` — members, pending invitations, invite form
- `/invitations/accept` — accept invitation via `?token=`

## Session persistence

- Browser client: `lib/supabase/client.ts` (`@supabase/ssr` cookies)
- Server client: `lib/supabase/server.ts`
- Proxy: `proxy.ts` + `lib/supabase/proxy.ts` refreshes/validates the session with
  `getClaims()` and redirects unauthenticated users away from `/dashboard` and
  `/onboarding`
- Axios reads the access token from the current Supabase session on each request

## Email verification

1. User registers at `/auth/register`
2. Supabase stores the PKCE verifier in cookies via `@supabase/ssr`
3. Supabase sends a verification email with redirect to `/auth/callback`
4. The server route exchanges the auth code for a session
5. Backend `GET /api/v1/auth/me` runs JIT provisioning
6. User is redirected to `/dashboard` (then `/onboarding` if they have no organization)

Add this redirect URL in the Supabase dashboard under Authentication → URL configuration:

`http://localhost:3000/auth/callback`

See [Supabase configuration](#supabase-configuration) above for the full setup.
