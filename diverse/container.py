from version import BaseVersion

class MetaContainer(type):
    def __new__(cls, name, bases, attrs):
        cclass = super(MetaContainer, cls).__new__(cls, name, bases, attrs)
        cclass._versions = {}
        for name, value in attrs.items():
            if name.startswith('vs_') or not isinstance(value, BaseVersion): continue
            cclass.version_register(name, value)

        return cclass

class BaseContainer(object):
    __metaclass__ = MetaContainer
    attrname = 'dc'
    _versions = None
    _version_params = ('conveyor', 'versionfile', 'accessor',
                       'filename', 'extension', 'storage',)

    @classmethod
    def version_params(cls):
        params = [(n, getattr(cls, 'vs_%s' % n)) for n in cls._version_params \
                                                 if hasattr(cls, 'vs_%s' % n)]
        return dict(params)

    @classmethod
    def version_register(cls, name, value):
        # set container specific version params
        # and force attrname assign to version
        params = cls.version_params()
        value.params(**params) if params else None
        value.params(attrname=name, force=True)

        # register version in internal registry
        # and del same named container property
        cls._versions.__setitem__(name, value)
        hasattr(cls, name) and delattr(cls, name)

    def __init__(self, source_file, data=None):
        self.source_file = source_file
        self.data = data
        self._versionfiles = {}

    def __getattr__(self, name):
        if name in self._versionfiles:
            versfile = self._versionfiles[name]
        elif name in self._versions:
            versfile = self._versionfiles[name] = self.version(name)
        else:
            self.__getattribute__(name)
        return versfile

    def version(self, name, instantiate=True):
        """
        version get method, for overrite behaviour of version creating to set
        some attrs in all(any) versions directly (use on your own risk),
        for example, like that:

        def version(self, name, instantiate=False):
            cls, args, kwargs = super(SomeClass, self).version(name, False)
            kwargs.update({'lazy': True, 'quiet': False,})
            return cls(*args, **kwargs)
        """

        if name not in self._versions:
            raise IndexError('Version with name %s does not exists.' % name)

        return self._versions[name].version(self.source_file, data=self.data,
                                            instantiate=instantiate)

    def post_save_handler(self):
        """model post save handler"""
        for name in self._versions.keys():
            self.__getattr__(name).create()

    def delete_versions(self):
        """model pre delete handler"""
        for name in self._versions.keys():
            self.__getattr__(name).delete()