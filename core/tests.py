from django.test import TestCase
from django.conf import settings

class SettingsTest(TestCase):
    def test_settings_configured(self):
        self.assertIn('192.168.10.229', settings.ALLOWED_HOSTS)
        self.assertEqual(settings.ASGI_APPLICATION, 'aiis_backend.asgi.application')
