from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone

from .models import Task, Worker, Tag, TaskType, Position
from .forms import (
    TaskForm, WorkerCreationForm, WorkerUpdateForm,
    TagForm, TaskTypeForm, PositionForm, TaskSearchForm, LoginForm
)


def login_view(request):
    if request.user.is_authenticated:
        return redirect("tasks:index")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("tasks:index")
    return render(request, "tasks/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("tasks:login")


@login_required
def index(request):
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(is_completed=True).count()
    pending_tasks = Task.objects.filter(is_completed=False).count()
    overdue_tasks = Task.objects.filter(
        is_completed=False, deadline__lt=timezone.now()
    ).count()
    recent_tasks = Task.objects.select_related("task_type").prefetch_related("assignees", "tags")[:5]
    my_tasks = request.user.assigned_tasks.filter(is_completed=False).select_related("task_type")[:5]
    workers_count = Worker.objects.count()

    context = {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "overdue_tasks": overdue_tasks,
        "recent_tasks": recent_tasks,
        "my_tasks": my_tasks,
        "workers_count": workers_count,
    }
    return render(request, "tasks/index.html", context)


# ── Tasks ──────────────────────────────────────────────────────────────────────

@login_required
def task_list(request):
    form = TaskSearchForm(request.GET)
    tasks = Task.objects.select_related("task_type").prefetch_related("assignees", "tags")

    if form.is_valid():
        search = form.cleaned_data.get("search")
        priority = form.cleaned_data.get("priority")
        is_completed = form.cleaned_data.get("is_completed")

        if search:
            tasks = tasks.filter(Q(name__icontains=search) | Q(description__icontains=search))
        if priority:
            tasks = tasks.filter(priority=priority)
        if is_completed == "true":
            tasks = tasks.filter(is_completed=True)
        elif is_completed == "false":
            tasks = tasks.filter(is_completed=False)

    return render(request, "tasks/task_list.html", {"tasks": tasks, "form": form})


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    return render(request, "tasks/task_detail.html", {"task": task})


@login_required
def task_create(request):
    form = TaskForm(request.POST or None)
    if form.is_valid():
        task = form.save(commit=False)
        task.created_by = request.user
        task.save()
        form.save_m2m()
        messages.success(request, f'Task "{task.name}" created successfully!')
        return redirect("tasks:task_detail", pk=task.pk)
    return render(request, "tasks/task_form.html", {"form": form, "title": "Create Task"})


@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    form = TaskForm(request.POST or None, instance=task)
    if form.is_valid():
        form.save()
        messages.success(request, f'Task "{task.name}" updated successfully!')
        return redirect("tasks:task_detail", pk=task.pk)
    return render(request, "tasks/task_form.html", {"form": form, "task": task, "title": "Edit Task"})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == "POST":
        name = task.name
        task.delete()
        messages.success(request, f'Task "{name}" deleted.')
        return redirect("tasks:task_list")
    return render(request, "tasks/task_confirm_delete.html", {"task": task})


@login_required
def task_toggle_complete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.is_completed = not task.is_completed
    task.save()
    status = "completed" if task.is_completed else "reopened"
    messages.success(request, f'Task "{task.name}" marked as {status}.')
    next_url = request.GET.get("next", "tasks:task_list")
    return redirect(next_url)


# ── Workers ────────────────────────────────────────────────────────────────────

@login_required
def worker_list(request):
    workers = Worker.objects.select_related("position").annotate(
        task_count=Count("assigned_tasks")
    )
    return render(request, "tasks/worker_list.html", {"workers": workers})


@login_required
def worker_detail(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    completed = worker.assigned_tasks.filter(is_completed=True).select_related("task_type")
    pending = worker.assigned_tasks.filter(is_completed=False).select_related("task_type")
    return render(request, "tasks/worker_detail.html", {
        "worker": worker,
        "completed_tasks": completed,
        "pending_tasks": pending,
    })


def worker_create(request):
    form = WorkerCreationForm(request.POST or None)
    if form.is_valid():
        worker = form.save()
        login(request, worker)
        messages.success(request, "Account created! Welcome aboard.")
        return redirect("tasks:index")
    return render(request, "tasks/worker_form.html", {"form": form, "title": "Register"})


@login_required
def worker_update(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    if request.user != worker and not request.user.is_staff:
        messages.error(request, "You can only edit your own profile.")
        return redirect("tasks:worker_detail", pk=pk)
    form = WorkerUpdateForm(request.POST or None, instance=worker)
    if form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("tasks:worker_detail", pk=worker.pk)
    return render(request, "tasks/worker_form.html", {"form": form, "worker": worker, "title": "Edit Profile"})


@login_required
def worker_delete(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    if request.user != worker and not request.user.is_staff:
        messages.error(request, "You can only delete your own account.")
        return redirect("tasks:worker_detail", pk=pk)
    if request.method == "POST":
        worker.delete()
        messages.success(request, "Account deleted.")
        return redirect("tasks:worker_list")
    return render(request, "tasks/worker_confirm_delete.html", {"worker": worker})


# ── Tags ───────────────────────────────────────────────────────────────────────

@login_required
def tag_list(request):
    tags = Tag.objects.annotate(task_count=Count("tasks"))
    return render(request, "tasks/tag_list.html", {"tags": tags})


@login_required
def tag_create(request):
    form = TagForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Tag created!")
        return redirect("tasks:tag_list")
    return render(request, "tasks/simple_form.html", {"form": form, "title": "Create Tag"})


@login_required
def tag_update(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    form = TagForm(request.POST or None, instance=tag)
    if form.is_valid():
        form.save()
        messages.success(request, "Tag updated!")
        return redirect("tasks:tag_list")
    return render(request, "tasks/simple_form.html", {"form": form, "title": "Edit Tag", "obj": tag})


@login_required
def tag_delete(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    if request.method == "POST":
        tag.delete()
        messages.success(request, "Tag deleted.")
        return redirect("tasks:tag_list")
    return render(request, "tasks/simple_confirm_delete.html", {"obj": tag, "obj_type": "Tag"})


# ── Task Types ─────────────────────────────────────────────────────────────────

@login_required
def task_type_list(request):
    task_types = TaskType.objects.annotate(task_count=Count("tasks"))
    return render(request, "tasks/task_type_list.html", {"task_types": task_types})


@login_required
def task_type_create(request):
    form = TaskTypeForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Task type created!")
        return redirect("tasks:task_type_list")
    return render(request, "tasks/simple_form.html", {"form": form, "title": "Create Task Type"})


@login_required
def task_type_update(request, pk):
    task_type = get_object_or_404(TaskType, pk=pk)
    form = TaskTypeForm(request.POST or None, instance=task_type)
    if form.is_valid():
        form.save()
        messages.success(request, "Task type updated!")
        return redirect("tasks:task_type_list")
    return render(request, "tasks/simple_form.html", {"form": form, "title": "Edit Task Type", "obj": task_type})


@login_required
def task_type_delete(request, pk):
    task_type = get_object_or_404(TaskType, pk=pk)
    if request.method == "POST":
        task_type.delete()
        messages.success(request, "Task type deleted.")
        return redirect("tasks:task_type_list")
    return render(request, "tasks/simple_confirm_delete.html", {"obj": task_type, "obj_type": "Task Type"})


# ── Positions ──────────────────────────────────────────────────────────────────

@login_required
def position_list(request):
    positions = Position.objects.annotate(worker_count=Count("workers"))
    return render(request, "tasks/position_list.html", {"positions": positions})


@login_required
def position_create(request):
    form = PositionForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Position created!")
        return redirect("tasks:position_list")
    return render(request, "tasks/simple_form.html", {"form": form, "title": "Create Position"})


@login_required
def position_update(request, pk):
    position = get_object_or_404(Position, pk=pk)
    form = PositionForm(request.POST or None, instance=position)
    if form.is_valid():
        form.save()
        messages.success(request, "Position updated!")
        return redirect("tasks:position_list")
    return render(request, "tasks/simple_form.html", {"form": form, "title": "Edit Position", "obj": position})


@login_required
def position_delete(request, pk):
    position = get_object_or_404(Position, pk=pk)
    if request.method == "POST":
        position.delete()
        messages.success(request, "Position deleted.")
        return redirect("tasks:position_list")
    return render(request, "tasks/simple_confirm_delete.html", {"obj": position, "obj_type": "Position"})
