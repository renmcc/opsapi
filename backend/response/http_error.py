#!/usr/bin/env python
# coding:utf-8
# __time__: 2021/3/23 11:53
# __author__ = 'ren_mcc'
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from public.get_data_by_cache import get_current_user
from public.logger import logger


async def http_error_handler(request: Request, exc: HTTPException):
    """自定义http异常"""
    authorization: str = request.headers.get("Authorization")
    access_token = authorization.split(" ")[1] if authorization else None
    request_path = request.scope['path']
    user = get_current_user(request)
    user = user["account"] if user else None
    logger.error(
        {
            f"client:{request.scope['client'][0]}, url:{request_path}, user:{user}, token:{access_token}, detail:{exc.detail}"
        })
    headers = getattr(exc, "headers", None)
    if headers:
        return JSONResponse(
            {"detail": exc.detail}, status_code=exc.status_code, headers=headers
        )
    else:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """自定义请求体验证错误"""
    logger.error(f"{request.scope['client']}-{exc.errors()}")
    return JSONResponse({'status_code': status.HTTP_400_BAD_REQUEST, 'message': exc.errors()},
                        status_code=status.HTTP_400_BAD_REQUEST)
