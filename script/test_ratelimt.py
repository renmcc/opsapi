#!/usr/bin/env python
#coding:utf-8
#__time__: 2021/4/6 18:21
#__author__ = 'ren_mcc'

import asyncio
import time

from ratelimiter import RateLimiter


async def limited(until):
    duration = int(round(until - time.time()))
    print('Rate limited, sleeping for {:d} seconds'.format(duration))


async def coro():
    rate_limiter = RateLimiter(max_calls=2, period=3, callback=limited)
    for i in range(3):
        async with rate_limiter:
            print('Iteration', i)


loop = asyncio.get_event_loop()
loop.run_until_complete(coro())