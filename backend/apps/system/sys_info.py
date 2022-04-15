#!/usr/bin/env python
# coding:utf-8
# __time__: 2021/2/22 12:59
# __author__ = 'ren_mcc'
import ast
from fastapi import APIRouter, Request, Depends, status, HTTPException
from fastapi.responses import JSONResponse
from core import config
from public.oppose_crawler import backstage, check_perm
from apps.system.sys_auth import oauth2_scheme
from public.logger import logger
from sqlalchemy.orm import Session
from db.session import get_db
from apps.system.model import SysApi
from public.data_utils import orm_all_to_dict
from db.db_base import DbHandleBase
from public.get_data_by_cache import get_current_user
from db.db_caches import cache
from core import config
import ast
from public.str_utils import md5_encrypt

router = APIRouter()


@router.get('/get-setting', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)],
            name="获取系统设置")
async def get_setting(request: Request):
    info = {'name': config.NAME, 'logo': config.LOGO,
            'header_img': config.HEADER_IMG}

    return JSONResponse({'detail': info}, status_code=status.HTTP_200_OK)


@router.get('/get-api', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="获取系统api",
            description="""
    获取系统api列表
""")
async def get_api(request: Request, db: Session = Depends(get_db)):
    # 缓存key
    ch_key = "api_" + md5_encrypt(str(request.url))
    if cache.exists(ch_key):
        total = int(cache.lrange(ch_key, 0, 0)[0])
        ch_api = cache.lrange(ch_key, 1, -1)
        api_list = [ast.literal_eval(x) for x in ch_api]
    else:
        db_api = db.query(SysApi.id, SysApi.name, SysApi.path, SysApi.name, SysApi.method, SysApi.create_time).filter(
            SysApi.state == 1, SysApi.path != '/api/system/auth/login', SysApi.path != '/api/system/auth/login-out')
        total = db_api.count()
        db_api = db_api.all()
        api_list = orm_all_to_dict(db_api)
        # 添加label字段
        for api in api_list:
            api["label"] = str(api["path"]) + " | " + str(api["name"])

        # 写入缓存
        ch_role_list = [str(x) for x in api_list]
        if ch_role_list:
            cache.rpush(ch_key, *ch_role_list)
        cache.lpush(ch_key, total)
        cache.expire(ch_key, config.CH_TIMEOUT)
    return JSONResponse({"total": total, "detail": api_list}, status_code=status.HTTP_200_OK)


@router.get('/reset-api', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="重置api",
            description="""
    重置api
""")
async def reset_api(request: Request, db: Session = Depends(get_db)):
    # 获取所有api路径
    api_paths = {route.path for route in request.app.router.routes}
    # 获取数据库api数据
    db_api = db.query(SysApi.path).filter(SysApi.state == 1).all()
    db_api_list = [x[0] for x in db_api]

    # 对比数据库数据取差集
    add_path_list = list(set(api_paths).difference(set(db_api_list)))
    del_path_list = list(set(db_api_list).difference(set(api_paths)))

    # 获取所有SysApi对象
    db_apis = []
    for route in request.app.router.routes:
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
    user = get_current_user(request)
    handle_db.batch_create(db, user, db_apis)

    # 删除过期的api数据
    db_api_del = db.query(SysApi).filter(SysApi.path.in_(del_path_list), SysApi.state == 1).all()
    handle_db.batch_delete(db, user, db_api_del)
    # TODO 清除缓存
    keys = cache.keys("api_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({"detail": "success"}, status_code=status.HTTP_200_OK)
