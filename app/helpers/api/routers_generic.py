from fastapi import APIRouter, Depends


class GenericModelRouter:
    """
    Класс router для mixin
    :attr api_router:          Fast Api роутер
    :attr registry:            регистри для взаимодействия с бд
    """

    api_router: APIRouter = None
    registry: callable = None

    def __init__(self):
        if not (self.api_router and self.registry):
            raise NotImplementedError("Необходимо определить api_router и registry")
        self.dependencies: list[Depends] = [
            Depends(getattr(self, method)()) for method in dir(self) if method.startswith("_set_")
        ]

        for method in dir(self):
            if method.startswith("_add_"):
                init_method = getattr(self, method)
                init_method(self.api_router, self.registry, self.dependencies)
