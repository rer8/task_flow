from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from tasks.models import Position, Tag, Task, TaskType, Worker


# ── Helpers ────────────────────────────────────────────────────────────────────

def make_worker(username="testuser", password="pass1234!", **kwargs):
    worker = Worker.objects.create_user(
        username=username, password=password, **kwargs
    )
    return worker


def make_task(name="Test Task", priority="medium", **kwargs):
    return Task.objects.create(name=name, priority=priority, **kwargs)


# ── Model Tests ────────────────────────────────────────────────────────────────

class PositionModelTest(TestCase):
    def test_str(self):
        pos = Position.objects.create(name="Backend Developer")
        self.assertEqual(str(pos), "Backend Developer")


class TagModelTest(TestCase):
    def test_str(self):
        tag = Tag.objects.create(name="python-refactoring")
        self.assertEqual(str(tag), "python-refactoring")


class TaskTypeModelTest(TestCase):
    def test_str(self):
        tt = TaskType.objects.create(name="Bug Fix")
        self.assertEqual(str(tt), "Bug Fix")


class WorkerModelTest(TestCase):
    def setUp(self):
        self.position = Position.objects.create(name="QA Engineer")
        self.worker = make_worker(
            username="alice",
            first_name="Alice",
            last_name="Smith",
            position=self.position,
        )

    def test_str(self):
        self.assertEqual(str(self.worker), "Alice Smith (alice)")

    def test_pending_tasks_property(self):
        task = make_task(name="Open", is_completed=False)
        task.assignees.add(self.worker)
        self.assertEqual(self.worker.pending_tasks.count(), 1)

    def test_completed_tasks_property(self):
        task = make_task(name="Done", is_completed=True)
        task.assignees.add(self.worker)
        self.assertEqual(self.worker.completed_tasks.count(), 1)

    def test_pending_excludes_completed(self):
        t1 = make_task(name="Open")
        t2 = make_task(name="Done", is_completed=True)
        t1.assignees.add(self.worker)
        t2.assignees.add(self.worker)
        self.assertEqual(self.worker.pending_tasks.count(), 1)
        self.assertEqual(self.worker.completed_tasks.count(), 1)


class TaskModelTest(TestCase):
    def test_str(self):
        task = make_task(name="Implement login")
        self.assertEqual(str(task), "Implement login")

    def test_is_overdue_when_past_deadline(self):
        past = timezone.now() - timezone.timedelta(days=1)
        task = make_task(deadline=past, is_completed=False)
        self.assertTrue(task.is_overdue)

    def test_is_not_overdue_when_future_deadline(self):
        future = timezone.now() + timezone.timedelta(days=1)
        task = make_task(deadline=future, is_completed=False)
        self.assertFalse(task.is_overdue)

    def test_is_not_overdue_when_completed(self):
        past = timezone.now() - timezone.timedelta(days=1)
        task = make_task(deadline=past, is_completed=True)
        self.assertFalse(task.is_overdue)

    def test_is_not_overdue_when_no_deadline(self):
        task = make_task(deadline=None)
        self.assertFalse(task.is_overdue)

    def test_priority_color(self):
        colors = {
            "urgent": "danger",
            "high": "warning",
            "medium": "info",
            "low": "secondary",
        }
        for priority, expected_color in colors.items():
            task = make_task(priority=priority)
            self.assertEqual(task.priority_color, expected_color)

    def test_many_to_many_tags(self):
        task = make_task()
        tag1 = Tag.objects.create(name="backend")
        tag2 = Tag.objects.create(name="frontend")
        task.tags.add(tag1, tag2)
        self.assertEqual(task.tags.count(), 2)

    def test_many_to_many_assignees(self):
        task = make_task()
        w1 = make_worker("w1")
        w2 = make_worker("w2")
        task.assignees.add(w1, w2)
        self.assertEqual(task.assignees.count(), 2)


# ── View Tests: Auth ───────────────────────────────────────────────────────────

