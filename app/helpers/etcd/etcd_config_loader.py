from tenacity import retry, stop_after_attempt, wait_exponential

from app.helpers.etcd.etcd_client import EtcdClient


def get_etcd_config(obj, config_key=None):
    etcd_service_client = EtcdClient(
        protocol=obj.ETCD.protocol,
        host=obj.ETCD.host,
        port=obj.ETCD.port,
        timeout=obj.ETCD.timeout,
    )
    config = etcd_service_client.get(key=config_key)
    return config


@retry(reraise=True, stop=stop_after_attempt(30), wait=wait_exponential(multiplier=1, min=2, max=60, exp_base=2))
def load(obj, env="default", silent=True, key=None, filename=None):
    try:
        config_root: str = obj.ETCD.root_key
        config_root = config_root.strip("/")
        config_key = f"/{config_root}/{obj.NAME}/{obj.VERSION}"
        config = get_etcd_config(obj, config_key)
        obj.set(key, config.get(key)) if key else obj.update(config)

    except Exception as error:  # pylint: disable=broad-except
        error_message = f"Ошибка инициализации настроек из etcd, по причине: {error}"
        raise ValueError(error_message)
