from django.urls import path

from tasks.views import (
    IndexView,
    LoginView,
    LogoutView,
    PositionCreateView,
    PositionDeleteView,
    PositionListView,
    PositionUpdateView,
    TagCreateView,
    TagDeleteView,
    TagListView,
    TagUpdateView,
    TaskCreateView,
    TaskDeleteView,
    TaskDetailView,
    TaskListView,
    TaskToggleCompleteView,
    TaskTypeCreateView,
    TaskTypeDeleteView,
    TaskTypeListView,
    TaskTypeUpdateView,
    TaskUpdateView,
    WorkerCreateView,
    WorkerDeleteView,
    WorkerDetailView,
    WorkerListView,
    WorkerUpdateView,
)

app_name = "tasks"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("register/", WorkerCreateView.as_view(), name="register"),

    # Tasks
    path("tasks/", TaskListView.as_view(), name="task_list"),
    path("tasks/create/", TaskCreateView.as_view(), name="task_create"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="task_detail"),
    path("tasks/<int:pk>/update/", TaskUpdateView.as_view(), name="task_update"),
    path("tasks/<int:pk>/delete/", TaskDeleteView.as_view(), name="task_delete"),
    path("tasks/<int:pk>/toggle/", TaskToggleCompleteView.as_view(), name="task_toggle"),

    # Workers
    path("workers/", WorkerListView.as_view(), name="worker_list"),
    path("workers/<int:pk>/", WorkerDetailView.as_view(), name="worker_detail"),
    path("workers/<int:pk>/update/", WorkerUpdateView.as_view(), name="worker_update"),
    path("workers/<int:pk>/delete/", WorkerDeleteView.as_view(), name="worker_delete"),

    # Tags
    path("tags/", TagListView.as_view(), name="tag_list"),
    path("tags/create/", TagCreateView.as_view(), name="tag_create"),
    path("tags/<int:pk>/update/", TagUpdateView.as_view(), name="tag_update"),
    path("tags/<int:pk>/delete/", TagDeleteView.as_view(), name="tag_delete"),

    # Task Types
    path("task-types/", TaskTypeListView.as_view(), name="task_type_list"),
    path("task-types/create/", TaskTypeCreateView.as_view(), name="task_type_create"),
    path("task-types/<int:pk>/update/", TaskTypeUpdateView.as_view(), name="task_type_update"),
    path("task-types/<int:pk>/delete/", TaskTypeDeleteView.as_view(), name="task_type_delete"),

    # Positions
    path("positions/", PositionListView.as_view(), name="position_list"),
    path("positions/create/", PositionCreateView.as_view(), name="position_create"),
    path("positions/<int:pk>/update/", PositionUpdateView.as_view(), name="position_update"),
    path("positions/<int:pk>/delete/", PositionDeleteView.as_view(), name="position_delete"),
]
