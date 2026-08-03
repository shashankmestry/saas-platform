# API Reference

Base URL (local development): `http://localhost:8000`

Interactive docs:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Authentication uses Supabase JWTs. Protected endpoints require:

```http
Authorization: Bearer <supabase_access_token>
```

---

## Endpoints

### `GET /`

Root service information.

**Auth:** none

**Response `200`**

```json
{
  "name": "SaaS Platform API",
  "version": "0.1.0",
  "status": "running"
}
```

---

### `GET /api/v1/health`

Health check.

**Auth:** none

**Response `200`**

```json
{
  "status": "healthy"
}
```

---

### `GET /api/v1/auth/me`

Returns the current platform user.

On first authenticated request, the backend provisions a platform user from the
verified Supabase JWT (JIT). Later requests return the existing user.

**Auth:** required (`Bearer` token)

**Response `200`**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "auth_user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "user@example.com",
  "display_name": null,
  "avatar_url": null,
  "is_active": true,
  "created_at": "2026-07-31T10:00:00Z",
  "updated_at": "2026-07-31T10:00:00Z"
}
```

**Errors**

| Status | When |
| ------ | ---- |
| `401` | Missing, invalid, or expired token |
| `403` | Platform user exists but is inactive |

**Example**

```bash
curl -s \
  -H "Authorization: Bearer <supabase_access_token>" \
  http://localhost:8000/api/v1/auth/me
```

---

## Notes

- API versioning is under `/api/v1`.
- Supabase remains the authentication provider; the application owns platform user records.
- There are currently no public user-management, organization, or RBAC endpoints.

## Frontend auth pages

| Path | Description |
| ---- | ----------- |
| `/` | Landing page with Create Account / Sign In |
| `/auth/register` | Supabase registration (sends verification email) |
| `/auth/callback` | Email verification return; exchanges session and calls `/api/v1/auth/me` |
| `/auth/login` | Supabase login, then `GET /api/v1/auth/me` |
| `/dashboard` | Temporary authenticated dashboard |
