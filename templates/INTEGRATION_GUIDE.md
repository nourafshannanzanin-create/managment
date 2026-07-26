# Integration Guide

## 1. Copy folders

- Copy `templates/common/frontend` into your frontend shared layer.
- Copy the module folder you need:
  - `templates/vrood-khorooj`
  - `templates/wallet`
  - `templates/support`
  - `templates/sms`
- Copy `templates/common/backend` and module backend files into your Django app/service layer.

## 2. Install packages

- Frontend:
  - `axios`
  - `pinia`
  - `vue-router`
- Backend:
  - `Django`
  - `djangorestframework`

## 3. Define environment values

- Frontend:
  - `VITE_API_BASE_URL`
- Backend:
  - `SMS_PROVIDER_BASE_URL`
  - `SMS_PROVIDER_API_KEY`
  - `SMS_PROVIDER_LINE_NUMBER`
  - `SMS_PRICE_PER_SEGMENT`

## 4. Create project config

- Start from:
  - `templates/config/project.config.example.js`
  - `templates/config/routes.config.example.js`
  - `templates/config/env.example`

## 5. Register frontend routes

- Create auth routes from `templates/vrood-khorooj/frontend/router.guard.js`.
- Keep public session routes open.
- Gate protected routes with role and feature checks.

## 6. Register stores

- Register the extracted auth store before router navigation.
- Use the normalized `authState` shape exposed by the auth template.

## 7. Configure API base URL

- Use `templates/common/frontend/apiClient.js`.
- If you run frontend dev server behind backend proxy, keep `/api` as dev base.

## 8. Install backend apps/services

- Mount the extracted backend helpers inside existing apps if you already have auth/payments/notifications domains.
- Do not create duplicate models if your target project already has equivalents.

## 9. Run migrations carefully

- Only create migrations for models you truly import.
- If target project already has wallet/ticket/template tables, map to existing tables instead of duplicating.

## 10. Register endpoints

- Bind extracted services to your existing DRF views or routers.
- Keep endpoint shapes consistent with `API_CONTRACT.md`.

## 11. Connect permissions

- Use role list + feature map + software lock together.
- Never trust frontend-only restrictions for financial actions.

## 12. Control menus by subscription/feature

- Build menus from auth payload fields:
  - `role`
  - `menu_access`
  - `license_status`

## 13. Customize branding

- Change:
  - project name
  - logo paths
  - primary/secondary colors
  - login text
  - support copy

## 14. Swap SMS provider

- Implement the same provider interface from `templates/sms/backend/sms_provider.py`.
- Keep campaign logic provider-agnostic.

## 15. Swap payment gateway

- Replace only the gateway adapter/callback implementation.
- Do not change wallet ledger rules.

## 16. Final verification

- Run:
  - auth login/logout/session restore tests
  - wallet balance and duplicate-callback tests
  - support ticket create/reply tests
  - SMS provider failure and logging tests
