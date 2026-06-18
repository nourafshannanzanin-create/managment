from fastapi import APIRouter

from app.api.routes import approvals, auth, bootstrap, expenses, health, reports, requests, settings, users

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(bootstrap.router, prefix="/bootstrap", tags=["bootstrap"])
api_router.include_router(requests.router, prefix="/requests", tags=["requests"])
api_router.include_router(expenses.router, prefix="/expenses", tags=["expenses"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
