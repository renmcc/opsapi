#!/usr/bin/env python
# coding:utf-8
# __time__: 2021/3/23 12:55
# __author__ = 'ren_mcc'

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.cors import CORSMiddleware
from core.config import CORS_ORIGINS, CORS_ALLOW_CREDENTIALS, CORS_ALLOW_HEADERS, CORS_ALLOW_METHODS, ALLOW_HOSTS, DOC_URL
from starlette.responses import PlainTextResponse
from db.session import SessionLocal
from sqlalchemy.orm import Session
from apps.system.model import SysDocWhileList
from public.logger import logger
from public.get_data_by_cache import get_current_user


def init_middlewares(app: FastAPI):
    """
    初始化中间件
    :param app: FastAPI
    :return: response
    """
    # 跨域
    app.add_middleware(CORSMiddleware,
                       allow_origins=CORS_ORIGINS,
                       allow_credentials=CORS_ALLOW_CREDENTIALS,
                       allow_methods=CORS_ALLOW_METHODS,
                       allow_headers=CORS_ALLOW_HEADERS)
    # 设置允许访问的主机
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOW_HOSTS)

    # 响应体压缩
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    @app.middleware('http')
    async def session_middleware(request: Request, call_text):
        response = await call_text(request)
        request_uri = request.scope["path"] if request.scope and request["path"] else ''
        # 限制doc访问
        if request_uri == DOC_URL:
            client_ip = request.scope['client'][0] if request.scope and request.scope['client'] else ''
            user = get_current_user(request)
            user = user["account"] if user else None
            authorization: str = request.headers.get("Authorization")
            access_token = authorization.split(" ")[1] if authorization else None

            # 从数据库获取放行ip
            while_ip = ["*", client_ip]
            db: Session = SessionLocal()
            db_doc_while_list = db.query(SysDocWhileList.id).filter(SysDocWhileList.while_ip.in_(while_ip),
                                                SysDocWhileList.state == 1).count()
            db.close()
            if db_doc_while_list > 0:
                pass
            else:
                logger.error(
                    {
                        f"client:{request.scope['client'][0]}, url:{request_uri}, user:{user}, token:{access_token}, detail:访问拒绝"
                    })
                response = PlainTextResponse("访问拒绝", status_code=400)

        return response
