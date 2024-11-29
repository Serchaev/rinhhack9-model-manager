from abc import ABC, abstractmethod
from contextlib import contextmanager


class BaseProvider(ABC):
    def __init__(self, class_type, *args, **kwargs):
        self.class_type = class_type
        self.args, self.kwargs = self._init_sub_providers(*args, **kwargs)

    def override(self, class_object):
        call = self._call

        @contextmanager
        def base_provide_override():
            try:
                self._call = lambda: class_object
                yield self
            finally:
                self._call = call

        return base_provide_override()

    @abstractmethod
    def _call(self):
        pass

    def __call__(self):
        return self._call()

    def __getattribute__(self, item):
        try:
            return super().__getattribute__(item)
        except AttributeError:
            return getattr(self(), item)

    @staticmethod
    def _init_sub_providers(*args, **kwargs) -> tuple[list, dict]:
        new_args = []
        for param in args:
            if isinstance(param, BaseProvider):
                new_args.append(param())
            else:
                new_args.append(param)
        for key, value in kwargs.items():
            if isinstance(value, BaseProvider):
                kwargs[key] = value()
        return new_args, kwargs


class Singleton(BaseProvider):
    def __init__(self, class_type, *args, **kwargs):
        self.class_object = None
        super().__init__(class_type, *args, **kwargs)

    def _call(self):
        if not self.class_object:
            self.class_object = self.class_type(*self.args, **self.kwargs)
        return self.class_object


class Factory(BaseProvider):
    def _call(self):
        return self.class_type(*self.args, **self.kwargs)


class Resource(BaseProvider):
    def _call(self):
        yield self.class_type(*self.args, **self.kwargs)
