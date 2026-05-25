from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic.edit import FormView

from tasks.forms import (
    LoginForm,
    PositionForm,
    TagForm,
    TaskForm,
    TaskSearchForm,
    TaskTypeForm,
    WorkerCreationForm,
    WorkerUpdateForm,
)
from tasks.models import Position, Tag, Task, TaskType, Worker


# ── Auth ───────────────────────────────────────────────────────────────────────

class LoginView(FormView):
    template_name = "tasks/login.html"
    form_class = LoginForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("tasks:index")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def form_valid(self, form):
        login(self.request, form.get_user())
        return redirect("tasks:index")


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("tasks:login")


# ── Dashboard ──────────────────────────────────────────────────────────────────

class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "tasks/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["total_tasks"] = Task.objects.count()
        ctx["completed_tasks"] = Task.objects.filter(is_completed=True).count()
        ctx["pending_tasks"] = Task.objects.filter(is_completed=False).count()
        ctx["overdue_tasks"] = Task.objects.filter(
            is_completed=False, deadline__lt=timezone.now()
        ).count()
        ctx["recent_tasks"] = (
            Task.objects.select_related("task_type")
            .prefetch_related("assignees", "tags")[:5]
        )
        ctx["my_tasks"] = (
            self.request.user.assigned_tasks
            .filter(is_completed=False)
            .select_related("task_type")[:5]
        )
        ctx["workers_count"] = Worker.objects.count()
        return ctx


# ── Tasks ──────────────────────────────────────────────────────────────────────

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"

    def get_queryset(self):
        qs = (
            Task.objects.select_related("task_type")
            .prefetch_related("assignees", "tags")
        )
        form = TaskSearchForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get("search")
            priority = form.cleaned_data.get("priority")
            is_completed = form.cleaned_data.get("is_completed")
            if search:
                qs = qs.filter(
                    Q(name__icontains=search) | Q(description__icontains=search)
                )
            if priority:
                qs = qs.filter(priority=priority)
            if is_completed == "true":
                qs = qs.filter(is_completed=True)
            elif is_completed == "false":
                qs = qs.filter(is_completed=False)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = TaskSearchForm(self.request.GET)
        return ctx


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"
    extra_context = {"title": "Create Task"}

    def form_valid(self, form):
        task = form.save(commit=False)
        task.created_by = self.request.user
        task.save()
        form.save_m2m()
        messages.success(self.request, f'Task "{task.name}" created successfully!')
        return redirect("tasks:task_detail", pk=task.pk)


class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"
    extra_context = {"title": "Edit Task"}

    def form_valid(self, form):
        task = form.save()
        messages.success(self.request, f'Task "{task.name}" updated successfully!')
        return redirect("tasks:task_detail", pk=task.pk)


class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = "tasks/task_confirm_delete.html"
    success_url = reverse_lazy("tasks:task_list")

    def form_valid(self, form):
        messages.success(self.request, f'Task "{self.object.name}" deleted.')
        return super().form_valid(form)


class TaskToggleCompleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        task = Task.objects.get(pk=pk)
        task.is_completed = not task.is_completed
        task.save()
        status = "completed" if task.is_completed else "reopened"
        messages.success(request, f'Task "{task.name}" marked as {status}.')
        next_url = request.GET.get("next") or request.META.get("HTTP_REFERER") or "/tasks/"
        return redirect(next_url if next_url.startswith("/") else "/tasks/")


# ── Workers ────────────────────────────────────────────────────────────────────

class WorkerListView(LoginRequiredMixin, ListView):
    model = Worker
    template_name = "tasks/worker_list.html"
    context_object_name = "workers"

    def get_queryset(self):
        return (
            Worker.objects.select_related("position")
            .annotate(task_count=Count("assigned_tasks"))
        )


class WorkerDetailView(LoginRequiredMixin, DetailView):
    model = Worker
    template_name = "tasks/worker_detail.html"
    context_object_name = "worker"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["completed_tasks"] = (
            self.object.assigned_tasks
            .filter(is_completed=True)
            .select_related("task_type")
        )
        ctx["pending_tasks"] = (
            self.object.assigned_tasks
            .filter(is_completed=False)
            .select_related("task_type")
        )
        return ctx


class WorkerCreateView(CreateView):
    model = Worker
    form_class = WorkerCreationForm
    template_name = "tasks/worker_form.html"
    extra_context = {"title": "Register"}

    def form_valid(self, form):
        worker = form.save()
        login(self.request, worker)
        messages.success(self.request, "Account created! Welcome aboard.")
        return redirect("tasks:index")


