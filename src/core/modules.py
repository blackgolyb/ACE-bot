from functools import cached_property
import importlib
from pathlib import Path

from aiogram.dispatcher.router import Router

from .config import MODULES_MODULE


class SubmoduleRequiredVariableNotFoundError(Exception):
    def __init__(self, module_name: str, submodule_name: str, variable_name: str):
        self.module_name = module_name
        self.submodule_name = submodule_name
        self.variable_name = variable_name
        super().__init__(f"Found module {self.module_name} with {self.submodule_name} but there no {self.variable_name} variable")


class UselessModule(Exception):
    def __init__(self, module_name: str):
        self.module_name = module_name
        super().__init__(f"Found useless module {self.module_name}")


class RequiredSubmoduleNotFoundError(Exception):
    def __init__(self, module_name: str, submodule_name: str):
        self.module_name = module_name
        self.submodule_name = submodule_name
        super().__init__(f"Required submodule {self.submodule_name} not found in module {self.module_name}")


class BaseSubmodule:
    name: str
    shared: list[str]
    is_required: bool = False

    def __init__(self, modules_module_name: str):
        self.module_name_fmt = f"{modules_module_name}.{{}}.{self.name}"

    def assebly_module_name(self, module_name: str) -> str:
        return self.module_name_fmt.format(module_name)

    def load(self, module_name) -> bool:
        raise NotImplementedError()


class SubmoduleWithRequiredVariables(BaseSubmodule):
    variables_names: list[str]

    def __init__(self, modules_module_name: str):
        super().__init__(modules_module_name)
        self.callbacks = []

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def load(self, module_name) -> bool:
        mod = self.assebly_module_name(module_name)

        try:
            submodule = importlib.import_module(mod)
            variables = {}

            for variable_name in self.variables_names:
                variables[variable_name] = getattr(submodule, variable_name)

            for callback in self.callbacks:
                callback(variables)

            return True
        except ModuleNotFoundError:
            ...
        except AttributeError as e:
            if e.name in self.variables_names:
                raise SubmoduleRequiredVariableNotFoundError(module_name, self.name, e.name)
            raise e

        return False


class TasksSubmodule(SubmoduleWithRequiredVariables):
    name = "tasks"
    variables_names = ["tasks"]
    shared = ["tasks"]

    def add_tasks(self, variables):
        tasks = variables["tasks"]
        self.tasks.extend(tasks)

    def init(self):
        self.tasks = []
        self.register_callback(self.add_tasks)


class RouterSubmodule(SubmoduleWithRequiredVariables):
    name = "router"
    variables_names = ["router"]
    shared = ["router"]

    def include_router(self, variables):
        router = variables["router"]
        self.router.include_router(router)

    def init(self):
        self.router = Router()
        self.register_callback(self.include_router)


class ModulesLoader:
    default_submodules = [
        TasksSubmodule,
        RouterSubmodule,
    ]

    def __init__(self, submodules: list[BaseSubmodule] | None = None):
        self.modules_module_name = MODULES_MODULE

        if submodules is not None:
            self.submodules_classes = submodules
        else:
            self.submodules_classes = self.default_submodules

        self._init_submodules()

    def _init_submodules(self):
        self.submodules = []
        for submodule_class in self.submodules_classes:
            submodule_loader = submodule_class(self.modules_module_name)
            submodule_loader.init()
            self.submodules.append(submodule_loader)

    def __getattr__(self, name):
        for s in self.submodules:
            if name in s.shared:
                return getattr(s, name)

        return super().__getattr__(self, name)

    @cached_property
    def modules_module(self):
        return importlib.import_module(self.modules_module_name)

    @property
    def modules_module_path(self):
        return Path(self.modules_module.__path__[0])

    def check_useless_module(self, module_name: str, modules_is_in_use: list[bool]):
        mod = f"{self.modules_module_name}.{module_name}"

        if not any(modules_is_in_use):
            module = importlib.import_module(mod)
            keep_useless = False
            if hasattr(module, "keep_useless"):
                keep_useless = module.keep_useless

            if not keep_useless:
                raise UselessModule(module_name)

    def check_required_submodule(self, module_name, submodule, is_in_use):
        if submodule.is_required and not is_in_use:
            raise RequiredSubmoduleNotFoundError(module_name, submodule.name)

    def load_module(self, module_name):
        modules_is_in_use = []

        for submodule in self.submodules:
            is_in_use = submodule.load(module_name)
            self.check_required_submodule(module_name, submodule, is_in_use)
            modules_is_in_use.append(is_in_use)

        self.check_useless_module(module_name, modules_is_in_use)

    def load(self):
        for dir in self.modules_module_path.iterdir():
            if dir.is_dir():
                self.load_module(dir.name)
