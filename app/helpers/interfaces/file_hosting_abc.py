from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Iterator, Protocol


class FileReaderProtocol(Protocol):
    def read(self) -> bytes:
        pass


class FileHostingClientAbc(ABC):
    @abstractmethod
    async def upload_file(self, bucket_name: str, object_name: str, data: FileReaderProtocol, **kwargs) -> str:
        """
        Загрузка файла в хранилище
        :param bucket_name:     название bucket
        :param object_name:     название файла
        :param data:            файл ридер
        :param kwargs:          дополнительные параметры
        :return:                название файла
        """
        pass

    @abstractmethod
    async def download_file_raw(self, bucket_name, object_name, **kwargs) -> Any:
        """
        Загрузка сырого файла из хранилища
        :param bucket_name:     название bucket
        :param object_name:     название файла
        :param kwargs:          дополнительные параметры
        :return:                байты
        """
        pass

    @abstractmethod
    async def download_file(self, bucket_name, object_name, **kwargs) -> bytes:
        """
        Загрузка файла из хранилища
        :param bucket_name:     название bucket
        :param object_name:     название файла
        :param kwargs:          дополнительные параметры
        :return:                байты
        """
        pass

    @abstractmethod
    async def download_file_chunk(self, bucket_name, object_name, **kwargs) -> AsyncGenerator:
        """
        Загрузка файла из хранилища чанками
        :param bucket_name:     название bucket
        :param object_name:     название файла
        :param kwargs:          дополнительные параметры
        :return:                название файла
        """
        pass

    async def delete_object(self, bucket_name: str, object_name: str, **kwargs) -> None:
        """
        Удаление файла из хранилища
        :param bucket_name:     название bucket
        :param object_name:     название файла
        :param kwargs:          дополнительные параметры
        :return:                название файла
        """
        pass

    async def get_list_objects(self, bucket_name: str, **kwargs) -> Iterator:
        """
        Данные файлов из хранилища
        :param bucket_name:     название bucket
        :param kwargs:          дополнительные параметры
        :return:                название файла
        """
        pass

    async def check_file_exist(self, bucket_name: str, object_name: str, **kwargs) -> bool:
        """
        Проверка на существование файла в хранилище
        :param bucket_name:     название bucket
        :param object_name:     название файла
        :param kwargs:          дополнительные параметры
        :return:                название файла
        """
        pass
