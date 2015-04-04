"""
Singleton inhearitable object
"""


class Singleton(object):
    """A Simple inheritable singleton"""
    __single = None
    def __new__(cls, *args, **kwargs):
        if cls != type(cls.__single):
            cls.__single = object.__new__(cls, *args, **kwargs)
        return cls.__single

