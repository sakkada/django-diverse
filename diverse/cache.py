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
    update_value_immediately = True
    delete_value_immediately = False

    def get_specdata(self, version):
        if version.data:
            instance = version.data.get('instance', None)
            field = version.data.get('field', None)
        else:
            instance, field = None, None

        try:
            cache = (instance._meta.get_field('%s_cache' % field.name)
                     if field else None)
        except FieldDoesNotExist:
            cache = None

        return instance, cache.name if instance and cache else (None,)*2

    def update_instance(self, instance, cachefield):
        # do nothing if object still not in database
        if not instance.pk:
            return

        # call update of queryset to disable models signals
        queryset = instance.__class__.objects.filter(id=instance.pk)
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
            value[version.attrname] = data
            setattr(instance, cachefield, json.dumps(value))

            if self.update_value_immediately:
                self.update_instance(instance, cachefield)

        return True

    def delete(self, version):
        instance, cachefield = self.get_specdata(version)
        if instance and cachefield:
            cache = getattr(instance, cachefield, '')

            try:
                value = json.loads(cache) if cache else {}
            except ValueError:
                value = {}
            value.pop(version.attrname, None)
            setattr(instance, cachefield, json.dumps(value) if value else '')

            if self.delete_value_immediately:
                self.update_instance(instance, cachefield)
