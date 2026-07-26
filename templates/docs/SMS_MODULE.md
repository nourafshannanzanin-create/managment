# SMS Module

## Goal

Reusable provider-agnostic SMS sending, logging, template rendering and customer targeting.

## Folder Structure

- `sms/backend/sms_provider.py`
- `sms/backend/sms_templates.py`
- `sms/frontend/sms.service.js`

## Provider Rules

- provider implementation must be behind an interface
- business code must not hardcode provider URLs
- provider credentials must come from env/config

## Current Capabilities Mapped

- template rendering
- customer campaign batching by rendered text
- SMS wallet debit
- log persistence
- vehicle event SMS

## Error Cases

- invalid phone
- insufficient SMS wallet balance
- provider error
- empty rendered template

## Testing

- provider success
- provider failure
- invalid recipient
- grouped campaign batching
- log payload creation