class WorkerUpdateView(LoginRequiredMixin, UpdateView):
    model = Worker
    form_class = WorkerUpdateForm
    template_name = "tasks/worker_form.html"
    extra_context = {"title": "Edit Profile"}

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user != obj and not request.user.is_staff:
            messages.error(request, "You can only edit your own profile.")
            return redirect("tasks:worker_detail", pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Profile updated successfully!")
        return redirect("tasks:worker_detail", pk=self.object.pk)


class WorkerDeleteView(LoginRequiredMixin, DeleteView):
    model = Worker
    template_name = "tasks/worker_confirm_delete.html"
    success_url = reverse_lazy("tasks:worker_list")

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user != obj and not request.user.is_staff:
            messages.error(request, "You can only delete your own account.")
            return redirect("tasks:worker_detail", pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Account deleted.")
        return super().form_valid(form)


# ── Tags ───────────────────────────────────────────────────────────────────────

class TagListView(LoginRequiredMixin, ListView):
    model = Tag
    template_name = "tasks/tag_list.html"
    context_object_name = "tags"

    def get_queryset(self):
        return Tag.objects.annotate(task_count=Count("tasks"))


class TagCreateView(LoginRequiredMixin, CreateView):
    model = Tag
    form_class = TagForm
    template_name = "tasks/simple_form.html"
    success_url = reverse_lazy("tasks:tag_list")
    extra_context = {"title": "Create Tag"}

    def form_valid(self, form):
        messages.success(self.request, "Tag created!")
        return super().form_valid(form)


class TagUpdateView(LoginRequiredMixin, UpdateView):
    model = Tag
    form_class = TagForm
    template_name = "tasks/simple_form.html"
    success_url = reverse_lazy("tasks:tag_list")
    extra_context = {"title": "Edit Tag"}

    def form_valid(self, form):
        messages.success(self.request, "Tag updated!")
        return super().form_valid(form)


class TagDeleteView(LoginRequiredMixin, DeleteView):
    model = Tag
    template_name = "tasks/simple_confirm_delete.html"
    success_url = reverse_lazy("tasks:tag_list")
    extra_context = {"obj_type": "Tag"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["obj"] = self.object
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Tag deleted.")
        return super().form_valid(form)


# ── Task Types ─────────────────────────────────────────────────────────────────

class TaskTypeListView(LoginRequiredMixin, ListView):
    model = TaskType
    template_name = "tasks/task_type_list.html"
    context_object_name = "task_types"

    def get_queryset(self):
        return TaskType.objects.annotate(task_count=Count("tasks"))


class TaskTypeCreateView(LoginRequiredMixin, CreateView):
    model = TaskType
    form_class = TaskTypeForm
    template_name = "tasks/simple_form.html"
    success_url = reverse_lazy("tasks:task_type_list")
    extra_context = {"title": "Create Task Type"}

    def form_valid(self, form):
        messages.success(self.request, "Task type created!")
        return super().form_valid(form)


class TaskTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = TaskType
    form_class = TaskTypeForm
    template_name = "tasks/simple_form.html"
    success_url = reverse_lazy("tasks:task_type_list")
    extra_context = {"title": "Edit Task Type"}

    def form_valid(self, form):
        messages.success(self.request, "Task type updated!")
        return super().form_valid(form)


class TaskTypeDeleteView(LoginRequiredMixin, DeleteView):
    model = TaskType
    template_name = "tasks/simple_confirm_delete.html"
    success_url = reverse_lazy("tasks:task_type_list")
    extra_context = {"obj_type": "Task Type"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["obj"] = self.object
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Task type deleted.")
        return super().form_valid(form)


# ── Positions ──────────────────────────────────────────────────────────────────

class PositionListView(LoginRequiredMixin, ListView):
    model = Position
    template_name = "tasks/position_list.html"
    context_object_name = "positions"

    def get_queryset(self):
        return Position.objects.annotate(worker_count=Count("workers"))


class PositionCreateView(LoginRequiredMixin, CreateView):
    model = Position
    form_class = PositionForm
    template_name = "tasks/simple_form.html"
    success_url = reverse_lazy("tasks:position_list")
    extra_context = {"title": "Create Position"}

    def form_valid(self, form):
        messages.success(self.request, "Position created!")
        return super().form_valid(form)


class PositionUpdateView(LoginRequiredMixin, UpdateView):
    model = Position
    form_class = PositionForm
    template_name = "tasks/simple_form.html"
    success_url = reverse_lazy("tasks:position_list")
    extra_context = {"title": "Edit Position"}

    def form_valid(self, form):
        messages.success(self.request, "Position updated!")
        return super().form_valid(form)


class PositionDeleteView(LoginRequiredMixin, DeleteView):
    model = Position
    template_name = "tasks/simple_confirm_delete.html"
    success_url = reverse_lazy("tasks:position_list")
    extra_context = {"obj_type": "Position"}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["obj"] = self.object
        return ctx

    def form_valid(self, form):
        messages.success(self.request, "Position deleted.")
        return super().form_valid(form)
