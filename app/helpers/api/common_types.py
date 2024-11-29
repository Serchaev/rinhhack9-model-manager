from copy import deepcopy
from typing import Annotated, Any, List, Mapping, Optional, Type
from uuid import UUID

from pydantic import BaseModel, Field


class StatusOut(BaseModel):
    """
    Статус
    """

    status: bool = Field(description="Статус")


class ObjectCreateOut(BaseModel):
    """
    Статус
    """

    uuid: UUID = Field(description="Уникальный идентификатор объекта")


class HTTPExceptionModel(BaseModel):
    """
    HTTP ошибка
    """

    detail: str = Field(description="Сообщение ошибки запроса")


class ProcessStatusOut(StatusOut):
    name: str = Field(description="Имя процесса")
    processes_num_plan: int = Field(description="Количество запланированных процессов")
    processes_num_alive: int = Field(description="Количество живых процессов")


def model_annotations_with_parents(model: BaseModel) -> Mapping[str, Any]:
    parent_models: List[Type] = [
        parent_model
        for parent_model in model.__bases__
        if (issubclass(parent_model, BaseModel) and hasattr(parent_model, "__annotations__"))
    ]

    annotations: Mapping[str, Any] = {}

    for parent_model in reversed(parent_models):
        annotations.update(model_annotations_with_parents(parent_model))

    annotations.update(model.__annotations__)
    return annotations


def partial_model_factory(model: BaseModel, prefix: str = "Partial", name: str = None) -> BaseModel:
    if not name:
        name = f"{model.__name__}{prefix}"

    return type(
        name,
        (model,),
        dict(
            __module__=model.__module__,
            __annotations__={
                k: Annotated[Optional[v], Field(default=None)] for k, v in model_annotations_with_parents(model).items()
            },
            model_config=model.model_config,
        ),
    )


def delete_none(items):
    if isinstance(items, dict):
        return {k: delete_none(v) for k, v in items.items() if v is not None}
    elif isinstance(items, (list, set, tuple)):
        return type(items)(delete_none(item) for item in items if item is not None)
    return items


def unvalidated_pydantic(pydantic_cls: Type[BaseModel], **data: Any) -> BaseModel:
    # TODO: Pydantic v2 почти в 4 раза быстрее чем unvalidated_pydantic()
    for name, field in pydantic_cls.model_fields.items():
        try:
            data[name]
        except KeyError:
            if field.is_required():
                raise TypeError(f"Missing required keyword argument {name!r}")
            # deepcopy is quite slow on None
            data[name] = None if field.default is None else deepcopy(field.default)
    pydantic_object = pydantic_cls.construct(_fields_set=set(data.keys()), **data)
    return pydantic_object
