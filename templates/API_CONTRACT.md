# API Contract

## Auth

- `GET /auth/csrf/`
- `POST /auth/login/`
- `POST /auth/logout/`
- `GET /auth/me/`
- `POST /auth/tenants/register/`

### `GET /auth/me/` response

```json
{
  "id": 12,
  "username": "manager01",
  "full_name": "Manager Name",
  "role": "manager",
  "platform_role": "",
  "phone": "0912...",
  "tenant_id": 4,
  "tenant_name": "Tenant",
  "purchased_menu_access": ["attendance", "sms_club"],
  "menu_access": {
    "attendance": true,
    "sms_club": true,
    "accounting": false
  },
  "license_status": {
    "is_locked": false,
    "reason": "",
    "notice": ""
  }
}
```

## Wallet

- `GET /payments/wallet/dashboard/`
- `GET /payments/wallet/options/`
- `POST /payments/wallet/deposit/`
- `POST /payments/wallet/deposit/start/`
- `POST /payments/wallet/withdraw/`

### Wallet transaction shape

```json
{
  "id": 10,
  "wallet": 3,
  "wallet_name": "کیف پول اصلی",
  "direction": "out",
  "amount": "500000.00",
  "description": "خرید آپشن",
  "reference_type": "feature_option_purchase",
  "reference_id": 44,
  "transacted_at": "2026-07-13T15:00:00Z"
}
```

## Support

- `GET /auth/support/tickets/`
- `POST /auth/support/tickets/`
- `GET /auth/support/tickets/{id}/`
- `POST /auth/support/tickets/{id}/messages/`
- `POST /auth/support/tickets/{id}/feedback/`

## SMS

- `GET /notifications/customer-club/`
- `GET|POST /notifications/customer-groups/`
- `GET|POST /notifications/sms/templates/`
- `POST /notifications/sms/send/`
- `POST /notifications/sms/simple/`

### SMS campaign request

```json
{
  "template_code": "vip-campaign",
  "template_text": "سلام [نام مشتری]",
  "target_label": "VIP customers",
  "note": "monthly campaign",
  "recipients": [
    {
      "key": "customer:10",
      "name": "Ali",
      "phone": "0912...",
      "carwash_name": "Tenant",
      "orders_count": 6,
      "total_spent": 2400000,
      "score": 4.7
    }
  ]
}
```
