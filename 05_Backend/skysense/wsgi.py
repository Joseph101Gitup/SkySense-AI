"""
WSGI config for SkySenseWeb project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skysense.settings')

application = get_wsgi_application()
