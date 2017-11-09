import os
from pilkit.lib import StringIO
from pilkit.exceptions import UnknownExtension, UnknownFormat
from pilkit.utils import (format_to_extension, extension_to_format,
                          img_to_fobj, open_image)
from diverse.processor import BaseProcessor
from .utils import IKContentFile


class ProcessorPipeline(list):
    """
    A list of other processors. This class allows any object that
    knows how to deal with a single processor to deal with a list of them.
    For example:
        processed_image = ProcessorPipeline(
            [ProcessorA(), ProcessorB()]
        ).process(image)
    Note: extended version of builtin pilkit ProcessorPipeline
          with "takes_file_verion" attribute support.
    """
    def process(self, img, filever):
        for proc in self:
            tfv = getattr(proc, 'takes_file_verion', False)
            img = proc.process(*((img, filever,) if tfv else (img,)))
        return img


class ImageKit(BaseProcessor):
    processor_pipeline_class = ProcessorPipeline

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
                extension = ('.jpg' if extension in ['.jpe', '.jpeg'] else
                             extension)
            except UnknownFormat:
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
        content = self._process_content(name, content, filever)

        # save processing file (delete original and save new with same name)
        storage.delete(name)
        filename = storage.save(name, content)

        # result filename (as status) and mimetype for next proc
        return filename, content.file.content_type

    def _process_content(self, filename, content, filever):
        # method code mostly based on
        #   imagekit.generators.SpecFileGenerator.process_content
        #   - filename param has now become required
        #   - source_file param also has now become required
        #   - callable processors get additionally param mimetype
        #   - img_to_fobj now receive also autoconvert param
        #   - return only content value, not img as first

        source_file = filever.source_file
        img = open_image(content)
        original_format = img.format

        # run the processors
        processors = self.processors
        if callable(processors):
            processors = processors(source_file, self.mimetype)
        img = self.processor_pipeline_class(processors or
                                            []).process(img, filever)
        options = dict(self.options or {})

        # Determine the format.
        format = self.format
        if not format:
            # try to guess the format from the extension.
            extension = os.path.splitext(filename)[1].lower()
            try:
                format = extension and extension_to_format(extension)
            except UnknownExtension:
                pass
        format = format or img.format or original_format or 'JPEG'

        imgfile = img_to_fobj(img, format,
                              autoconvert=self.autoconvert, **options)
        content = IKContentFile(filename, imgfile.read(), format=format)

        return content
