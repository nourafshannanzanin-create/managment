# Wallet Module

## Goal

Provide reusable wallet, ledger and feature-purchase patterns with safe money handling.

## Folder Structure

- `wallet/frontend/wallet.service.js`
- `wallet/backend/license.py`
- `wallet/backend/wallet_options.py`

## Core Backend Models

- `Wallet`
- `CashflowTransaction`
- `WalletGatewayRequest`
- `CarWashFeaturePurchase`

## Endpoints

- `/payments/wallet/dashboard/`
- `/payments/wallet/options/`
- `/payments/wallet/deposit/`
- `/payments/wallet/deposit/start/`
- `/payments/wallet/withdraw/`

## Financial Rules

- use `Decimal`
- wrap balance changes in DB transactions
- use `select_for_update()` on mutable balances
- write a ledger row for every balance change
- keep gateway callback idempotent

## Feature Purchase Logic

- feature option catalog is config-driven
- initial purchase can be `cash` or `installment`
- backend computes lock status, not frontend

## Error States

- insufficient balance
- invalid wallet type
- duplicate active feature
- installment already settled

## Testing

- deposit success
- withdraw insufficient balance
- duplicate gateway callback
- installment payment success
- software lock calculation
