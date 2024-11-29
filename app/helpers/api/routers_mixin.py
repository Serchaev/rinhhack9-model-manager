from functools import partial
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi_filter.base.filter import BaseFilterModel, FilterDepends
from pydantic.main import BaseModel

from app.helpers.api.common_types import (
    HTTPExceptionModel,
    ObjectCreateOut,
    StatusOut,
    delete_none,
    partial_model_factory,
    unvalidated_pydantic,
)
from app.helpers.interfaces.pagination_abc import PaginationParamsABC
from app.helpers.interfaces.registry_abc import RegistryABC
from app.helpers.paginator import PageParams, paginate


class FindPaginateModelMixinRouter:
    """
    Mixin router для поиска объектов(с пагинацией)
    :attr filters_model:        фильтры
    :attr response_model:       выходные данные
    :attr paginator:            метод пагинации
    :attr find_descriptions:    описание метода
    :attr find_path:            путь
    """

    filters_model: BaseFilterModel = None
    response_model: BaseModel = None
    paginator_params = PageParams
    paginator: callable = paginate
    find_descriptions = "List objects"
    find_path: str = "/"
    validate: bool = True

    @classmethod
    async def _find(
        cls,
        request: Request,
        filters: BaseFilterModel,
        model_registry: RegistryABC,
        paginator: callable,
        paginator_params: PaginationParamsABC,
    ):
        return await model_registry.paginate_find(
            filters=filters, sorts=filters, paginator=partial(paginator, params=paginator_params)
        )

    @classmethod
    def _add_find(cls, api_router: APIRouter, registry: callable, dependencies: list[Depends]):
        if not (cls.response_model and cls.filters_model):
            raise NotImplementedError("Необходимо определить response_model и filters_model")

        @api_router.get(cls.find_path, dependencies=dependencies, description=cls.find_descriptions)
        async def find(
            request: Request,
            paginator_params: PaginationParamsABC = Depends(cls.paginator_params.query_parameters),
            filters: cls.filters_model = FilterDepends(cls.filters_model),
            model_registry: RegistryABC = Depends(registry),
        ) -> cls.response_model:
            response = await cls._find(request, filters, model_registry, cls.paginator, paginator_params)
            if cls.validate:
                return response
            return unvalidated_pydantic(cls.response_model, **response.dict())


class RetrieveModelMixinRouter:
    """
    Mixin router для поиска объекта
    :attr retrieve_model:           выходные данные
    :attr retrieve_descriptions:    описание метода
    :attr retrieve_path:            путь
    """

    retrieve_model: BaseModel = None
    retrieve_descriptions = "Retrieve objects"
    retrieve_path: str = "/{uuid}"
    id_type = UUID

    @classmethod
    async def _retrieve(cls, request: Request, uuid: Any, model_registry: RegistryABC):
        return await model_registry.get(uuid=uuid)

    @classmethod
    def _add_retrieve(cls, api_router: APIRouter, registry: callable, dependencies: list[Depends]):
        if not cls.retrieve_model:
            raise NotImplementedError("Необходимо определить retrieve_model")

        @api_router.get(
            cls.retrieve_path,
            dependencies=dependencies,
            responses={404: {"model": HTTPExceptionModel}},
            description=cls.retrieve_descriptions,
        )
        async def retrieve(
            request: Request, uuid: cls.id_type, model_registry: registry = Depends(registry)
        ) -> cls.retrieve_model:
            obj = await cls._retrieve(request, uuid, model_registry)
            if not obj:
                raise HTTPException(status_code=404, detail="Object not found")
            return obj


class CreateModelMixinRouter:
    """
    Mixin router для создания объектов
    :attr model_input:            входные данные
    :attr status_output:          выходные данные о статусе
    :attr create_path:            путь
    :attr create_descriptions:    описание метода
    """

    model_input: BaseModel = None
    create_output: BaseModel = ObjectCreateOut
    create_path: str = "/"
    create_descriptions: str = "Create object"

    @classmethod
    async def _create(cls, request: Request, data: BaseModel, model_registry: RegistryABC, create_output: BaseModel):
        uuid = await model_registry.create(**data.model_dump())
        return create_output(uuid=uuid)

    @classmethod
    def _add_create(cls, api_router: APIRouter, registry: callable, dependencies: list[Depends]):
        if not cls.model_input:
            raise NotImplementedError("Необходимо определить model_input")

        @api_router.post(
            cls.create_path,
            dependencies=dependencies,
            responses={400: {"model": HTTPExceptionModel}},
            description=cls.create_descriptions,
        )
        async def create(
            request: Request, data: cls.model_input, model_registry: registry = Depends(registry)
        ) -> cls.create_output:
            return await cls._create(request, data, model_registry, cls.create_output)


