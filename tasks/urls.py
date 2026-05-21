from django.urls import path
from . import views

app_name = "tasks"

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.worker_create, name="register"),

    # Tasks
    path("tasks/", views.task_list, name="task_list"),
    path("tasks/create/", views.task_create, name="task_create"),
    path("tasks/<int:pk>/", views.task_detail, name="task_detail"),
    path("tasks/<int:pk>/update/", views.task_update, name="task_update"),
    path("tasks/<int:pk>/delete/", views.task_delete, name="task_delete"),
    path("tasks/<int:pk>/toggle/", views.task_toggle_complete, name="task_toggle"),

    # Workers
    path("workers/", views.worker_list, name="worker_list"),
    path("workers/<int:pk>/", views.worker_detail, name="worker_detail"),
    path("workers/<int:pk>/update/", views.worker_update, name="worker_update"),
    path("workers/<int:pk>/delete/", views.worker_delete, name="worker_delete"),

    # Tags
    path("tags/", views.tag_list, name="tag_list"),
    path("tags/create/", views.tag_create, name="tag_create"),
    path("tags/<int:pk>/update/", views.tag_update, name="tag_update"),
    path("tags/<int:pk>/delete/", views.tag_delete, name="tag_delete"),

    # Task Types
    path("task-types/", views.task_type_list, name="task_type_list"),
    path("task-types/create/", views.task_type_create, name="task_type_create"),
    path("task-types/<int:pk>/update/", views.task_type_update, name="task_type_update"),
    path("task-types/<int:pk>/delete/", views.task_type_delete, name="task_type_delete"),

    # Positions
    path("positions/", views.position_list, name="position_list"),
    path("positions/create/", views.position_create, name="position_create"),
    path("positions/<int:pk>/update/", views.position_update, name="position_update"),
    path("positions/<int:pk>/delete/", views.position_delete, name="position_delete"),
]
