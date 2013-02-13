class BaseProcessor(object):
    def run(self, path, mimetype, storage, filever):
        self.process(path, mimetype, storage, filever)
        return self.status, self.mimetype

    def process(self, path, mimetype, storage, filever):
        raise NotImplementedError

    def extension(self, filever):
        """
        suggested extension:
            may return :same, real value (.ext) or None
            if None, VersionFile will raise NotImplementedError
            if :same, extension will be taken from source_file
        """
        return None