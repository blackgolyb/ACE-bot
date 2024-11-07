from aiogram import F, Router as BaseRouter

from src.core.config import get_config


class CallOverwritter:
    def __init__(self, base_object):
        self.base_object = base_object

    def old_call(self, *args, **kwds):
        return self.base_object(*args, **kwds)

    def call(self, *args, **kwds):
        raise NotImplementedError()

    def __call__(self, *args, **kwds):
        return self.call(*args, **kwds)

    def __getattr__(self, attr):
        return getattr(self.base_object, attr)


class BaseAdminRouter(BaseRouter):
    def __init__(self):
        super().__init__()
        self._init_observers()

    def get_admins() -> list[int]:
        raise NotImplementedError()

    def __compile_filter(self):
        return F.from_user.id.in_(self.get_admins())

    def _path_observer(self, observer_name):
        observer = getattr(self, observer_name)
        admin_filter = self.__compile_filter()

        def wrap(*filters, **kwargs):
            if "filters" in kwargs:
                filters = kwargs["filters"]

            res = observer(admin_filter, *filters, **kwargs)
            return res

        new_observer = CallOverwritter(observer)
        new_observer.call = wrap

        self.observers[observer_name] = new_observer
        setattr(self, observer_name, new_observer)

    def _init_observers(self):
        for observer in self.observers:
            self._path_observer(observer)


class AdminRouter(BaseAdminRouter):
    def __init__(self):
        config = get_config()
        self.admins = config.bot.admins
        super().__init__()

    def get_admins(self) -> list[int]:
        return self.admins


class Router(BaseRouter):
    def __init__(self):
        super().__init__()
        self.admin = AdminRouter()
        self.include_router(self.admin)
