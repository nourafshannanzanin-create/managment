# Support Module

## Goal

Reusable tenant support tickets with threaded replies, attachments and feedback.

## Folder Structure

- `support/frontend/support.service.js`
- `support/backend/ticket_contract.py`

## Endpoints

- `GET/POST /auth/support/tickets/`
- `GET /auth/support/tickets/{id}/`
- `POST /auth/support/tickets/{id}/messages/`
- `POST /auth/support/tickets/{id}/feedback/`

## Backend Shapes

- ticket list item
- ticket detail with messages
- feedback payload
- reply payload

## Frontend States

- loading
- empty
- selected detail
- sending reply
- feedback submitted

## Edge Cases

- closed ticket cannot accept tenant reply
- hidden internal HQ messages must not leak to tenant UI
- missing attachments should degrade safely

## Testing

- create ticket
- reply to open ticket
- reject reply on closed ticket
- submit feedback once
