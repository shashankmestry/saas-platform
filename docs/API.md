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

### `GET /api/v1/organizations`

Returns organizations the current authenticated platform user belongs to.

**Auth:** required (`Bearer` token)

**Response `200`**

```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Acme Technologies",
    "slug": "acme-technologies",
    "created_at": "2026-08-03T10:00:00Z",
    "updated_at": "2026-08-03T10:00:00Z",
    "role": "owner",
    "permissions": [
      "invitation.create",
      "invitation.revoke",
      "invitation.view",
      "member.invite",
      "member.remove",
      "member.role.update",
      "member.view",
      "organization.manage",
      "organization.view"
    ]
  }
]
```

**Errors**

| Status | When |
| ------ | ---- |
| `401` | Missing, invalid, or expired token |

---

### `POST /api/v1/organizations`

Creates an organization and an `owner` membership for the current platform user in one transaction. The slug is generated on the backend from the name.

**Auth:** required (`Bearer` token)

**Request**

```json
{
  "name": "Acme Technologies"
}
```

**Response `201`**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Acme Technologies",
  "slug": "acme-technologies",
  "created_at": "2026-08-03T10:00:00Z",
  "updated_at": "2026-08-03T10:00:00Z",
  "role": "owner",
  "permissions": [
    "invitation.create",
    "invitation.revoke",
    "invitation.view",
    "member.invite",
    "member.remove",
    "member.role.update",
    "member.view",
    "organization.manage",
    "organization.view"
  ]
}
```

**Errors**

| Status | When |
| ------ | ---- |
| `401` | Missing, invalid, or expired token |
| `409` | Unable to generate a unique organization slug |
| `422` | Invalid organization name |

**Example**

```bash
curl -s -X POST \
  -H "Authorization: Bearer <supabase_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme Technologies"}' \
  http://localhost:8000/api/v1/organizations
```

---

### `GET /api/v1/organizations/{organization_id}/profile`

Returns a cohesive organization profile combining core organization identity
(`name`, `slug`) with optional extended profile fields. If no
`organization_profiles` row exists yet, profile fields are returned as `null`
without writing to the database (lazy creation).

Requires `organization.view`.

**Auth:** required (`Bearer` token)

**Response `200`**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Acme Technologies",
  "slug": "acme-technologies",
  "website": null,
  "contact_email": null,
  "phone": null,
  "country_code": null,
  "timezone": null,
  "default_currency": null,
  "logo_url": null
}
```

**Errors**

| Status | When |
| ------ | ---- |
| `401` | Missing, invalid, or expired token |
| `403` | Not a member, or missing `organization.view` |

---

### `PATCH /api/v1/organizations/{organization_id}/profile`

Updates organization name and/or extended profile fields in one transaction.
Creates the `organization_profiles` row on first write if it does not exist.
Slug is read-only and cannot be changed through this endpoint.

Requires `organization.manage`.

**Auth:** required (`Bearer` token)

**Request** (all fields optional; at least one required)

```json
{
  "name": "Acme Technologies",
  "website": "https://acme.example",
  "contact_email": "hello@acme.example",
  "phone": "+1 555 0100",
  "country_code": "US",
  "timezone": "America/New_York",
  "default_currency": "USD"
}
```

**Response `200`**

Same shape as `GET .../profile`.

**Errors**

| Status | When |
| ------ | ---- |
| `401` | Missing, invalid, or expired token |
| `403` | Not a member, or missing `organization.manage` |
| `422` | Invalid field values |

---

### `POST /api/v1/organizations/{organization_id}/logo/upload`

Authorizes a short-lived Supabase Storage signed upload for an organization
logo. Does **not** update `logo_path`. The browser uploads directly to Storage
using the returned token.

Requires `organization.manage`.

Supported content types: `image/jpeg`, `image/png`, `image/webp`.
Maximum declared size: 2 MB.

**Auth:** required (`Bearer` token)

**Request**

```json
{
  "content_type": "image/png",
  "file_size": 204800
}
```

**Response `200`**

```json
{
  "bucket": "organization-assets",
  "path": "organizations/3fa85f64-5717-4562-b3fc-2c963f66afa6/logo/a1b2c3d4e5f64789a0b1c2d3e4f50617.png",
  "token": "<signed-upload-token>",
  "signed_url": "https://<project>.supabase.co/storage/v1/object/upload/sign/..."
}
```

**Errors**

| Status | When |
| ------ | ---- |
| `401` | Missing, invalid, or expired token |
| `403` | Missing `organization.manage` |
| `422` | Unsupported type or size |
| `502` | Storage authorization failed |

---

### `POST /api/v1/organizations/{organization_id}/logo/confirm`

Verifies a previously authorized Storage object and sets
`organization_profiles.logo_path`. Replaces an existing logo only after the new
object is verified, then best-effort deletes the old object.

Requires `organization.manage`.

**Auth:** required (`Bearer` token)

**Request**

```json
{
  "path": "organizations/3fa85f64-5717-4562-b3fc-2c963f66afa6/logo/a1b2c3d4e5f64789a0b1c2d3e4f50617.png"
}
```

**Response `200`**

Same shape as `GET .../profile`, including a temporary `logo_url`.

**Errors**

