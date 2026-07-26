# Subscription Module

## Current Reality In This Project

There is no standalone subscription app.

Subscription-like behavior is implemented by:

- `CarWashFeaturePurchase`
- `license_status_for_tenant()` in payments
- route lock behavior in frontend router

## Reusable Strategy

- treat software access as a feature purchase
- expose a normalized `license_status` payload in auth session
- keep frontend lock behavior read-only
- keep due-date and grace logic in backend services

## Required Config

- grace days
- required feature key
- installment interval
- annual renewal rules

## Critical Tests

- no purchase => locked
- active purchase => unlocked
- overdue inside grace => warned not locked
- overdue past grace => locked
