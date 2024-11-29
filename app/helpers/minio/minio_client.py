import logging
import os
from asyncio import to_thread
from typing import AsyncGenerator, Iterator, Union

import certifi
from minio import Minio, S3Error
from minio.commonconfig import Tags
from minio.helpers import MIN_PART_SIZE
from urllib3 import HTTPResponse, PoolManager, Retry, Timeout

from app.helpers.exceptions import ObjectNotFound, OutDiskSpace
from app.helpers.interfaces import FileHostingClientAbc, FileReaderProtocol
from app.helpers.minio.error_codes import (
    MINIO_QUOTA_FULL,
    MINIO_STORAGE_FULL,
    NO_SUCH_BUCKET,
    NO_SUCH_FILE,
)


class MinioClient(FileHostingClientAbc):
    def __init__(
        self,
        protocol: str,
        host: str,
        port: Union[str, int],
        access_key: str,
        secret_key: str,
        region: str,
        chunk_size: int = 1024,
        timeout=300,
        pool_max_size=30,
        cert_check=True,
        retry_count=5,
        logger: logging.Logger = None,
    ):
        self.chunk_size = chunk_size
        self.logger = logger or logging
        self.client = Minio(
            endpoint=f"{host}:{port}",
            secure=True if protocol == "https" else False,
            access_key=access_key,
            secret_key=secret_key,
            region=region,
            http_client=PoolManager(
                timeout=Timeout(connect=timeout, read=timeout),
                maxsize=pool_max_size,
                cert_reqs="CERT_REQUIRED" if cert_check else "CERT_NONE",
                ca_certs=os.environ.get("SSL_CERT_FILE") or certifi.where(),
                retries=Retry(total=retry_count, backoff_factor=0.2, status_forcelist=[500, 502, 503, 504]),
            ),
        )

    async def upload_file(self, bucket_name: str, object_name: str, data: FileReaderProtocol, **kwargs) -> str:
        self.logger.debug("Загрузка файла %s в bucket %s...", object_name, bucket_name)
        length = kwargs.pop("length", -1)
        kwargs["part_size"] = MIN_PART_SIZE if length == -1 else 0
        minio_tags = Tags(for_object=True)
        if tags := kwargs.pop("tags", {}):
            minio_tags.update(**tags)
        try:
            response = await to_thread(
                self.client.put_object,
                bucket_name=bucket_name,
                object_name=object_name,
                data=data,
                length=length,
                tags=minio_tags,
                **kwargs,
            )
        except S3Error as error:
            if error.code == NO_SUCH_BUCKET:
                self.logger.warning("Не найден bucket %s...", bucket_name)
                await to_thread(self.client.make_bucket, bucket_name=bucket_name)
                self.logger.info("Bucket %s успешно создан", bucket_name)
                return await self.upload_file(bucket_name, object_name, data, **kwargs)
            if error.code == MINIO_STORAGE_FULL:
                raise OutDiskSpace("Закончилось место на диске")
            if error.code == MINIO_QUOTA_FULL:
                raise OutDiskSpace(f"Закончилось выделенное место в bucket: {bucket_name} ")
            raise error
        self.logger.debug("Загрузка файла %s в bucket %s прошла успешно", object_name, bucket_name)
        return response.object_name

    async def download_file_raw(self, bucket_name, object_name, **kwargs) -> HTTPResponse:
        """
        Загрузка файла из minio
        :param bucket_name:     название bucket
        :param object_name:     название файла
        :param kwargs:          дополнительные параметры
        :return:                HTTPResponse
        """
        self.logger.debug("Загрузка файла %s из bucket %s...", object_name, bucket_name)
        try:
            response = await to_thread(
                self.client.get_object,
                bucket_name=bucket_name,
                object_name=object_name,
                **kwargs,
            )
        except S3Error as error:
            if error.code == NO_SUCH_FILE:
                raise ObjectNotFound("Файл с таким именем не найден")
            raise error
        self.logger.debug("Загрузка файла %s из bucket %s прошла успешно", object_name, bucket_name)
        return response

    async def download_file(self, bucket_name, object_name, **kwargs) -> bytes:
        response = None
        try:
            response = await self.download_file_raw(bucket_name=bucket_name, object_name=object_name, **kwargs)
            return response.data
        finally:
            if response:
                response.close()
                response.release_conn()

    async def download_file_chunk(self, bucket_name, object_name, **kwargs) -> AsyncGenerator:
        response = None
        offset = 0
        try:
            while True:
                response = await self.download_file_raw(
                    bucket_name=bucket_name,
                    object_name=object_name,
                    length=self.chunk_size,
                    offset=offset,
                    **kwargs,
                )
                offset += self.chunk_size
                yield response.data
                if len(response.data) < self.chunk_size:
                    break
        finally:
            if response:
                response.close()
                response.release_conn()

    async def delete_object(self, bucket_name: str, object_name: str, **kwargs) -> None:
        await to_thread(self.client.remove_object, bucket_name=bucket_name, object_name=object_name, **kwargs)

    async def get_list_objects(self, bucket_name: str, **kwargs) -> Iterator:
        return await to_thread(self.client.list_objects, bucket_name=bucket_name, **kwargs)

    async def check_file_exist(self, bucket_name: str, object_name: str, **kwargs) -> bool:
        try:
            await to_thread(
                self.client.stat_object,
                bucket_name=bucket_name,
                object_name=object_name,
                **kwargs,
            )
        except S3Error as error:
            if error.code in (NO_SUCH_FILE, NO_SUCH_BUCKET):
                return False
            raise error
        return True
