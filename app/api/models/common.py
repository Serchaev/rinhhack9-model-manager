from pydantic import BaseModel


class StatusOut(BaseModel):
    """
    Статус
    """

    status: bool
