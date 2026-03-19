import redis
from django.conf import settings


def get_redis_connection(db: int = 0) -> redis.Redis:
    """
    获取 Redis 连接，统一从 Django settings.REDIS_CONFIG 读取配置。
    默认使用 db=0，如需其他库可通过参数指定。
    """
    config = getattr(settings, "REDIS_CONFIG", {})
    host = config.get("host", "localhost")
    port = config.get("port", 6379)
    password = config.get("password")

    return redis.Redis(host=host, port=port, db=db, password=password)

