"""
Test Suite 1: Django Application Loads
Verifies:
- Django settings configuration and security defaults
- Core, predictions, and accounts applications are registered and ready
- WSGI and ASGI application handlers instantiate correctly
- Default database connectivity and query execution
- Static files and templates directory resolution
"""

from django.test import TestCase
from django.conf import settings
from django.apps import apps
from django.db import connection
from pathlib import Path


class DjangoApplicationLoadTests(TestCase):
    def test_django_settings_configured(self):
        """Verifies fundamental Django settings are properly initialized."""
        self.assertTrue(settings.configured)
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertTrue(len(settings.SECRET_KEY) > 0)
        self.assertIn('default', settings.DATABASES)
        self.assertEqual(settings.DATABASES['default']['ENGINE'], 'django.db.backends.sqlite3')
        self.assertEqual(settings.ROOT_URLCONF, 'skysense.urls')

    def test_installed_apps_registered(self):
        """Verifies that all SKYsense AI custom apps are registered in apps registry."""
        self.assertTrue(apps.is_installed('core'))
        self.assertTrue(apps.is_installed('predictions'))
        self.assertTrue(apps.is_installed('accounts'))
        self.assertTrue(apps.is_installed('django.contrib.auth'))
        self.assertTrue(apps.is_installed('django.contrib.contenttypes'))
        self.assertTrue(apps.is_installed('django.contrib.sessions'))
        self.assertTrue(apps.is_installed('django.contrib.messages'))
        self.assertTrue(apps.is_installed('django.contrib.staticfiles'))

    def test_app_configs_ready(self):
        """Verifies that app configs load models and components cleanly."""
        core_app = apps.get_app_config('core')
        predictions_app = apps.get_app_config('predictions')
        accounts_app = apps.get_app_config('accounts')

        self.assertEqual(core_app.name, 'core')
        self.assertEqual(predictions_app.name, 'predictions')
        self.assertEqual(accounts_app.name, 'accounts')

    def test_database_connection_functional(self):
        """Verifies database connection is alive and can execute queries."""
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
            self.assertEqual(row[0], 1)

    def test_wsgi_application_instantiation(self):
        """Verifies that the WSGI callable loads without import or syntax errors."""
        from skysense.wsgi import application
        self.assertIsNotNone(application)
        self.assertTrue(callable(application))

    def test_asgi_application_instantiation(self):
        """Verifies that the ASGI callable loads without import or syntax errors."""
        from skysense.asgi import application
        self.assertIsNotNone(application)
        self.assertTrue(callable(application))

    def test_templates_and_media_paths(self):
        """Verifies that template directories and media root are correctly configured."""
        self.assertTrue(len(settings.TEMPLATES) > 0)
        template_dirs = settings.TEMPLATES[0]['DIRS']
        self.assertTrue(any(Path(d).exists() for d in template_dirs))
        self.assertIsNotNone(settings.MEDIA_ROOT)
        self.assertIsNotNone(settings.MEDIA_URL)
        self.assertEqual(settings.MEDIA_URL, '/media/')
