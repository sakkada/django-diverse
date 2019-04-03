from rest_framework import fields


class DiverseFileField(fields.FileField):
    # versions to representation as list or tuple, None means all,
    # string means version as is (if original is not set to True)
    dc_versions = None
    # include original image as "self" key,
    # to show only original as only url use regular file field
    dc_original = False
    # use default representation (only url), should be used in
    # custom fileobj_to_representation method definition
    dc_url_only = False

    def __init__(self, *args, **kwargs):
        self.dc_versions = kwargs.pop('versions', self.dc_versions)
        self.dc_original = kwargs.pop('original', self.dc_original)
        self.dc_url_only = kwargs.pop('url_only', self.dc_url_only)
        super(DiverseFileField, self).__init__(*args, **kwargs)

    def get_version_data(self, obj, version):
        return

    def fileobj_to_representation(self, obj):
        return super(DiverseFileField, self).to_representation(obj)

    def version_to_representation(self, obj, version):
        return self.fileobj_to_representation(getattr(obj.dc, version))

    def to_representation(self, obj):
        data = None
        if obj:
            versions = self.dc_versions or obj.dc._versions.keys()
            is_iterable = isinstance(versions, (list, tuple,))
            if is_iterable or self.dc_original:
                data = dict(
                    (i, self.version_to_representation(obj, i),)
                    for i in (versions if is_iterable else [versions]))
                if self.dc_original:
                    data.update(self=self.fileobj_to_representation(obj))
            else:
                data = self.version_to_representation(obj, versions)
        return data


class DiverseImageField(DiverseFileField, fields.ImageField):
    def fileobj_to_representation(self, obj):
        url = super(DiverseImageField, self).fileobj_to_representation(obj)
        return url if self.dc_url_only else {
            'url': url, 'width': obj.width, 'height': obj.height,
        }
