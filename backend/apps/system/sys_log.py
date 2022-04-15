from fastapi import APIRouter, Request, Depends, status, Query, HTTPException
from typing import Optional
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from public.oppose_crawler import backstage, pagination, check_perm
from apps.system.model import SysLoginLog as Login, SysOperationLog as Ope
from public.data_utils import orm_all_to_dict
from apps.system.sys_auth import oauth2_scheme
from db.session import get_db
from datetime import datetime
from core import config

__author__ = 'ren_mcc'
router = APIRouter()


@router.get('/login-log', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="登录日志列表", description="""
    登录日志列表
    "account": 账号
    "time_start": 开始时间
    "time_end": 结束时间
    """)
async def login_log(request: Request, db: Session = Depends(get_db), page: dict = Depends(pagination),
                    account: Optional[str] = Query(None, min_length=2, max_length=10, title="账号", description="账号"),
                    time_start: Optional[datetime] = Query(None, title="起始时间", description="起始时间"),
                    time_end: Optional[datetime] = Query(None, title="结束时间", description="结束时间")):
    if not hasattr(Login, page["order_id"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的排序id")

    db_log = db.query(Login.id, Login.account, Login.user_name, Login.login_ip, Login.is_success,
                      Login.access_token, Login.create_time,
                      Login.browser).filter(Login.state == 1)
    if account:
        db_log = db_log.filter(Login.account == account)
    if time_start:
        db_log = db_log.filter(Login.create_time >= time_start)
    if time_end:
        db_log = db_log.filter(Login.create_time <= time_end)
    total = db_log.count()
    orm_logs = db_log.order_by(page["order_by"]).limit(page["page_size"]).offset(page["offset"]).all()

    login_log_list = orm_all_to_dict(orm_logs)
    return JSONResponse({"total": total, "detail": login_log_list}, status_code=status.HTTP_200_OK)


@router.get('/operate-log', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="操作日志列表", description="""
    操作日志列表
    "account": 账号
    "time_start": 开始时间
    "time_end": 结束时间
    """)
async def operate_log(request: Request, db: Session = Depends(get_db), page: dict = Depends(pagination),
                      account: Optional[str] = Query(None, min_length=2, max_length=10, title="账号", description="账号"),
                      time_start: Optional[datetime] = Query(None, title="起始时间", description="起始时间"),
                      time_end: Optional[datetime] = Query(None, title="结束时间", description="结束时间")):
    if not hasattr(Ope, page["order_id"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的排序id")

    db_log = db.query(Ope.id, Ope.account, Ope.ip, Ope.access_token, Ope.create_time, Ope.operation_url,
                      Ope.request_body,
                      Ope.browser).filter(Ope.state == 1)
    if account:
        db_log = db_log.filter(Ope.account == account)
    if time_start:
        db_log = db_log.filter(Ope.create_time >= time_start)
    if time_end:
        db_log = db_log.filter(Ope.create_time <= time_end)
    total = db_log.count()
    orm_logs = db_log.order_by(page["order_by"]).limit(page["page_size"]).offset(page["offset"]).all()
    operate_log_list = orm_all_to_dict(orm_logs)
    return JSONResponse({"total": total, "detail": operate_log_list}, status_code=status.HTTP_200_OK)
