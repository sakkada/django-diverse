import os
from diverse.conveyor import TempFileConveyor
from diverse.files import VersionFile, VersionImageFile


class BaseVersion(object):
    # default values
    attrname = None
    conveyor = None
    versionfile = None
    filename = None
    extension = None
    storage = None
    accessor = None

    def __init__(self, processors,
                 attrname=None, conveyor=None, versionfile=None,
                 filename=None, extension=None, storage=None,
                 accessor=None):
        """
        processors  - list or one of processor instances
        attrname    - name of version file (usually assign by container)
        conveyor    - processors conveyor class
        versionfile - real file class (some like django FieldFile)
        filename    - pattern with named keys (dirname, basename, attrname,
                      extension) or callable (important: result must be source
                      content independent):
                        receive source_file, namedict and additional args
                        return pattern with one %s key for extension
        extension   - string value of ext (.ext), usually empty - versionfile
                      class get it by _suggested_extension (extension value
                      by processors)
        storage     - django file storage instance (todo: :default -> default storage)
        accessor    - access policy configuration params
        """

        self.processors = (processors if isinstance(processors, list) else
                           [processors])
        self.params(attrname=attrname, conveyor=conveyor,
                    versionfile=versionfile, filename=filename,
                    extension=extension, storage=storage,
                    accessor=accessor, force=True)

        if not self.versionfile:
            raise ValueError('Versionfile value is required (by init args'
                             ' or class property).')

    def params(self,
               attrname=None, conveyor=None, versionfile=None, filename=None,
               extension=None, storage=None, accessor=None, force=False):
        """
        each param purpose look at __init__ docstring
        this method alters each param only if original value is None or force
        """

        pdict = ('attrname', 'conveyor', 'versionfile',
                 'filename', 'extension', 'storage', 'accessor',)
        pdict = dict([(i, locals().get(i, None)) for i in pdict])
        check = lambda name: ((force and pdict.get(name) is not None) or
                              getattr(self, name) is None)

        self.attrname = attrname if check('attrname') else self.attrname
        self.conveyor = conveyor if check('conveyor') else self.conveyor
        self.versionfile = (versionfile if check('versionfile') else
                            self.versionfile)
        self.filename = filename if check('filename') else self.filename
        self.extension = (extension
                          if (check('extension') and
                              self._check_extension(extension)) else
                          self.extension)
        self.storage = storage if check('storage') else self.storage
        self.accessor = accessor if check('accessor') else self.accessor

    def getextension(self, source_file, *args):
        return self.extension

    # fast no regexp is extension checking
    def _check_extension(self, value):
        return (value and isinstance(value, basestring) and
                len(value) > 1 and value.startswith('.'))

    def getfilename(self, source_file, *args):
        filename = self.filename
        namedict = self.filenamedict(source_file, *args)
        if callable(filename):
            filename = filename(source_file, namedict, *args)
        elif filename:
            filename = filename % namedict
        return filename

    def filenamedict(self, source_file, *args):
        dirname, basename = os.path.split(source_file.name)
        basename, extension = os.path.splitext(basename)
        return {'dirname': dirname, 'basename': basename,
                'attrname': self.attrname, 'extension': r'%s',}

    def arguments(self, source_file, data=None):
        if not self.attrname:
            raise ValueError('Attrname value is required (by init args,'
                             ' class property or direct assignation).')

        arguments = [self.attrname, source_file, self.processors,]
        kwarguments = {'conveyor': self.conveyor,
                       'storage': self.storage,
                       'accessor': self.accessor,
                       'data': data,}

        # add data related values
        argslocal = [data, arguments, kwarguments]
        kwarguments.update({
            'filename': self.getfilename(source_file, *argslocal),
            'extension': self.getextension(source_file, *argslocal),
        })

        return self.versionfile, arguments, kwarguments

    def version(self, source_file, instantiate=True, data=None):
        cls, args, kwargs = self.arguments(source_file, data=data)
        return cls(*args, **kwargs) if instantiate else (cls, args, kwargs)


# build in version classes
class Version(BaseVersion):
    conveyor = TempFileConveyor
    versionfile = VersionFile


class ImageVersion(BaseVersion):
    conveyor = TempFileConveyor
    versionfile = VersionImageFile
