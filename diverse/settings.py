from django.conf import settings
import tempfile

TEMPORARY_DIR = getattr(settings, 'DIVERSE_TEMPORARY_DIR', None) or tempfile.gettempdir()