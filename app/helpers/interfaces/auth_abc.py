from abc import ABC, abstractmethod


class AuthClient(ABC):
    @abstractmethod
    async def get_user(self, token) -> dict:
        pass
