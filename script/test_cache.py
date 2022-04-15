#!/usr/bin/env python
# coding:utf-8
# __time__: 2021/3/22 14:31
# __author__ = 'ren_mcc'


import asyncio

from aiocache import caches, Cache

caches.set_config({
    'default': {
        'cache': "aiocache.SimpleMemoryCache",
        'serializer': {
            'class': "aiocache.serializers.StringSerializer"
        }
    },
    'redis_alt': {
        'cache': "aiocache.RedisCache",
        'endpoint': "192.168.20.10",
        'db': 9,
        'port': 6379,
        'timeout': 100,
        'serializer': {
            'class': "aiocache.serializers.JsonSerializer"
        }
    }
})


async def alt_cache():
    cache = caches.create(**caches.get_alias_config('default'))
    l1 = [1, 2, 23, 4, 5, 65]
    key = 0
    while True:
        await cache.set(key, l1, ttl=1000)
        abc = await cache.get(key)
        print(abc)
        timeout = await cache.ttl(key)
        print(timeout)
        key += 1



    # await cache.close()


if __name__ == "__main__":
    asyncio.run(alt_cache())
