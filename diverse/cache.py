import json
from django.db.models import FieldDoesNotExist

class BaseCache(object):
    def get(self, version):
        raise NotImplementedError

    def set(self, version, data):
        raise NotImplementedError

    def delete(self, version):
        raise NotImplementedError

class ModelCache(object):
    update_instance_independently = False

    def get_specdata(self, version):
        if version.data:
            instance = version.data.get('instance', None)
            field = version.data.get('field', None)
        else:
            instance, field = None, None

        try:
            cache = instance._meta.get_field_by_name('%s_cache' % field.name) \
                    if field else None
        except FieldDoesNotExist:
            cache = None

        return instance, cache[0].name if instance and cache else (None,)*2

    def update_instance(self, instance, cachefield):
        if not self.update_instance_independently: return
        queryset = instance.__class__.objects.filter(id=instance.pk)

        # do nothing if object still not in database
        if not instance.pk or not queryset.count(): return
        queryset.update(**{cachefield: getattr(instance, cachefield),})

    def get(self, version):
        instance, cachefield = self.get_specdata(version)

        value = {}
        if instance and cachefield:
            cache = getattr(instance, cachefield, '')
            try:
                value = json.loads(cache) if cache else {}
            except ValueError:
                value = {}
            value = value.get(version.attrname, {})

        return value

    def set(self, version, data):
        instance, cachefield = self.get_specdata(version)

        if instance and cachefield:
            cache = getattr(instance, cachefield, '')
            try:
                value = json.loads(cache) if cache else {}
            except ValueError:
                value = {}
            value.__setitem__(version.attrname, data)
            value = json.dumps(value)
            setattr(instance, cachefield, value)
            self.update_instance(instance, cachefield)

        return True

    def delete(self, version):
        instance, cachefield = self.get_specdata(version)

        value = {}
        if instance and cachefield:
            cache = getattr(instance, cachefield, '')
            try:
                value = json.loads(cache) if cache else {}
            except ValueError:
                value = {}
            value.has_key(version.attrname) and value.pop(version.attrname)
            value = json.dumps(value) if value else ''
            setattr(instance, cachefield, value)
            self.update_instance(instance, cachefield)

class ModelCacheSecure(ModelCache):
    update_instance_independently = True