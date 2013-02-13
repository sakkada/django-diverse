from django import get_version
from fields import DiverseFileField
if get_version() < '1.2.5':
    raise Exception('Diverse FileField require Django 1.2.5 or greater.')