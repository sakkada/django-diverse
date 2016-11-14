from django import VERSION
from .fields import DiverseFileField, DiverseImageField

if VERSION < (1, 2, 5,):
    raise Exception('Diverse FileField require Django 1.2.5 or greater.')
