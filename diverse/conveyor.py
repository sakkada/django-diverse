from __future__ import with_statement
from django.core.files.storage import FileSystemStorage
from . import settings
import mimetypes, shutil, hashlib, os, time

class VersionGenerationError(Exception):
    pass

class Conveyor(object):
    # convention: storage should operate files on local filesystem
    # to allow processors use system file operation functions
    storage_allowed = (FileSystemStorage,)
    storage = None

    def __init__(self, *args, **kwargs):
        if not self.storage or not isinstance(self.storage, self.storage_allowed):
            raise ValueError('Conveyor storage should be in storage_allowed (local fs).')

    def run(self, filever, force=False):
        raise NotImplementedError

class TempFileConveyor(Conveyor):
    def __init__(self, *args, **kwargs):
        self.storage = FileSystemStorage(location=settings.TEMPORARY_DIR)
        super(TempFileConveyor, self).__init__(*args, **kwargs)

    def run(self, filever, force=False):
        source_file = filever.source_file
        dest_storage = filever.storage()

        # check file existance and force
        if dest_storage.exists(filever.path):
            if not force: return
            dest_storage.delete(filever.path)

        # open (rb mode) source file
        source_closed = source_file.closed
        source_closed and source_file.open()

        # get hasher
        md5hash = hashlib.md5()
        md5hash.update('%s@%s' % (source_file.name, str(time.time())))

        # create temporary file and get mimetype
        tempname = os.path.splitext(source_file.name)
        tempname = '%s%s' % (md5hash.hexdigest(), tempname[1])
        tempname = self.storage.save(tempname, source_file)
        mimetype = mimetypes.guess_type(tempname)

        # safe processors call and close source
        status = True
        try:
            # run processors conveyor
            for processor in filever.processors():
                tempname, mimetype = processor.run(tempname, mimetype,
                                                    self.storage, filever)
                if not tempname: break
        except Exception, e:
            status = False
            # alter default exception message
            message = 'File version "%s" generation error for "%s" at %s. Real' \
                      ' reason is: %%s' % (filever.attrname, source_file.name,
                                           processor.__class__)
            e.args = tuple([message % e.args[0]] + list(e.args[1:]))
            raise
        else:
            if status:
                # save target file with destination storage
                # todo: check new filename correctness
                with self.storage.open(tempname) as tempfile:
                    dest_storage.save(filever.path, tempfile)
        finally:
            # close source and delete temporary
            source_closed and source_file.close()
            # warning: delete is unsafe with locks (especially write mode locks)
            #          that means that each processor have to be extremally
            #          safety with opened filepointers
            self.storage.delete(tempname)

        if not status:
            status = 'File version "%s" generation error for "%s" at %s.' \
                     % (filever.attrname, source_file.name, processor.__class__)
            raise VersionGenerationError(status)