from django.db.models import signals
from django.db.models.fields.files import FileField, FieldFile
from django.db.models.fields.files import ImageField, ImageFieldFile
from forms import DiverseFormFileField, DiverseFormImageField
import os

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
        self._container.post_save_handler()

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
        return '<img src="%s" alt="%s" />' % (thumbnail.url, thumbnail.url,) \
               if thumbnail else '[no thumbnail]'

# file field
class DiverseFileField(FileField):
    attr_class = DiverseFieldFile

    def __init__(self, verbose_name=None, container=None,
                  clearable=False, updatable=False, erasable=False, **kwargs):
        super(DiverseFileField, self).__init__(verbose_name=verbose_name, **kwargs)
        self.container, self.erasable = container, erasable
        self.clearable, self.updatable = clearable, updatable

        if not self.blank and self.clearable:
            raise ValueError('Non blank FileField can not be clearable.')

        if not self.container:
            raise ValueError('Container is required for Diverse FileField.')

    def save_form_data(self, instance, data):
        # overwrite to delete file if checkbox is selected
        if data == '__delete__' and self.blank and self.clearable:
            # delete file (or versions) while delete "checkbox" checked
            file = getattr(instance, self.name)
            self._safe_erase(file, instance)
            setattr(instance, self.name, None)
        elif data == '__update__' and self.updatable:
            # update file versions while update "checkbox" checked
            file = getattr(instance, self.name)
            file._container.delete_versions()
            file._container.post_save_handler()
        else:
            # erase old file (or versions) before update if field is erasable
            if instance.pk and data:
                file = instance.__class__.objects.get(pk=instance.pk)
                file = getattr(file, self.name)
                file and file != data and self._safe_erase(file, instance)
            super(DiverseFileField, self).save_form_data(instance, data)

    def formfield(self, **kwargs):
        keys = ['clearable', 'updatable',]
        kwargs['form_class'] = DiverseFormFileField
        kwargs.update([(i, getattr(self, i, None)) for i in keys])
        return super(DiverseFileField, self).formfield(**kwargs)

    # erasable deletion
    def contribute_to_class(self, cls, name):
        super(DiverseFileField, self).contribute_to_class(cls, name)
        signals.post_delete.connect(self.post_delete, sender=cls)

    def post_delete(self, instance, sender, **kwargs):
        file = getattr(instance, self.attname)
        self._safe_erase(file, instance, save=False)

    def _safe_erase(self, file, instance, save=True):
        if not file: return
        count = instance.__class__._default_manager
        count = count.filter(**{self.name: file.name,}) \
                     .exclude(pk=instance.pk).count()

        # File real fs erase
        if not count:
            # If no other object of this type references the file.
            if file.name != self.default:
                # And it's not the default value for future objects,
                # delete it from the backend (or just delete versions).
                file.delete(save=save) if self.erasable \
                else file._container.delete_versions()
            else:
                # Otherwise, just erase all version files.
                file._container.delete_versions()
        # Try to close the file, so it doesn't tie up resources.
        file.closed or file.close()

    def south_field_triple(self):
        """Return a suitable description of this field for South."""
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.files.FileField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)

# image field
class DiverseImageField(DiverseFileField, ImageField):
    attr_class = DiverseImageFieldFile

    def __init__(self, verbose_name=None, thumbnail=None, **kwargs):
        super(DiverseImageField, self).__init__(verbose_name=verbose_name, **kwargs)
        self.thumbnail = thumbnail

        # if not self.thumbnail:
        #     raise ValueError('Thumbnail is required for Diverse ImageField.')

    def formfield(self, **kwargs):
        keys = ['clearable', 'updatable', 'thumbnail',]
        kwargs['form_class'] = DiverseFormImageField
        kwargs.update([(i, getattr(self, i, None)) for i in keys])
        return super(DiverseFileField, self).formfield(**kwargs)

    def south_field_triple(self):
        """Return a suitable description of this field for South."""
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.files.ImageField"
        args, kwargs = introspector(self)
        return (field_class, args, kwargs)