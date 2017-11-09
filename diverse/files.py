import os
import mimetypes
from django.core.files.images import get_image_dimensions
from settings import QUIET_OPERATION
from accessor import LazyPolicyAccessorMixin


# todo: add logging
class VersionFileBase(object):
    # state attrs
    _generated = False
    _attrs = None

    # attrs names
    attrs_unrel = ['url', 'mimetype',]
    attrs_rel   = ['size',]

    # default values
    _conveyor = None

    def __init__(self, attrname, source_file, processors,
                 filename=None, extension=None, storage=None,
                 data=None, conveyor=None, accessor=None):
        """
        attrname    - name of version file
        source_file - django db file instance
        processors  - list or one of processor instances
        filename    - pattern with %s for extension (use carefully)
                      usually receive from version instance or empty
                      if empty: get _default_filename result value
        extension   - string value of ext (.ext), usually empty
        storage     - django file storage instance
        data        - additional data (model, instance, ect.)
        accessor    - access policy configuration params
        """

        self.attrname = attrname
        self.source_file = source_file
        self.data = data
        self.accessor = accessor

        # attrs list working via getters
        self._processors = (processors
                            if isinstance(processors, list) else [processors])
        self._filename = filename or self._default_filename()
        self._extension = (extension
                           if self._check_extension(extension) else None)
        self._conveyor = conveyor or self._conveyor
        self._storage = storage or source_file.storage

        # checks
        if not self._conveyor:
            raise ValueError('Conveyor value is required (by init args'
                             ' or by class property (_conveyor)).')
        # initial state
        self._attrs = {}

    # laziness check in __getattr__ and post_source_save
    # version attrs get methods (_get_[name])
    def _get_url(self):
        # unrelated method
        return self.storage().url(self.name)

    def _get_mimetype(self):
        # unrelated method
        return mimetypes.guess_type(self.path)[0]

    def _get_size(self):
        # related method
        return self.storage().size(self.name)

    # magic get/set methods
    def __setattr__(self, name, value):
        if name in self.attrs_rel + self.attrs_unrel:
            raise ValueError('You can\'t assign attributes named like'
                             ' attrs_rel(_unrel) entries.')
        super(VersionFileBase, self).__setattr__(name, value)

    # policy: getting attr, creation and deletion
    #         overridable by accessor
    def __getattr__(self, name):
        # name in data related or unrelated keys
        if name in self.attrs_rel + self.attrs_unrel:
            # get from state
            value = self._attrs.get('name', None)
            # get real value and set to state
            if value is None:
                if self.generate():
                    return None
                value = self._attrs[name] = self.__getattribute__(
                    '_get_%s' % name)()
        # raise std exception
        else:
            value = self.__getattribute__(name)

        return value

    def create(self, force=False):
        self.generate(force=force)

    def delete(self):
        self.storage().delete(self.name)

    # version generation
    def generate(self, force=False):
        if self._generated and not force:
            return
        try:
            self.process(force=force)
        except:
            if not QUIET_OPERATION:
                raise
            return 1
        self._generated = True

    def process(self, force=False):
        self.conveyor().run(self, force=force)

    # attributes
    @property
    def name(self):
        if not hasattr(self, '_name'):
            self._name = self.filename()
        return self._name

    @property
    def path(self):
        if not hasattr(self, '_path'):
            self._path = self.storage().path(self.name)
        return self._path

    def _default_filename(self):
        dirname, basename = os.path.split(self.source_file.name)
        basename, extension = os.path.splitext(basename)
        return '%sdcache/%s.%s%%s' % ('%s/' % dirname if dirname else '',
                                      basename, self.attrname)

    # processors getter
    def processors(self):
        return self._processors

    # filename getter
    def filename(self):
        return self._filename % self.extension()

    # extension getter
    def extension(self):
        return self._extension or self._suggested_extension()

    # conveyor getter
    def conveyor(self):
        return self._conveyor()

    # storage getter
    def storage(self):
        return self._storage

    # fast no regexp is extension checking
    def _check_extension(self, value):
        return (value and isinstance(value, basestring) and
                len(value) > 1 and value.startswith('.'))

    # getting suggested extension from processors or raise
    def _suggested_extension(self):
        # extension = proc = None
        for proc in self.processors()[::-1]:
            extension = proc.extension(self) or ''
            if not extension == ':same':
                break

        extension = (os.path.splitext(self.source_file.name)[1].lower()
                     if extension == ':same' else extension)
        if not extension or not (len(extension) > 1 and extension[0] == '.'):
            raise NotImplementedError(
                'Extension method override required with processor:'
                ' %s, ext value: "%s". Value is empty or incorrect.'
                % (proc.__class__.__name__, extension))
        return extension


class VersionImageFileBase(VersionFileBase):
    # add data related attrs
    attrs_rel = VersionFileBase.attrs_rel + ['width', 'height',]

    def _get_width(self):
        # related method
        return self._get_image_dimensions()[0]

    def _get_height(self):
        # related method
        return self._get_image_dimensions()[1]

    def _get_image_dimensions(self):
        if not hasattr(self, '_dimensions_cache'):
            if 'image' in self.mimetype:
                self._dimensions_cache = get_image_dimensions(self.path)
            else:
                self._dimensions_cache = [None, None]
        return self._dimensions_cache


# default versionfile classes
class VersionFile(LazyPolicyAccessorMixin, VersionFileBase):
    pass


class VersionImageFile(LazyPolicyAccessorMixin, VersionImageFileBase):
    pass
