# Administration-01 — User & Institution Administration

## Scope
NCCT administrator workspace for platform user lifecycle, role assignment, institution assignment, account activation/deactivation, and institution creation/register.

## Access
Administration actions require `NCCT_ADMIN`.

## APIs
- `GET /api/v1/users`
- `PATCH /api/v1/users/{user_id}`
- existing `GET /api/v1/institutions`
- existing `POST /api/v1/institutions`

## Safety
- An administrator cannot deactivate their own account.
- Roles are limited to the platform's existing five roles.
- Users cannot be assigned to inactive or missing institutions.
- No password data is exposed by the admin API.

## Migration
None. Uses the existing `users` and `institutions` tables.


### Fix: unassign institution
The user directory now supports explicitly clearing a user's institution assignment by selecting **Unassigned**. The frontend sends `null`, and the backend distinguishes an explicit null from an omitted field.
