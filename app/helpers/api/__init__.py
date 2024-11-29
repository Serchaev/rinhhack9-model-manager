from app.helpers.api.common_types import (
    HTTPExceptionModel,
    ObjectCreateOut,
    StatusOut,
    unvalidated_pydantic,
)
from app.helpers.api.exception_handler import (
    add_exception_handler,
    add_object_not_found_handler,
    add_object_service_unavailable_handler,
)
from app.helpers.api.filters import PatchedFilter
from app.helpers.api.health_check import add_health_check_router
from app.helpers.api.pydantic_mixins import AddFieldMixin
from app.helpers.api.routers_dependencies import AuthMixinDependencies
from app.helpers.api.routers_generic import GenericModelRouter
from app.helpers.api.routers_mixin import (
    CreateModelMixinRouter,
    CRUDMixinRouter,
    DeleteModelMixinRouter,
    FindPaginateModelMixinRouter,
    PatchModelMixinRouter,
    RetrieveModelMixinRouter,
    UpdateModelMixinRouter,
)
from app.helpers.api.server import Server
from app.helpers.api.static_swagger import add_swagger_static_router
from app.helpers.api.websocket_manager import WebsocketManager

__all__ = [
    "add_health_check_router",
    "add_object_not_found_handler",
    "AddFieldMixin",
    "CRUDMixinRouter",
    "AuthMixinDependencies",
    "WebsocketManager",
    "StatusOut",
    "ObjectCreateOut",
    "FindPaginateModelMixinRouter",
    "CreateModelMixinRouter",
    "UpdateModelMixinRouter",
    "DeleteModelMixinRouter",
    "GenericModelRouter",
    "PatchedFilter",
    "RetrieveModelMixinRouter",
    "add_exception_handler",
    "add_object_service_unavailable_handler",
    "Server",
    "PatchModelMixinRouter",
    "unvalidated_pydantic",
    "HTTPExceptionModel",
    "add_swagger_static_router",
]
