#!/usr/bin/env python
# coding:utf-8
# __time__: 2021/3/23 11:27
# __author__ = 'ren_mcc'

from fastapi import FastAPI
from typing import Callable
from aioredis import create_redis_pool
import databases
from core import config
from db.session import SessionLocal
from db.db_base import DbHandleBase
from apps.system.model import SysApi


db_url = config.DB_CONN_URI.replace("+pymysql", "") + "&min_size=10&max_size=100"
database = databases.Database(db_url)


def start_init_db_handler(app: FastAPI) -> Callable:
    """
    FastApi 启动完成事件
    :param app: FastAPI
    :return: start_app
    """
    async def init_db():
        app.state.redis = await create_redis_pool(address=f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}",
                                                  db=config.REDIS_DB,
                                                  encoding="utf8",
                                                  minsize=10, maxsize=100)

        await database.connect()
        app.state.mysql = database
    return init_db


def stop_shutdown_db_handler(app: FastAPI) -> Callable:
    """
    FastApi 停止事件
    :param app: FastAPI
    :return: stop_app
    """
    async def shutdown_db():
        app.state.redis.close()
        await app.state.redis.wait_closed()
        await database.disconnect()
    return shutdown_db


def start_init_sys_api_handler(app: FastAPI) -> Callable:
    """
    FastApi 启动完成事件
    :param app: FastAPI
    :return: start_app
    """
    async def init_sys_api() -> None:
        """启动前执行"""
        db = SessionLocal()

        # 获取所有api路径
        api_paths = {route.path for route in app.router.routes}
        # 获取数据库api数据
        db_api = db.query(SysApi.path).filter(SysApi.state == 1).all()
        db_api_list = [x[0] for x in db_api]

        # 对比数据库数据取差集
        add_path_list = list(set(api_paths).difference(set(db_api_list)))
        del_path_list = list(set(db_api_list).difference(set(api_paths)))

        # 获取所有SysApi对象
        db_apis = []
        for route in app.router.routes:
            if route.path in add_path_list:
                db_api = SysApi()
                db_api.path = route.path
                try:
                    db_api.method = ",".join(route.methods)
                except Exception:
                    db_api.method = None
                db_api.name = route.name
                db_apis.append(db_api)
        # 添加到数据库
        handle_db = DbHandleBase()
        handle_db.batch_create(db, None, db_apis)

        # 删除过期的api数据
        db_api_del = db.query(SysApi).filter(SysApi.path.in_(del_path_list), SysApi.state == 1).all()
        handle_db.batch_delete(db, None, db_api_del)
    return init_sys_api






