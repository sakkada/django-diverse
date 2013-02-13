from diverse.processor import BaseProcessor
from .processors.base import ProcessorPipeline
from .lib import StringIO
from .utils import UnknownFormatError, UnknownExtensionError, \
                    format_to_extension, extension_to_format, \
                     img_to_fobj, open_image, IKContentFile
import os, mimetypes

class ImageKit(BaseProcessor):
    def __init__(self, processors=None, format=None,
                        options=None, autoconvert=True):
        self.processors = processors
        self.format = format
        self.options = options or {}
        self.autoconvert = autoconvert

    def savetempfile(self, storage, path, content):
        # try to save file to the same path using storage
        # todo: may be do something with this?
        #       now allow to work with files in processor manually
        #       because of check for local FS storage added
        counter = 9 # may be another?
        while counter>0:
            path = os.path.abspath(path)
            storage.delete(path)
            pnew = storage.save(path, content)
            pnew = os.path.abspath(pnew)
            if pnew == path: break
            storage.delete(pnew)
            counter-=1

        return counter>0

    def extension(self, filever):
        if self.format:
            try:
                extension = format_to_extension(self.format)
                extension = extension in ['.jpe', '.jpeg'] and '.jpg' or extension
            except UnknownFormatError:
                extension = ':same'
        else:
            extension = ':same'
        return extension

    def process(self, path, mimetype, storage, filever):
        self.status, self.mimetype = False, mimetype

        # todo: what should we do if not exists?
        try:
            fp = storage.open(path)
        except IOError:
            return

        # get content and close processing file
        fp.seek(0)
        content = StringIO(fp.read())
        fp.close()

        # main transformation call
        content = self._process_content(path, content, filever.source_file)

        # try to save to processing file (required same name)
        status = self.savetempfile(storage, path, content)

        # result status and mimetype for next proc
        self.status, self.mimetype = status, content.file.content_type

    def _process_content(self, filename, content, filever):
        # method code mostly based on
        #   imagekit.generators.SpecFileGenerator.process_content
        #   - filename param has now become required
        #   - source_file param also has now become required
        #   - callable processors get additionally param mimetype
        #   - img_to_fobj now receive also autoconvert param
        #   - return only content value, not img as first

        img = open_image(content)
        original_format = img.format

        # run the processors
        processors = self.processors
        if callable(processors):
            processors = processors(source_file, self.mimetype)
        img = ProcessorPipeline(processors or []).process(img)

        options = dict(self.options or {})

        # Determine the format.
        format = self.format
        if not format:
            # try to guess the format from the extension.
            extension = os.path.splitext(filename)[1].lower()
            try:
                format = extension and extension_to_format(extension)
            except UnknownExtensionError:
                pass
        format = format or img.format or original_format or 'JPEG'

        imgfile = img_to_fobj(img, format, autoconvert=self.autoconvert, **options)
        content = IKContentFile(filename, imgfile.read(), format=format)

        return content