# task_flow

TaskFlow - IT teams Task Manager
A Django-based task management system for IT teams. Inspired by Trello/ClickUp, built as a portfolio project.


DB Structure

![Скріншот](https://github.com/rer8/task_flow/blob/develop/docs/db_structure.png)


## Setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Features

Dashboard - overview stats, recent tasks, my pending tasks
Task Management - create, assign, prioritize, and complete tasks
Team Management - workers with positions, per-worker task stats (completed vs pending)
Tags - Many-to-Many tagging with custom labels (e.g. python-refactoring, landing-page-layout)
Task Types - Bug Fix, Feature, Deployment, etc.
Positions - Backend Developer, QA Engineer, etc.
Search & Filter - filter tasks by name, priority, and completion status
Overdue detection - visual indicators for tasks past their deadline
Authentication - login, register, profile management

Demo Credentials
root:admin pass:admin1234

# TechStack
Backend: Django 6, SQLite
Frontend: Bootstrap 5.3, Bootstrap Icons
Fonts: Syne + JetBrains Mono
