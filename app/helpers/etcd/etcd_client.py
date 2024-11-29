import base64
import re
from typing import Generator, Union

import requests


class EtcdClient:
    DIR_VALUE = "etcdv3_dir_$2H#%gRe3*t"
    DIR_RE_EXP = re.compile(r"\S*etcdv3_dir_\S*")

    def __init__(
        self,
        protocol: str,
        host: str,
        port: Union[int, str],
        timeout: int = 30,
    ):
        """
        Клиент для подключения к http сервисам
        :param protocol:                протокол
        :param host:                    хост
        :param port:                    порт
        :param timeout:                 таймаут в секундах
        """
        self.protocol = protocol
        self.host = host
        self.port = port
        self.timeout = timeout
        self.session = requests.session()

    @property
    def url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    def put(self, key: str, value: str, endpoint: str = "v3/kv/put") -> dict:
        for folder in self.get_folders(path=key):
            self._put(key=folder, value=EtcdClient.DIR_VALUE, endpoint=endpoint)
        response = self._put(key=key, value=value, endpoint=endpoint)
        return response

    def _put(self, key: str, value: str, endpoint: str) -> dict:
        data = {
            "key": self.b64_encode_data(key.encode()),
            "value": self.b64_encode_data(value.encode()),
        }
        response = self.session.post(f"{self.url}/{endpoint}", json=data, timeout=self.timeout)
        response = response.json()
        return response

    def get(self, key: str, endpoint: str = "v3/kv/range") -> dict:
        if not key:
            raise ValueError("Не указан ключ")
        nested_length = len(key.strip("/").split("/"))
        data = {
            "key": self.b64_encode_data(key.encode()),
            "range_end": self.b64_encode_data(self.increment_last_byte(key.encode())),
        }
        response = self.session.post(f"{self.url}/{endpoint}", json=data, timeout=self.timeout)
        response = response.json()

        response = self.serializer(response=response, nested_length=nested_length)
        return response

    @staticmethod
    def get_folders(path: str) -> Generator[str, None, None]:
        folders = path.split("/")
        nested_folder = "/"
        for folder in folders:
            nested_folder = "".join([nested_folder, folder])
            yield nested_folder
            nested_folder = "".join([nested_folder, "/"])

    @staticmethod
    def b64_encode_data(data: bytes) -> str:
        data = base64.b64encode(data)
        data = data.decode()
        return data

    @staticmethod
    def increment_last_byte(byte_string: bytes) -> bytes:
        s = bytearray(byte_string)
        s[-1] = s[-1] + 1
        return bytes(s)

    @staticmethod
    def b64_decode_data(data: str) -> str:
        data = base64.b64decode(data)
        data = data.decode()
        return data

    @staticmethod
    def serializer(response: dict, nested_length: int) -> list[str]:
        data = {}
        kvs = response.get("kvs")
        if kvs is None:
            return data
        for kv in kvs:
            key = EtcdClient.b64_decode_data(kv["key"])
            value = EtcdClient.b64_decode_data(kv["value"])
            if re.findall(EtcdClient.DIR_RE_EXP, value):
                continue
            key = key.split("/")
            key = "/".join(key[nested_length + 1 :])
            if not key:
                continue
            data.update({key: value})

        return data
