import types

class PrivacyContext(object):
    def __init__(self):
        from django.utils.datastructures import SortedDict
        self.roles = SortedDict()
        self.comparator = cmp
        self.get_privacy = lambda obj: getattr(obj, 'privacy', {})

class RestrictedObject(object):
    def __init__(self, restricted, accessor, context, prefix=""):
        self._restricted = restricted
        self._privacy = context.get_privacy(restricted)
        self._accessor = accessor
        self._context = context
        self._prefix = prefix

    def _blanktype(self, value):
        if type(value) in types.StringTypes:
            return ""
        return "moo"
        #elif isinstance(value, (models.fields.files.ImageFieldFile, Photo)):
        #    return self.BlankImage()

    def __getattr__(self, attr):
        full_attr = '.'.join(self._prefix, attr)
        print full_attr
        if self._context.comparator(self._accessor, self._privacy.get(full_attr, None)) > 0:
            return RestrictedObject(getattr(self._restricted, attr), self._accessor, self._context, full_attr)
        return self.blanktype(getattr(self.restricted, attr))

