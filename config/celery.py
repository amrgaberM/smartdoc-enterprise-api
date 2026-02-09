import os
from celery import Celery

# 1. Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 2. Create the Celery app
app = Celery('config')

# 3. Read config from settings.py (Look for variables starting with CELERY_)
app.config_from_object('django.conf:settings', namespace='CELERY')

# 4. Auto-discover tasks in all installed apps
app.autodiscover_tasks()