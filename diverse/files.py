from django.core.files.images import get_image_dimensions
import os, mimetypes

class VersionFile(object):

    # state attrs
    _generated = False

    # attrs names
    attrs_unrel = ['url', 'mimetype',]
    attrs_rel   = ['size',]

    # default values
    quiet = False
    lazy = False
    cache = None
    _conveyor = None

    def __init__(self, attrname, source_file, processors,
                  filename=None, extension=None, storage=None, data=None,
                   conveyor=None, cache=None, quiet=None, lazy=None):
        """
        attrname    - name of version file
        source_file - django db file instance
        processors  - list or one of processor instances
        filename    - pattern with %s for extension (use carefully)
                      usually receive from version instance or empty
                      if empty: get _default_filename result value
        extension   - string value of ext (.ext), usually empty
        storage     - django file storage instance
        cache       - cache class for caching datarel attrs
        data        - additional data (model, instance, ect.)
        quiet       - be quiet if generation errors
        lazy        - be lazy
        """

        self.attrname = attrname
        self.source_file = source_file
        self.data = data
        self.quiet = self.quiet if quiet is None else bool(quiet)
        self.lazy = self.lazy if lazy is None else bool(lazy)
        self.cache = cache or self.cache

        # attrs list working via getters
        self._processors = processors if isinstance(processors, list) else [processors]
        self._filename = filename or self._default_filename()
        self._extension = self._check_extension(extension) and extension or None
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

    # magic get/set methods (with laziness checking)
    def __setattr__(self, name, value):
        if name in self.attrs_rel + self.attrs_unrel:
            raise ValueError('You can\'t assign attributes named like attrs_rel(_unrel) entries.')
        super(VersionFile, self).__setattr__(name, value)

    def __getattr__(self, name):
        # name in data related keys
        if name in self.attrs_rel:
            # get from cache
            value = self.cache_get().get(name, None)
            if not self.lazy and value is not None:
                pass
            # get from state
            elif self._attrs.has_key(name):
                value = self._attrs[name]
            # get real value and set to state
            else:
                if self.generate(): return None
                value = self.__getattribute__('_get_%s' % name)()
                self._attrs[name] = value

        # name in data unrelated keys
        elif name in self.attrs_unrel:
            # get from state
            if self._attrs.has_key(name):
                value = self._attrs[name]
            # get real value and set to state
            else:
                if self.lazy and self.generate(): return None
                value = self.__getattribute__('_get_%s' % name)()
                self._attrs[name] = value

        # raise std exception
        else:
            self.__getattribute__(name)

        return value

    # creation and deletion
    def post_save_handler(self, force=False):
        if self.lazy and not force:
            return None
        self.generate(force=force)

    def delete(self):
        self.lazy or self.cache_delete()
        self.storage().delete(self.name)

    def generate(self, force=False):
        if self._generated and not force:
            return
        try:
            self.process()
        except:
            if not self.quiet: raise
            return 1
        self._generated = True
        self.lazy or self.cache_set()

    # processing
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
        return '%s/dcache/%s.%s%%s' % (dirname, basename, self.attrname)

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
        return value and isinstance(value, basestring) and len(value) > 1 \
                     and value.startswith('.')

    # getting suggested extension from processors or raise
    def _suggested_extension(self):
        # extension = proc = None
        for proc in self.processors()[::-1]:
            extension = proc.extension(self) or ''
            if not extension == ':same': break

        extension = os.path.splitext(self.source_file.name)[1].lower() \
                    if extension == ':same' else extension
        if not extension or not (len(extension) > 1 and extension[0] == '.'):
            raise NotImplementedError('Extension method override required with processor:'
                                      ' %s, ext value: "%s". Value is empty or incorrect.'
                                      % (proc.__class__.__name__, extension))
        return extension

    # cache system
    def cache_get(self):
        if not hasattr(self, '_attrs_cache'):
            if self.cache:
                data = self.cache().get(self) or {}
                data = dict([(i,j) for i,j in data.items() if i in self.attrs_rel])
                self._attrs_cache = data
            else:
                self._attrs_cache = {}
        return self._attrs_cache

    def cache_set(self):
        if not self.cache or self.generate():
            return None

        data = {}
        for i in self.attrs_rel:
            data[i] = self.__getattribute__('_get_%s' % i)()

        self._attrs_cache = data
        return self.cache().set(self, data)

    def cache_delete(self):
        self.cache and self.cache().delete(self)

class VersionImageFile(VersionFile):
    # add data related attrs
    attrs_rel = VersionFile.attrs_rel + ['width', 'height',]

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