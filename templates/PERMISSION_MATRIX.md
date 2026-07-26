# Permission Matrix

| Module | Accountant | Admin | Manager | Owner | Operator | Worker | HQ Support | HQ Admin |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Login/Logout | Y | Y | Y | Y | Y | Y | Y | Y |
| Session Restore | Y | Y | Y | Y | Y | Y | Y | Y |
| Wallet Dashboard | Y | Y | Y | N | N | N | N | N |
| Wallet Deposit/Withdraw | Y | Y | Y | N | N | N | N | N |
| Feature Purchase | N | Y | Y | N | N | N | N | N |
| Support Tickets | Y | Y | Y | Y | Y | Y | Y | Y |
| Support Assignment | N | N | N | N | N | N | Y | Y |
| SMS Dashboard | N | Y | Y | N | N | N | N | N |
| SMS Send | N | Y | Y | N | N | N | N | N |
| SMS Templates | N | Y | Y | N | N | N | N | N |
| Attendance Upgrade Override | N | N | N | N | N | N | N | Y |

## Notes

- Frontend route access is advisory.
- Backend must validate every financial and support-management action.
- Software lock must override most tenant routes except safe payment/support routes.
