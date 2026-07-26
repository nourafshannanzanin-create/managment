# Shared Platform Template

This folder contains reusable extracts built from the current CarWash project.

## Structure

- `vrood-khorooj/`
  Auth, session restore, route guard, access payload normalization
- `wallet/`
  Wallet ledger, software lock, feature-option purchase patterns
- `support/`
  Ticket API contract and frontend repository helpers
- `sms/`
  SMS provider interface, template renderer, campaign contracts
- `common/`
  Shared API client and backend config helpers
- `config/`
  Example project-level configuration
- `docs/`
  Module-level documentation and integration notes
- `tests/`
  Example regression tests for sensitive flows

## Design Rules

- Session-based auth, not JWT
- Config-first branding and endpoints
- `Decimal` for money and balances
- backend is the source of truth for financial state
- provider integrations are adapter-based
- no project secret is embedded in this template

## Intended Use

1. Copy only the required module folders into the target project.
2. Replace example config with project-specific values.
3. Register routes, stores and backend URLs using the examples in `INTEGRATION_GUIDE.md`.
4. Keep business rules in backend services; keep frontend orchestration thin.
