from pydantic import create_model


class AddFieldMixin:
    @classmethod
    def add_field(cls, **fields):
        return create_model("ModelWithFields", __base__=cls, **fields)
