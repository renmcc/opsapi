from fastapi import Request, HTTPException, status, Query, Depends, BackgroundTasks
import ast
from db.db_caches import cache
from sqlalchemy.orm import Session
from db.db_base import DbHandleBase
from apps.system.model import SysOperationLog
from public.get_data_by_cache import get_current_user
from public.logger import logger
from typing import Optional
from core import config
from db.session import get_db
from sqlalchemy import text
from apps.system.model import SysApi, SysRolePermission

__author__ = 'ren_mcc'


async def backstage(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """登录拦截器"""
    try:
        request_body = await request.json() if await request.body() else {}
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise Exception("未登录")

        access_token = authorization.split(" ")[1] if authorization else None
        token_value = cache.get(access_token)
        token_value = token_value if token_value else None
        if not token_value:
            raise Exception("token失效，请重新登录")

        client_ip = request.scope['client'][0] if request.scope and request.scope['client'] else ''
        user_agent = request.headers.get("User-Agent")
        # 转化成字典
        token_value = ast.literal_eval(token_value)
        if token_value["login_ip"] != client_ip or token_value["browser"] != user_agent:
            raise Exception("无效的token,请重新登录")
        # 记录操作
        # background_tasks.add_task(operation_log, request, request_body, db)
        operation_log(request, request_body, db)
    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


async def check_perm(request: Request, db: Session = Depends(get_db)):
    """
    权限检查拦截器
    """
    user = get_current_user(request)
    super_user = user["is_super"]
    # 超级用户不校验权限
    if super_user:
        return
    try:
        user_roles = user["roles"] if user else []
        role_ids = [x["id"] for x in user_roles]
    except Exception as e:
        logger.error(e)
        role_ids = []
    db_api = db.query(SysApi.path).filter(SysApi.state == 1, SysApi.id.in_(
        db.query(SysRolePermission.api_id).filter(SysRolePermission.state == 1,
                                                  SysRolePermission.role_id.in_(role_ids)))).all()
    db_api_list = [x[0] for x in db_api]
    request_uri = request.scope["path"]
    # 没有权限抛异常
    if request_uri not in db_api_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权限访问")


def operation_log(request: Request, request_body, db: Session):
    """
    记录操作日志
    """
    try:
        referer: int = 1 if request.headers.get("Referer") else 0
        authorization: str = request.headers.get("Authorization")
        access_token = authorization.split(" ")[1] if authorization else None
        user = get_current_user(request)
        operation_log = SysOperationLog()
        operation_log.operation_url = str(request.url)
        operation_log.ip = request.scope['client'][0]
        operation_log.is_doc = referer
        operation_log.browser = request.headers.get("User-Agent")
        operation_log.access_token = access_token
        operation_log.account = user['account'] if user else None
        operation_log.request_body = request_body
        db_handle = DbHandleBase()
        db_handle.create(db, user, operation_log)
    except Exception as e:
        logger.error(e)


async def pagination(page: Optional[int] = Query(1, ge=1, le=1000, title="页码"),
                     page_size: Optional[int] = Query(config.PAGE_SIZE, ge=1, le=10000, title="每页最大行数"),
                     order_by: Optional[str] = Query('id', min_length=1, max_length=20, title='排序')):
    """
    分页
    """
    # 用于连表查询
    if order_by.startswith("-"):
        order_id = order_by[1:]
        desc = True
    else:
        order_id = order_by
        desc = False

    order_by = text(order_by)
    offset = (page - 1) * page_size
    return {"page_size": page_size, "offset": offset, "order_by": order_by, "order_id": order_id, "desc": desc}
