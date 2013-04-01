from diverse.cache import ModelCache

class LazyPolicyAccessorMixin(object):
    ac_cache = ModelCache
    ac_lazy  = False

    def __init__(self, *args, **kwargs):
        super(LazyPolicyAccessorMixin, self).__init__(*args, **kwargs)
        if self.accessor and isinstance(self.accessor, dict):
            self.ac_cache = self.accessor.get('cache', self.ac_cache)
            self.ac_lazy  = self.accessor.get('lazy', self.ac_lazy)

    # cache accessors
    def cache_get(self):
        if not self.ac_cache: return {}
        if not hasattr(self, '_attrs_cache'):
            data = self.ac_cache().get(self) or {}
            data = dict([(i,j) for i,j in data.items() if i in self.attrs_rel])
            self._attrs_cache = data
        return self._attrs_cache

    def cache_set(self):
        if not self.ac_cache: return None
        data = dict((i, self.__getattribute__('_get_%s' % i)(),)
                    for i in self.attrs_rel)
        self._attrs_cache = data
        return self.ac_cache().set(self, data)

    def cache_delete(self):
        self.ac_cache and self.ac_cache().delete(self)

    # main accessors policy methods: getting, creation and deletion
    # be carefull with modifying this - it is real __getattr__
    def __getattr__(self, name):
        # name in data related keys
        if name in self.attrs_rel:
            # get from cache
            value = self.cache_get().get(name, None)
            if not self.ac_lazy and value is not None:
                pass
            # get from state
            elif self._attrs.has_key(name):
                value = self._attrs[name]
            # get real value and set to state
            else:
                if self.generate(): return None
                value = self.__getattribute__('_get_%s' % name)()
                self._attrs[name] = value
                self.ac_lazy or self.cache_set() # does it need here?

        # name in data unrelated keys
        elif name in self.attrs_unrel:
            # get from state
            if self._attrs.has_key(name):
                value = self._attrs[name]
            # get real value and set to state
            else:
                self.ac_lazy and self.generate()
                value = self.__getattribute__('_get_%s' % name)()
                self._attrs[name] = value

        # raise std exception or get
        else:
            value = self.__getattribute__(name)

        return value

    # different: check laziness and save/delete cache if not lazy
    def create(self, force=False):
        if self.ac_lazy and not force:
            return None
        self.generate(force=force) or self.ac_lazy or self.cache_set()

    def delete(self):
        self.ac_lazy or self.cache_delete()
        self.storage().delete(self.name)