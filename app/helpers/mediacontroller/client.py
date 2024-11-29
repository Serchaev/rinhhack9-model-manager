import json
from io import BytesIO
from typing import AsyncGenerator, Optional

from aiohttp import FormData

from app.helpers.aiohttp_client import AioHttpClient
from app.helpers.interfaces import ClientHttpAbc


class MediaControllerClient(AioHttpClient, ClientHttpAbc):
    async def get_file(self, uuid: str, endpoint: str = "files") -> dict:
        return await self.get_object(uuid=uuid, session=self.session, endpoint=endpoint)

    async def get_files(self, filters: Optional[dict] = None, endpoint: str = "files") -> list[dict]:
        return await self.get_objects(filters=filters, session=self.session, endpoint=endpoint)

    def get_files_generator(self, filters: Optional[dict] = None, endpoint: str = "files") -> AsyncGenerator:
        return self.get_objects_generator(filters=filters, session=self.session, endpoint=endpoint)

    async def download(self, uuid: str, endpoint: str = "files/media") -> bytes:
        """
        Скачать файл
        :param uuid:        уникальный идентификатор файла
        :param endpoint:    путь запроса
        :return:            файл
        """
        async with self.session.get(f"/{endpoint}/{uuid}", params={"download": "true"}) as response:
            return await response.read()

    async def create_file(
        self,
        name: str,
        path: str,
        file_data: bytes,
        bucket: str,
        mimetype: str,
        uuid: Optional[str] = None,
        jdata: Optional[dict] = None,
        tags: Optional[dict] = None,
        references: Optional[str] = None,
        reference_uuid: Optional[str] = None,
        endpoint: str = "files",
        **kwargs,
    ) -> str:
        """
        Загрузить файл
        :param uuid:            уникальный идентификатор файла
        :param name:            название
        :param path:            путь
        :param file_data:       байты
        :param bucket:          бакет в хранилище
        :param mimetype:        тип файла
        :param jdata:           доп. данные
        :param tags:            теги
        :param references:      Связанный объект
        :param reference_uuid:  Идентификатор связанного объекта
        :param endpoint:        путь запроса
        :return:                уникальный идентификатор файла
        """
        form_data = FormData()
        data = {
            "uuid": uuid,
            "name": name,
            "path": path,
            "bucket": bucket,
            "mimetype": mimetype,
            "jdata": jdata,
            "tags": tags,
            "references": references,
            "reference_uuid": reference_uuid,
            **kwargs,
        }
        form_data.add_field("file", json.dumps(data))
        form_data.add_field("file_data", BytesIO(file_data), filename=name, content_type=mimetype)
        async with self.session.post(f"/{endpoint}/", data=form_data) as response:
            result = await response.json()
            return result["uuid"]

    async def delete_file(
        self,
        uuid: str,
        endpoint: str = "files",
    ) -> bool:
        return await self.delete_object(uuid=uuid, session=self.session, endpoint=endpoint)

    async def update_file(
        self,
        uuid,
        data: dict,
        endpoint: str = "files",
    ) -> bool:
        return await self.update_object(uuid=uuid, data=data, session=self.session, endpoint=endpoint)