class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.worker = make_worker(username="testuser", password="pass1234!")
        self.url = reverse("tasks:login")

    def test_login_page_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "TaskFlow")

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            self.url, {"username": "testuser", "password": "pass1234!"}
        )
        self.assertRedirects(response, reverse("tasks:index"))

    def test_login_with_invalid_credentials(self):
        response = self.client.post(
            self.url, {"username": "testuser", "password": "wrongpassword"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_authenticated_user_redirected_from_login(self):
        self.client.force_login(self.worker)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("tasks:index"))


class LogoutViewTest(TestCase):
    def test_logout_redirects(self):
        worker = make_worker()
        self.client.force_login(worker)
        response = self.client.get(reverse("tasks:logout"))
        self.assertRedirects(response, reverse("tasks:login"))


# ── View Tests: Dashboard ──────────────────────────────────────────────────────

class IndexViewTest(TestCase):
    def setUp(self):
        self.worker = make_worker()
        self.client.force_login(self.worker)

    def test_dashboard_loads(self):
        response = self.client.get(reverse("tasks:index"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("tasks:index"))
        self.assertRedirects(response, "/login/?next=/")

    def test_dashboard_shows_correct_counts(self):
        make_task("T1", is_completed=True)
        make_task("T2", is_completed=False)
        response = self.client.get(reverse("tasks:index"))
        self.assertEqual(response.context["total_tasks"], 2)
        self.assertEqual(response.context["completed_tasks"], 1)
        self.assertEqual(response.context["pending_tasks"], 1)

    def test_dashboard_shows_overdue_count(self):
        past = timezone.now() - timezone.timedelta(days=2)
        make_task("Overdue", deadline=past, is_completed=False)
        response = self.client.get(reverse("tasks:index"))
        self.assertEqual(response.context["overdue_tasks"], 1)


# ── View Tests: Tasks ──────────────────────────────────────────────────────────

class TaskListViewTest(TestCase):
    def setUp(self):
        self.worker = make_worker()
        self.client.force_login(self.worker)
        self.url = reverse("tasks:task_list")

    def test_task_list_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_task_list_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_task_list_shows_tasks(self):
        make_task("Alpha")
        make_task("Beta")
        response = self.client.get(self.url)
        self.assertContains(response, "Alpha")
        self.assertContains(response, "Beta")

    def test_search_filter(self):
        make_task("Fix login bug")
        make_task("Write documentation")
        response = self.client.get(self.url, {"search": "login"})
        self.assertContains(response, "Fix login bug")
        self.assertNotContains(response, "Write documentation")

    def test_priority_filter(self):
        make_task("Urgent task", priority="urgent")
        make_task("Low task", priority="low")
        response = self.client.get(self.url, {"priority": "urgent"})
        self.assertContains(response, "Urgent task")
        self.assertNotContains(response, "Low task")

    def test_completed_filter(self):
        make_task("Done", is_completed=True)
        make_task("Open", is_completed=False)
        response = self.client.get(self.url, {"is_completed": "true"})
        self.assertContains(response, "Done")
        self.assertNotContains(response, "Open")


class TaskDetailViewTest(TestCase):
    def setUp(self):
        self.worker = make_worker()
        self.client.force_login(self.worker)
        self.task = make_task("Detail Task")

    def test_task_detail_loads(self):
        response = self.client.get(reverse("tasks:task_detail", args=[self.task.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detail Task")

    def test_task_detail_404_for_missing(self):
        response = self.client.get(reverse("tasks:task_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)


class TaskCreateViewTest(TestCase):
    def setUp(self):
        self.worker = make_worker()
        self.client.force_login(self.worker)
        self.url = reverse("tasks:task_create")

    def test_create_form_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_create_task_success(self):
        response = self.client.post(self.url, {
            "name": "New Task",
            "priority": "medium",
            "description": "",
            "assignees": [],
            "tags": [],
        })
        self.assertEqual(Task.objects.filter(name="New Task").count(), 1)

    def test_created_by_set_to_current_user(self):
        self.client.post(self.url, {
            "name": "My Task",
            "priority": "low",
            "description": "",
        })
        task = Task.objects.get(name="My Task")
        self.assertEqual(task.created_by, self.worker)

    def test_create_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


class TaskUpdateViewTest(TestCase):
    def setUp(self):
        self.worker = make_worker()
        self.client.force_login(self.worker)
        self.task = make_task("Old Name")

    def test_update_task(self):
        url = reverse("tasks:task_update", args=[self.task.pk])
        self.client.post(url, {"name": "New Name", "priority": "high", "description": ""})
        self.task.refresh_from_db()
        self.assertEqual(self.task.name, "New Name")


class TaskDeleteViewTest(TestCase):
    def setUp(self):
        self.worker = make_worker()
        self.client.force_login(self.worker)
        self.task = make_task("To Delete")

    def test_delete_task(self):
        url = reverse("tasks:task_delete", args=[self.task.pk])
        self.client.post(url)
        self.assertEqual(Task.objects.filter(name="To Delete").count(), 0)


class TaskToggleViewTest(TestCase):
    def setUp(self):
        self.worker = make_worker()
        self.client.force_login(self.worker)

    def test_toggle_incomplete_to_complete(self):
        task = make_task(is_completed=False)
        self.client.get(reverse("tasks:task_toggle", args=[task.pk]))
        task.refresh_from_db()
        self.assertTrue(task.is_completed)

    def test_toggle_complete_to_incomplete(self):
        task = make_task(is_completed=True)
        self.client.get(reverse("tasks:task_toggle", args=[task.pk]))
        task.refresh_from_db()
        self.assertFalse(task.is_completed)


# ── View Tests: Workers ────────────────────────────────────────────────────────

class WorkerListViewTest(TestCase):
    def setUp(self):
        self.worker = make_worker()
        self.client.force_login(self.worker)

    def test_worker_list_loads(self):
        response = self.client.get(reverse("tasks:worker_list"))
        self.assertEqual(response.status_code, 200)

    def test_worker_list_shows_workers(self):
        make_worker("alice", first_name="Alice", last_name="Smith")
        response = self.client.get(reverse("tasks:worker_list"))
        self.assertContains(response, "Alice")


class WorkerDetailViewTest(TestCase):
    def setUp(self):
        self.worker = make_worker(
            username="alice", first_name="Alice", last_name="Smith"
        )
        self.client.force_login(self.worker)

    def test_worker_detail_loads(self):
        response = self.client.get(
            reverse("tasks:worker_detail", args=[self.worker.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice")

    def test_worker_detail_shows_pending_and_completed(self):
        pending = make_task("Pending Task", is_completed=False)
        done = make_task("Done Task", is_completed=True)
        pending.assignees.add(self.worker)
        done.assignees.add(self.worker)
        response = self.client.get(
            reverse("tasks:worker_detail", args=[self.worker.pk])
        )
        self.assertContains(response, "Pending Task")
        self.assertContains(response, "Done Task")

    def test_worker_detail_404_for_missing(self):
        response = self.client.get(reverse("tasks:worker_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)


class WorkerCreateViewTest(TestCase):
    def test_register_creates_worker_and_logs_in(self):
        response = self.client.post(reverse("tasks:register"), {
            "username": "newuser",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertTrue(Worker.objects.filter(username="newuser").exists())
        self.assertRedirects(response, reverse("tasks:index"))


# ── View Tests: Tags ───────────────────────────────────────────────────────────

class TagViewTest(TestCase):
    def setUp(self):
        self.worker = make_worker()
        self.client.force_login(self.worker)

    def test_tag_list_loads(self):
        response = self.client.get(reverse("tasks:tag_list"))
        self.assertEqual(response.status_code, 200)

    def test_create_tag(self):
        self.client.post(reverse("tasks:tag_create"), {"name": "new-tag"})
        self.assertTrue(Tag.objects.filter(name="new-tag").exists())

    def test_update_tag(self):
        tag = Tag.objects.create(name="old-name")
        self.client.post(reverse("tasks:tag_update", args=[tag.pk]), {"name": "new-name"})
        tag.refresh_from_db()
        self.assertEqual(tag.name, "new-name")

    def test_delete_tag(self):
        tag = Tag.objects.create(name="to-delete")
        self.client.post(reverse("tasks:tag_delete", args=[tag.pk]))
        self.assertFalse(Tag.objects.filter(name="to-delete").exists())


# ── View Tests: Task Types ─────────────────────────────────────────────────────

class TaskTypeViewTest(TestCase):
    def setUp(self):
        self.worker = make_worker()
        self.client.force_login(self.worker)

    def test_task_type_list_loads(self):
        response = self.client.get(reverse("tasks:task_type_list"))
        self.assertEqual(response.status_code, 200)

    def test_create_task_type(self):
        self.client.post(reverse("tasks:task_type_create"), {"name": "Bug Fix"})
        self.assertTrue(TaskType.objects.filter(name="Bug Fix").exists())

    def test_delete_task_type(self):
        tt = TaskType.objects.create(name="Old Type")
        self.client.post(reverse("tasks:task_type_delete", args=[tt.pk]))
        self.assertFalse(TaskType.objects.filter(name="Old Type").exists())


# ── View Tests: Positions ──────────────────────────────────────────────────────

class PositionViewTest(TestCase):
    def setUp(self):
        self.worker = make_worker()
        self.client.force_login(self.worker)

    def test_position_list_loads(self):
        response = self.client.get(reverse("tasks:position_list"))
        self.assertEqual(response.status_code, 200)

    def test_create_position(self):
        self.client.post(reverse("tasks:position_create"), {"name": "DevOps Engineer"})
        self.assertTrue(Position.objects.filter(name="DevOps Engineer").exists())

    def test_update_position(self):
        pos = Position.objects.create(name="Old Role")
        self.client.post(
            reverse("tasks:position_update", args=[pos.pk]), {"name": "New Role"}
        )
        pos.refresh_from_db()
        self.assertEqual(pos.name, "New Role")

    def test_delete_position(self):
        pos = Position.objects.create(name="To Remove")
        self.client.post(reverse("tasks:position_delete", args=[pos.pk]))
        self.assertFalse(Position.objects.filter(name="To Remove").exists())
