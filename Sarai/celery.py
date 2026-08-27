"""Celery application for the Sarai project."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Sarai.settings")

app = Celery("Sarai")

# All Celery settings live in Django settings under the CELERY_ prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load tasks.py from every installed app.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
