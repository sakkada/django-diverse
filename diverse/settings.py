from django.conf import settings
import tempfile

TEMPORARY_DIR   = getattr(settings, 'DIVERSE_TEMPORARY_DIR', None) or tempfile.gettempdir()
QUIET_OPERATION = getattr(settings, 'DIVERSE_QUIET_OPERATION', False)