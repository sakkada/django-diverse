import tempfile
from django.conf import settings

QUIET_OPERATION = getattr(settings, 'DIVERSE_QUIET_OPERATION', False)
TEMPORARY_DIR = getattr(settings,  'DIVERSE_TEMPORARY_DIR',
                        None) or tempfile.gettempdir()
