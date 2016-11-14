import os
from django.db.models import signals
from django.db.models.fields.files import FileField, FieldFile
from django.db.models.fields.files import ImageField, ImageFieldFile
from django.core import checks
from .forms import DiverseFormFileField, DiverseFormImageField
from .validators import isuploaded


# file attr class
class DiverseFieldFile(FieldFile):
    def __getattr__(self, name):
        # do not create container attr by default (should i?)
        container = self.field.container
        if name in (container.attrname, '_container'):
            data = {'instance': self.instance, 'field': self.field,}
            self._container = container(self, data)
            setattr(self, container.attrname, self._container)
        return self.__getattribute__(name)

    def save(self, *args, **kwargs):
        super(DiverseFieldFile, self).save(*args, **kwargs)
        if not self.field.get_action(self.instance):
            self.field.set_action(self.instance, '__update__') # in post_save

    def delete(self, *args, **kwargs):
        self._container.delete_versions()
        super(DiverseFieldFile, self).delete(*args, **kwargs)

    @property
    def extension(self):
        file = getattr(self.instance, self.field.name)
        return file and os.path.splitext(file.name)[1]


# image attr class
class DiverseImageFieldFile(DiverseFieldFile, ImageFieldFile):
    def thumbnail(self):
        thumbnail = self.field.thumbnail
        return thumbnail and getattr(self._container, thumbnail, None)

    @property
    def thumbnail_tag(self):
        thumbnail = self.thumbnail()
        return ('<img src="%s" alt="%s" />' % (thumbnail.url, thumbnail.url,)
                if thumbnail else '[no thumbnail]')


# file field
class DiverseFileField(FileField):
    attr_class = DiverseFieldFile

    def __init__(self, verbose_name=None, container=None,
                  clearable=False, updatable=False, erasable=False, **kwargs):
        super(DiverseFileField, self).__init__(verbose_name=verbose_name, **kwargs)
        self.container, self.erasable = container, erasable
        self.clearable, self.updatable = clearable, updatable

    # django system check framework
    def check(self, **kwargs):
        errors = super(DiverseFileField, self).check(**kwargs)
        errors.extend(self._check_clearable())
        errors.extend(self._check_container())
        return errors

    def _check_clearable(self):
        if not self.blank and self.clearable:
            return [
                checks.Error(
                    'Non blank FileField can not be clearable.',
                    hint='Either set blank to True, or clearable to False.',
                    obj=self,
                    id='diverse.fields.E001',
                )
            ]
        return []

    def _check_container(self):
        if not self.container:
            return [
                checks.Error(
                    'Container is required for Diverse FileField.',
                    hint=None,
                    obj=self,
                    id='diverse.fields.E002',
                )
            ]
        return []

    def deconstruct(self):
        name, path, args, kwargs = super(DiverseFileField, self).deconstruct()
        # del kwargs['blank']
        # kwargs['container'] = self.container
        return name, path, args, kwargs

    # get/set special action for diverse fields in pre/post save
    def get_action(self, instance, default=None):
        actions = getattr(instance, '__diverse_update_actions__', {})
        return actions.get(self.name, default)

    def set_action(self, instance, value):
        """
        Set in-signals action for diverse containers.
        __delete__ - erase file and (or only) versions in pre_save
        __update__ - erase versions and regenerate it in post_save
        __change__ - erase previous file and (or only) versions in
                     pre_save and regenerate new versions in
                     post_save (after new file saved)
        """

        if not hasattr(instance, '__diverse_update_actions__'):
            instance.__diverse_update_actions__ = {}
        instance.__diverse_update_actions__[self.name] = value

    def save_form_data(self, instance, data):
        if data == '__delete__' and self.blank and self.clearable:
            action = '__delete__'
        elif data == '__update__' and self.updatable:
            action = '__update__'
        else:
            action = '__change__' if isuploaded(data) else '__none__'
            super(DiverseFileField, self).save_form_data(instance, data)
        self.set_action(instance, action)

    def pre_save(self, instance, add):
        # enhancement: may be move this to model.pre_save signal?
        #              it will resolve *_cache field definiton ordering issue
        file = getattr(instance, self.name)
        action = self.get_action(instance, '__none__')
        if action == '__delete__':
            # delete file (or versions) if delete checkbox is checked
            self._safe_erase(file, instance, save=False)
            setattr(instance, self.name, None)
        elif action == '__update__':
            # update file versions if update checkbox is checked
            # delete and create versions in post_save handler
            pass
        elif action == '__change__' and not add:
            # erase old file (or versions) before change if field is erasable
            orig = instance.__class__.objects.filter(pk=instance.pk).first()
            orig = getattr(orig, self.name, None)
            orig and self._safe_erase(orig, instance, save=False)

        return super(DiverseFileField, self).pre_save(instance, add)

    def formfield(self, **kwargs):
        keys = ['clearable', 'updatable',]
        kwargs['form_class'] = DiverseFormFileField
        kwargs.update([(i, getattr(self, i, None)) for i in keys])
        return super(DiverseFileField, self).formfield(**kwargs)

    # erasable deletion
    def contribute_to_class(self, cls, name):
        super(DiverseFileField, self).contribute_to_class(cls, name)
        signals.post_save.connect(self.post_save_handler, sender=cls)
        signals.post_delete.connect(self.post_delete_handler, sender=cls)

    def post_save_handler(self, instance, **kwargs):
        action = self.get_action(instance)
        file = getattr(instance, self.attname)
        if action in ('__update__', '__change__',):
            if action == '__update__':
                file._container.delete_versions()
            file._container.create_versions()

    def post_delete_handler(self, instance, **kwargs):
        file = getattr(instance, self.attname)
        self._safe_erase(file, instance, save=False)

    def _safe_erase(self, file, instance, save=True):
        if not file:
            return
        count = instance.__class__._default_manager
        count = count.filter(**{self.name: file.name,}) \
                     .exclude(pk=instance.pk).count()

        # File real fs erase
        if not count:
            # If no other object of this type references the file.
            if file.name != self.default:
                # And it's not the default value for future objects,
                # delete it from the backend (or just delete versions).
                if self.erasable:
                    file.delete(save=save)
                else:
                    file._container.delete_versions()
            else:
                # Otherwise, just erase all version files.
                file._container.delete_versions()
        # Try to close the file, so it doesn't tie up resources.
        file.closed or file.close()


# image field
class DiverseImageField(DiverseFileField, ImageField):
    attr_class = DiverseImageFieldFile

    def __init__(self, verbose_name=None, thumbnail=None, **kwargs):
        super(DiverseImageField, self).__init__(verbose_name=verbose_name, **kwargs)
        self.thumbnail = thumbnail

    def formfield(self, **kwargs):
        keys = ['clearable', 'updatable', 'thumbnail',]
        kwargs['form_class'] = DiverseFormImageField
        kwargs.update([(i, getattr(self, i, None)) for i in keys])
        return super(DiverseFileField, self).formfield(**kwargs)
