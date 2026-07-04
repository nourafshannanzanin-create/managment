from django.urls import path

from workflow import views

urlpatterns = [
    path("health", views.health_view),
    path("auth/login", views.login_view),
    path("auth/me", views.me_view),
    path("bootstrap", views.bootstrap_view),
    path("requests", views.requests_view),
    path("requests/<str:request_code>", views.request_detail_view),
    path("requests/<str:request_code>/approve", views.request_approve_view),
    path("requests/<str:request_code>/reject", views.request_reject_view),
    path("expenses", views.expenses_view),
    path("expenses/summary", views.expenses_summary_view),
    path("expenses/<str:expense_code>", views.expense_detail_view),
    path("expenses/<str:expense_code>/approve", views.expense_approve_view),
    path("expenses/<str:expense_code>/reject", views.expense_reject_view),
    path("users", views.users_view),
    path("reports", views.reports_view),
    path("reports/<str:report_key>/export", views.report_export_view),
    path("approvals", views.approvals_view),
    path("approvals/metrics", views.approvals_metrics_view),
    path("approvals/signature", views.approvals_signature_view),
    path("approvals/documents", views.documents_create_view),
    path("approvals/<str:document_code>", views.approval_detail_view),
    path("approvals/<str:document_code>/download", views.approval_download_view),
    path("approvals/<str:document_code>/approve", views.approval_approve_view),
    path("approvals/<str:document_code>/reject", views.approval_reject_view),
    path("settings", views.settings_view),
    path("settings/profile", views.settings_profile_view),
]
