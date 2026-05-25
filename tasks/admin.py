from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from tasks.models import Worker, Task, Tag, TaskType, Position


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Worker)
class WorkerAdmin(UserAdmin):
    list_display = ["username", "first_name", "last_name", "email", "position"]
    list_filter = ["position", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (
        ("Position", {"fields": ("position",)}),
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(TaskType)
class TaskTypeAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["name", "priority", "task_type", "is_completed", "deadline", "created_at"]
    list_filter = ["priority", "is_completed", "task_type"]
    search_fields = ["name", "description"]
    filter_horizontal = ["assignees", "tags"]
