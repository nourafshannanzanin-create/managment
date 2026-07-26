from django.urls import include, path

urlpatterns = [
    path('api/workers/', include('apps.workers.urls')),
]

# Public worker page API:
# GET/POST /api/workers/attendance/public/<token>/
#
# Admin/manager APIs:
# GET  /api/workers/attendance/dashboard/
# POST /api/workers/attendance/events/
# POST /api/workers/<worker_id>/attendance-token/refresh/
