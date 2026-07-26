# Auth Module

## Goal

Session-based login, session restore, route guarding and feature-aware access payloads.

## Folder Structure

- `vrood-khorooj/frontend/auth.store.js`
- `vrood-khorooj/frontend/router.guard.js`
- `vrood-khorooj/backend/auth_payload.py`

## Pages

- Login page and tenant onboarding can keep project-specific UI.
- Template extraction focuses on logic, not the exact current visuals.

## Stores

- Auth store keeps normalized `user`
- Derived state:
  - `role`
  - `isHq`
  - `menuAccess`
  - `licenseStatus`

## Services

- CSRF bootstrap
- login/logout
- `me` session restore

## Backend Models Used

- `User`
- `CarWash`
- `CarWashFeaturePurchase`

## Endpoints

- `/auth/csrf/`
- `/auth/login/`
- `/auth/logout/`
- `/auth/me/`

## Validations

- login by username or phone
- inactive user rejection
- pending tenant registration rejection

## Route/Permission Rules

- redirect HQ users away from tenant app
- redirect locked tenants to wallet-safe routes
- use backend-provided `menu_access`

## User Flow

1. frontend requests CSRF
2. frontend posts credentials
3. backend returns normalized auth payload
4. store saves user
5. router sends user to role home

## Edge Cases

- expired/no session
- role mismatch
- software lock
- feature disabled

## Testing

- login success
- login invalid password
- fetch session success
- fetch session unauthenticated
- logout clears session