class UpdateModelMixinRouter:
    """
    Mixin router для обновления объектов
    :attr model_input:            входные данные
    :attr status_output:          выходные данные о статусе
    :attr update_path:            путь
    :attr update_descriptions:    описание метода
    """

    model_input: BaseModel = None
    update_output: BaseModel = StatusOut
    update_path: str = "/{uuid}"
    update_descriptions: str = "Update object"
    id_type = UUID

    @classmethod
    async def _update(
        cls, request: Request, uuid: Any, data: BaseModel, model_registry: RegistryABC, update_output: BaseModel
    ):
        await model_registry.update(uuid=uuid, **data.model_dump())
        return update_output(status=True)

    @classmethod
    def _add_update(cls, api_router: APIRouter, registry: callable, dependencies: list[Depends]):
        if not cls.model_input:
            raise NotImplementedError("Необходимо определить model_input")

        @api_router.put(
            cls.update_path,
            dependencies=dependencies,
            responses={400: {"model": HTTPExceptionModel}, 404: {"model": HTTPExceptionModel}},
            description=cls.update_descriptions,
        )
        async def update(
            request: Request, uuid: cls.id_type, data: cls.model_input, model_registry: registry = Depends(registry)
        ) -> cls.update_output:
            return await cls._update(request, uuid, data, model_registry, cls.update_output)


class PatchModelMixinRouter:
    """
    Mixin router для частичного обновления объектов
    :attr model_input:            входные данные
    :attr status_output:          выходные данные о статусе
    :attr update_path:            путь
    :attr update_descriptions:    описание метода
    """

    model_input: BaseModel = None
    patch_output: BaseModel = StatusOut
    patch_path: str = "/{uuid}"
    patch_descriptions: str = "Patch update object"
    id_type = UUID

    @classmethod
    async def _patch(
        cls, request: Request, uuid: Any, data: BaseModel, model_registry: RegistryABC, patch_output: BaseModel
    ):
        await model_registry.update(uuid=uuid, **delete_none(data.model_dump()))
        return patch_output(status=True)

    @classmethod
    def _add_patch(cls, api_router: APIRouter, registry: callable, dependencies: list[Depends]):
        if not cls.model_input:
            raise NotImplementedError("Необходимо определить model_input")
        model_input = partial_model_factory(cls.model_input, "Patch")

        @api_router.patch(
            cls.patch_path,
            dependencies=dependencies,
            responses={400: {"model": HTTPExceptionModel}, 404: {"model": HTTPExceptionModel}},
            description=cls.patch_descriptions,
        )
        async def patch(
            request: Request, uuid: cls.id_type, data: model_input, model_registry: registry = Depends(registry)
        ) -> cls.patch_output:
            return await cls._patch(request, uuid, data, model_registry, cls.patch_output)


class DeleteModelMixinRouter:
    """
    Mixin router для удаления объектов
    :attr status_output:          выходные данные о статусе
    :attr delete_path:            путь
    :attr delete_descriptions:    описание метода
    """

    delete_output: BaseModel = StatusOut
    delete_path: str = "/{uuid}"
    delete_descriptions: str = "Delete object"
    id_type = UUID

    @classmethod
    async def _delete(cls, request: Request, uuid: Any, model_registry: RegistryABC, delete_output: BaseModel):
        await model_registry.delete(uuid=uuid)
        return delete_output(status=True)

    @classmethod
    def _add_delete(cls, api_router: APIRouter, registry: callable, dependencies: list[Depends]):
        @api_router.delete(
            cls.delete_path,
            dependencies=dependencies,
            responses={404: {"model": HTTPExceptionModel}},
            description=cls.delete_descriptions,
        )
        async def delete(
            request: Request, uuid: cls.id_type, model_registry: registry = Depends(registry)
        ) -> cls.delete_output:
            return await cls._delete(request, uuid, model_registry, cls.delete_output)


class CRUDMixinRouter(
    FindPaginateModelMixinRouter,
    RetrieveModelMixinRouter,
    CreateModelMixinRouter,
    PatchModelMixinRouter,
    UpdateModelMixinRouter,
    DeleteModelMixinRouter,
):
    """
    Объединенные миксины для реализации CRUD
    """
