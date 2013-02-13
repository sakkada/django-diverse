from django.utils import simplejson
from django.db.models import FieldDoesNotExist

class BaseCache(object):
    def get(self, version):
        raise NotImplementedError

    def set(self, version, data):
        raise NotImplementedError

    def delete(self, version):
        raise NotImplementedError

class ModelCache(object):
    def get(self, version):
        if version.data:
            instance, field = version.data.get('instance', None), version.data.get('field', None)
        else:
            instance, field = None, None
            
        try:
            cache = instance and field and instance._meta.get_field_by_name('%s_cache' % field.name)
        except FieldDoesNotExist:
            cache = None

        value = {}
        if instance and field and cache:
            cache = getattr(instance, '%s_cache' % field.name, '')
            try:
                value = simplejson.loads(cache) if cache else {}
            except ValueError:
                value = {}
            value = value.get(version.attrname, {})

        return value

    def set(self, version, data):
        if version.data:
            instance, field = version.data.get('instance', None), version.data.get('field', None)
        else:
            instance, field = None, None

        try:
            cache = instance and field and instance._meta.get_field_by_name('%s_cache' % field.name)
        except FieldDoesNotExist:
            cache = None
            
        if instance and field and cache:
            cache = getattr(instance, '%s_cache' % field.name, '')
            try:
                value = simplejson.loads(cache) if cache else {}
            except ValueError:
                value = {}
            value.__setitem__(version.attrname, data)
            value = simplejson.dumps(value)
            setattr(instance, '%s_cache' % field.name, value)
        
        return True

    def delete(self, version):
        if version.data:
            instance, field = version.data.get('instance', None), version.data.get('field', None)
        else:
            instance, field = None, None
            
        try:
            cache = instance and field and instance._meta.get_field_by_name('%s_cache' % field.name)
        except FieldDoesNotExist:
            cache = None

        value = {}
        if instance and field and cache:
            cache = getattr(instance, '%s_cache' % field.name, '')
            try:
                value = simplejson.loads(cache) if cache else {}
            except ValueError:
                value = {}
            value.has_key(version.attrname) and value.pop(version.attrname)
            value = simplejson.dumps(value) if value else ''
            setattr(instance, '%s_cache' % field.name, value)