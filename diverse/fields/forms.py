import os
from django.forms import ValidationError
from django.forms.fields import FileField, ImageField
from django.utils.translation import ugettext as _
from django.template.defaultfilters import filesizeformat
from widgets import DiverseFileInput, DiverseImageFileInput


class DiverseFormFileField(FileField):
    default_widget = DiverseFileInput

    def __init__(self, *args, **kwargs):
        self.clearable = kwargs.pop('clearable', None)
        self.updatable = kwargs.pop('updatable', None)

        widget = kwargs.get('widget', self.default_widget)
        if isinstance(widget, type) and issubclass(widget, self.default_widget):
            kwargs["widget"] = widget(
                show_update_checkbox=self.updatable,
                show_delete_checkbox=(self.clearable and not
                                      kwargs.get("required", True)),
            )

        super(DiverseFormFileField, self).__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        return (data if data in ['__delete__', '__update__',] else
                super(DiverseFormFileField, self).clean(data, initial))


class DiverseFormImageField(DiverseFormFileField, ImageField):
    default_widget = DiverseImageFileInput

    def __init__(self, *args, **kwargs):
        self.clearable = kwargs.pop('clearable', None)
        self.updatable = kwargs.pop('updatable', None)
        self.thumbnail = kwargs.pop('thumbnail', None)

        widget = kwargs.get('widget', self.default_widget)
        if isinstance(widget, type) and issubclass(widget, self.default_widget):
            kwargs["widget"] = widget(
                show_update_checkbox=self.updatable,
                show_delete_checkbox=(self.clearable and not
                                      kwargs.get("required", True)),
                thumbnail=self.thumbnail,
            )

        super(DiverseFormFileField, self).__init__(*args, **kwargs)
