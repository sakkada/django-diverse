from StringIO import StringIO
from django.core.files.base import ContentFile
from diverse.processor import BaseProcessor
from .processors import ProcessorPipeline, AutoConvert
from .utils import UnknownFormatError, UnknownExtensionError, \
                   format_to_extension, extension_to_format, \
                   img_to_fobj, open_image
import os, mimetypes

class ImageKit(BaseProcessor):
    def __init__(self, processors=None, format=None,
                        options=None, autoconvert=True):
        self.processors = processors
        self.format = format
        self.options = options or {}
        self.autoconvert = autoconvert

    def process(self, path, mimetype, storage, filever):
        self.status, self.mimetype = False, mimetype

        try:
            fp = storage.open(path)
        except IOError:
            return

        fp.seek(0)
        content = StringIO(fp.read())
        fp.close()

        img, content, format = self._process_content(path, content)
        mimetype = mimetypes.guess_type('name%s' % format_to_extension(format))[0]
        status = self.savetempfile(storage, path, content)
        self.status, self.mimetype = status, mimetype

    def savetempfile(self, storage, path, content):
        """try to save file to the same path"""
        counter = 99 # may be another?
        while counter>0:
            path = os.path.abspath(path)
            storage.delete(path)
            pnew = storage.save(path, content)
            pnew = os.path.abspath(pnew)
            if pnew == path: break
            storage.delete(pnew)
            counter-=1

        return counter>0

    def _process(self, image):
        processors = ProcessorPipeline(self.processors or [])
        return processors.process(image.copy())

    def _process_content(self, filename, content):
        img = open_image(content)
        original_format = img.format
        img = self._process(img)
        options = dict(self.options or {})

        # determine the format.
        format = self.format
        if not format:
            extension = os.path.splitext(filename)[1].lower()
            try:
                format = extension_to_format(extension)
            except UnknownExtensionError:
                pass
        format = format or img.format or original_format or 'JPEG'

        # run the AutoConvert processor
        if self.autoconvert:
            autoconvert_processor = AutoConvert(format)
            img = autoconvert_processor.process(img)
            options = dict(autoconvert_processor.save_kwargs.items() + options.items())

        imgfile = img_to_fobj(img, format, **options)
        content = ContentFile(imgfile.read())

        return img, content, format

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