| Status | When |
| ------ | ---- |
| `401` | Missing, invalid, or expired token |
| `403` | Missing `organization.manage` |
| `404` | Storage object missing |
| `422` | Invalid/cross-tenant path or invalid object metadata |
| `502` | Storage verification failed |

---

### `DELETE /api/v1/organizations/{organization_id}/logo`

Clears `logo_path` and best-effort removes the Storage object. Idempotent when
no logo is set.

Requires `organization.manage`.

**Auth:** required (`Bearer` token)

**Response `200`**

Same shape as `GET .../profile` with `logo_url: null`.

**Errors**

| Status | When |
| ------ | ---- |
| `401` | Missing, invalid, or expired token |
| `403` | Missing `organization.manage` |

---

### `GET /api/v1/organizations/{organization_id}/members`

Lists members of an organization. Requires `member.view`.

**Auth:** required (`Bearer` token)

**Response `200`**

```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "display_name": null,
    "email": "owner@example.com",
    "role": "owner",
    "created_at": "2026-08-03T10:00:00Z"
  }
]
```

**Errors**

| Status | When |
| ------ | ---- |
| `401` | Missing, invalid, or expired token |
| `403` | Not a member, or missing `member.view` |

---

### `POST /api/v1/organizations/{organization_id}/invitations`

Creates a pending member invitation. Requires `member.invite`. Invitation role is always `member`.

In `APP_ENV=development`, the response may include `invite_url` with the raw token for local testing. Production responses never include raw tokens or invite URLs.

**Auth:** required (`Bearer` token)

**Request**

```json
{
  "email": "person@example.com"
}
```

**Response `201`**

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "organization_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "email": "person@example.com",
  "role": "member",
  "expires_at": "2026-08-10T10:00:00Z",
  "created_at": "2026-08-03T10:00:00Z",
  "invite_url": "http://localhost:3000/invitations/accept?token=..."
}
```

**Errors**

| Status | When |
| ------ | ---- |
| `401` | Missing, invalid, or expired token |
| `403` | Not a member, or missing `member.invite` |
| `409` | Email already a member, or pending invitation exists |
| `422` | Invalid email |

---

### `PATCH /api/v1/organizations/{organization_id}/members/{membership_id}`

Update a member role. Requires `member.role.update`.

**Request**

```json
{ "role": "owner" }
```

**Errors**

| Status | When |
| ------ | ---- |
| `403` | Missing permission |
| `404` | Membership not in organization |
| `409` | Would leave organization with zero owners |

---

### `DELETE /api/v1/organizations/{organization_id}/members/{membership_id}`

Remove a member. Requires `member.remove`. Returns `204`.

---

### `POST /api/v1/organizations/{organization_id}/leave`

Current user leaves the organization. Requires membership (`organization.view`). Returns `204`. Sole owner cannot leave (`409`).

---

### `POST /api/v1/organizations/{organization_id}/ownership/transfer`

Transfer ownership to another membership. Requires `organization.ownership.transfer`.

**Request**

```json
{ "membership_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6" }
```

Atomically promotes target to owner and demotes requester to member.

---

### `GET /api/v1/organizations/{organization_id}/invitations`

Lists pending invitations for an organization. Requires `invitation.view`. Never returns `token_hash` or raw tokens.

**Auth:** required (`Bearer` token)

---

### `DELETE /api/v1/organizations/{organization_id}/invitations/{invitation_id}`

Revokes a pending invitation by setting `revoked_at`. Requires `invitation.revoke`. Does not hard-delete.

**Auth:** required (`Bearer` token)

**Response `204`**

---

### `POST /api/v1/invitations/accept`

Accepts an invitation for the authenticated platform user. Membership creation and `accepted_at` update are atomic. Invitation email must match the authenticated user's email.

**Auth:** required (`Bearer` token)

**Request**

```json
{
  "token": "<raw invitation token>"
}
```

**Errors**

| Status | When |
| ------ | ---- |
| `401` | Missing, invalid, or expired token |
| `403` | Invitation email does not match authenticated user |
| `404` | Invitation not found |
| `409` | Already accepted, revoked, or already a member |
| `410` | Invitation expired |

---

## Notes

- API versioning is under `/api/v1`.
- Supabase remains the authentication provider; the application owns platform user records.
- Organization list endpoints are tenant-isolated to the caller's memberships.
- Organization list/create responses include the caller's `role` and `permissions` for UI authorization.
- Invitation emails are normalized (trim + lowercase) before storage/comparison.
- Raw invitation tokens are never stored; only SHA-256 `token_hash` is persisted.
- Organization authorization uses code-defined roles/permissions (no RBAC database tables).
- There are currently no organization detail/update/delete or custom-role endpoints.

## Frontend auth pages

| Path | Description |
| ---- | ----------- |
| `/` | Landing page with Create Account / Sign In |
| `/auth/register` | Supabase registration (sends verification email) |
| `/auth/callback` | Email verification return; exchanges session and calls `/api/v1/auth/me` |
| `/auth/login` | Supabase login, then `GET /api/v1/auth/me` |
| `/onboarding` | Create organization when the user has none |
| `/dashboard` | Temporary authenticated dashboard (shows organization name) |
| `/dashboard/members` | Members, pending invitations, and invite form |
| `/invitations/accept` | Accept invitation via token query param |
