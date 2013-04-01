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

    def process(self, name, mimetype, storage, filever):
        filename, mimetype = False, mimetype

        # exception will be processed in versionfile generate method
        try:
            fp = storage.open(name)
        except IOError:
            raise

        # get content and close processing file
        content = StringIO(fp.read())
        fp.close()

        # main transformation call
        content = self._process_content(name, content, filever.source_file)

        # save processing file (delete original and save new with same name)
        storage.delete(name)
        filename = storage.save(name, content)

        # result filename (as status) and mimetype for next proc
        return filename, content.file.content_type

    def _process_content(self, filename, content, source_file):
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