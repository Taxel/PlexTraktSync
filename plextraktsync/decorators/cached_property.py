try:
    from functools import cached_property
except ImportError:
    # For py<3.8
    # https://docs.python.org/3.8/library/functools.html
    # https://github.com/pydanny/cached-property/blob/409f24286e16ea3086af463edea6b80cdd62deed/cached_property.py#L18-L47

    class cached_property(object):
        """
        A property that is only computed once per instance and then replaces itself
        with an ordinary attribute. Deleting the attribute resets the property.
        Source: https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76
        """

        def __init__(self, func):
            self.__doc__ = getattr(func, "__doc__")
            self.func = func

        def __get__(self, obj, cls):
            if obj is None:
                return self

            value = obj.__dict__[self.func.__name__] = self.func(obj)
            return value
