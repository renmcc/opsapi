from redis import Redis, ConnectionPool
from core import config

__author__ = 'ren_mcc'


class Cache:
    _client = None

    @classmethod
    def client(cls):
        """
        单例模式获取连接
        """
        if cls._client:
            return cls._client
        else:
            pool = ConnectionPool(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB,
                                  decode_responses=True, max_connections=10000)
            cls._client = Redis(connection_pool=pool)
        return cls._client


cache = Cache().client()
# 设置默认时间
# cache.expire(cache_key, time(单位秒))
# cache.set(cache_key, value, time(时间秒))
