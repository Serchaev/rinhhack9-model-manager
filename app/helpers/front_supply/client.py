from typing import AsyncGenerator, Optional

from app.helpers.aiohttp_client import AioHttpClient
from app.helpers.front_supply.models import GroupType
from app.helpers.interfaces import ClientHttpAbc


class FrontSupplyClient(AioHttpClient, ClientHttpAbc):
    async def create_group(
        self,
        name: str,
        group_type: GroupType = GroupType.REFERENCE_BOOK_GROUP,
        order: Optional[int] = None,
        description: Optional[str] = None,
        parent_id: Optional[str] = None,
        endpoint: str = "groups",
        **kwargs
    ) -> str:
        group = {
            "name": name,
            "group_type": group_type.value,
            "order": order,
            "description": description,
            "parent_id": parent_id,
            **kwargs,
        }
        return await self.create_object(data=group, session=self.session, endpoint=endpoint)

    async def update_group(self, uuid, data: dict, endpoint: str = "groups") -> bool:
        return await self.update_object(uuid=uuid, data=data, session=self.session, endpoint=endpoint)

    async def delete_group(self, uuid: str, endpoint: str = "groups") -> bool:
        return await self.delete_object(uuid=uuid, session=self.session, endpoint=endpoint)

    async def get_group(self, uuid: str, endpoint: str = "groups") -> dict:
        return await self.get_object(uuid=uuid, session=self.session, endpoint=endpoint)

    def get_groups_generator(self, filters: Optional[dict] = None, endpoint: str = "groups") -> AsyncGenerator:
        return self.get_objects_generator(filters=filters, session=self.session, endpoint=endpoint)

    async def get_groups(self, filters: Optional[dict] = None, endpoint: str = "groups") -> list[dict]:
        return await self.get_objects(filters=filters, session=self.session, endpoint=endpoint)

    async def create_reference_book(
        self,
        name: str,
        value: str,
        group_id: str,
        description: Optional[str] = None,
        order: Optional[int] = None,
        endpoint: str = "reference_book",
        **kwargs
    ) -> str:
        reference_book = {
            "name": name,
            "value": value,
            "order": order,
            "description": description,
            "group_id": group_id,
            **kwargs,
        }
        return await self.create_object(data=reference_book, session=self.session, endpoint=endpoint)

    async def update_reference_book(self, uuid, data: dict, endpoint: str = "reference_book") -> bool:
        return await self.update_object(uuid=uuid, data=data, session=self.session, endpoint=endpoint)

    async def delete_reference_book(self, uuid: str, endpoint: str = "reference_book") -> bool:
        return await self.delete_object(uuid=uuid, session=self.session, endpoint=endpoint)

    async def get_reference_book(self, uuid: str, endpoint: str = "reference_book") -> dict:
        return await self.get_object(uuid=uuid, session=self.session, endpoint=endpoint)

    async def get_reference_books(self, filters: Optional[dict] = None, endpoint: str = "reference_book") -> list[dict]:
        return await self.get_objects(filters=filters, session=self.session, endpoint=endpoint)

    def get_reference_books_generator(
        self, filters: Optional[dict] = None, endpoint: str = "reference_book"
    ) -> AsyncGenerator:
        return self.get_objects_generator(filters=filters, session=self.session, endpoint=endpoint)

    async def create_front_setting(
        self,
        name: str,
        jdata: dict,
        group_id: str,
        description: Optional[str] = None,
        order: Optional[int] = None,
        endpoint: str = "front_settings",
        **kwargs
    ) -> str:
        front_setting = {
            "name": name,
            "jdata": jdata,
            "order": order,
            "description": description,
            "group_id": group_id,
            **kwargs,
        }
        return await self.create_object(data=front_setting, session=self.session, endpoint=endpoint)

    async def update_front_setting(self, uuid, data: dict, endpoint: str = "front_settings") -> bool:
        return await self.update_object(uuid=uuid, data=data, session=self.session, endpoint=endpoint)

    async def delete_front_setting(self, uuid: str, endpoint: str = "front_settings") -> bool:
        return await self.delete_object(uuid=uuid, session=self.session, endpoint=endpoint)

    async def get_front_setting(self, uuid: str, endpoint: str = "front_settings") -> dict:
        return await self.get_object(uuid=uuid, session=self.session, endpoint=endpoint)

    async def get_front_settings(self, filters: Optional[dict] = None, endpoint: str = "front_settings") -> list[dict]:
        return await self.get_objects(filters=filters, session=self.session, endpoint=endpoint)

    def get_front_settings_generator(
        self, filters: Optional[dict] = None, endpoint: str = "front_settings"
    ) -> AsyncGenerator:
        return self.get_objects_generator(filters=filters, session=self.session, endpoint=endpoint)
