class BaseProcessor(object):

    def run(self, name, mimetype, storage, filever):
        # (filename (as status), mimetype,) tuple expected
        return self.process(name, mimetype, storage, filever)

    def process(self, name, mimetype, storage, filever):
        raise NotImplementedError

    def extension(self, filever):
        """
        suggested extension:
            may return :same, real value (.ext) or None
            if None, VersionFile will raise NotImplementedError
            if :same, extension will be taken from source_file
        """
        return None
