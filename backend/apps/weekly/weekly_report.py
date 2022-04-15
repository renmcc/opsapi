#!/usr/bin/env python
# coding:utf-8
# __time__: 2021/4/7 10:31
# __author__ = 'ren_mcc'

from fastapi import APIRouter, Request, Depends, status, Query, HTTPException
from datetime import datetime
from apps.weekly.model import weekly_project, weekly_type, weekly_report
from apps.system.model import SysUser
from apps.weekly.form import WeeklyReportRequestForm, WeeklyReportUpdateRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.orm import aliased
from sqlalchemy import desc
from db.db_base import DbHandleBase
from fastapi.responses import JSONResponse
from public.oppose_crawler import backstage, pagination, check_perm
from public.data_utils import orm_all_to_dict
from public.get_data_by_cache import get_current_user
from apps.system.sys_auth import oauth2_scheme
from typing import Optional, List
from db.session import get_db
import ast
from db.db_caches import cache
from core import config
from public.str_utils import md5_encrypt

router = APIRouter()


@router.post('/add-weekly-report', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)],
             name="添加周报",
             description="""
    添加周报
    """)
async def add_weekly_report(request: Request, form: WeeklyReportRequestForm, db: Session = Depends(get_db)):
    # 添加角色到数据库
    user = get_current_user(request)
    db_weekly_report = weekly_report()
    db_weekly_report.start_time = form.start_time
    if form.type_id:
        db_weekly_report.type_id = form.type_id
    db_weekly_report.applicant = form.applicant
    if form.project_id:
        db_weekly_report.project_id = form.project_id
    db_weekly_report.operation_text = form.operation_text
    db_weekly_report.result = form.result
    handle_db = DbHandleBase()
    handle_db.create(db, user, db_weekly_report)

    # TODO 清除缓存
    keys = cache.keys("weeklyReport_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '添加周报成功'}, status_code=status.HTTP_201_CREATED)


@router.post('/add-weekly-reports', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)],
             name="批量添加周报",
             description="""
    批量添加周报
    """)
async def add_weekly_reports(request: Request, formList: List[WeeklyReportRequestForm], db: Session = Depends(get_db)):
    # 添加角色到数据库
    user = get_current_user(request)
    db_weekly_list = []
    for form in formList:
        db_weekly_report = weekly_report()
        db_weekly_report.start_time = form.start_time
        db_weekly_report.type_id = form.type_id
        db_weekly_report.applicant = form.applicant
        db_weekly_report.project_id = form.project_id
        db_weekly_report.operation_text = form.operation_text
        db_weekly_report.result = form.result
        db_weekly_list.append(db_weekly_report)
    handle_db = DbHandleBase()
    handle_db.batch_create(db, user, db_weekly_list)

    # TODO 清除缓存
    keys = cache.keys("weeklyReport_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '添加周报成功'}, status_code=status.HTTP_201_CREATED)


@router.put('/update-weekly-report', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)],
            name="更新周报",
            description="""
    更新周报
    """)
async def update_weekly_report(request: Request, form: WeeklyReportUpdateRequestForm, db: Session = Depends(get_db)):
    # 如果周报不存在退出
    if not db.query(weekly_report.id).filter(weekly_report.id == form.id, weekly_report.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="周报不存在")

    # TODO 更新ip到数据库
    user = get_current_user(request)
    db_weekly_report = db.query(weekly_report).filter(weekly_report.id == form.id, weekly_report.state == 1).first()
    db_weekly_report.start_time = form.start_time
    db_weekly_report.type_id = form.type_id
    db_weekly_report.applicant = form.applicant
    db_weekly_report.project_id = form.project_id
    db_weekly_report.operation_text = form.operation_text
    db_weekly_report.result = form.result
    handle_db = DbHandleBase()
    handle_db.update(db, user, db_weekly_report)

    # TODO 清除缓存
    keys = cache.keys("weeklyReport_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '更新周报成功'}, status_code=status.HTTP_200_OK)


@router.delete('/del-weekly-report', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)],
               name="删除周报",
               description="""
    删除周报
    """)
async def del_weekly_report(request: Request, db: Session = Depends(get_db),
                            report_id: Optional[int] = Query(..., ge=1, title="周报id", description="周报id")):
    # 如果周报id不存在退出
    if not db.query(weekly_report.id).filter(weekly_report.id == report_id, weekly_report.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="找不到该id信息或已删除")

    # TODO 删除角色
    user = get_current_user(request)
    handle_db = DbHandleBase()
    # 获取角色对象
    db_weekly_report = db.query(weekly_report).filter(weekly_report.id == report_id, weekly_report.state == 1).first()
    handle_db.delete(db, user, db_weekly_report)
    # TODO 清除缓存
    keys = cache.keys("weeklyReport_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '删除成功'}, status_code=status.HTTP_200_OK)


@router.get('/get-weekly-report', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)],
            name="获取周报",
            description="""
    获取周报
    name：周报名称
    page：页码
    page_size：每页最大行数
    """)
async def get_weekly_report(request: Request, db: Session = Depends(get_db),
                            creater: Optional[str] = Query(None, min_length=2, max_length=10, title="创建者", description="创建者"),
                            create_start_time: Optional[datetime] = Query(None, title="创建时间", description="创建时间"),
                            create_end_time: Optional[datetime] = Query(None, title="结束时间", description="结束时间"),
                            start_time: Optional[datetime] = Query(None, title="操作开始时间", description="操作开始时间"),
                            end_time: Optional[datetime] = Query(None, title="结束时间", description="结束时间"),
                            applicant: Optional[str] = Query(None, min_length=2, max_length=10, title="申请人", description="申请人"),
                            page: dict = Depends(pagination)):
    # 缓存key
    user = get_current_user(request)
    ch_key = "weeklyReport_" + md5_encrypt(str(request.url)) + user['account']
    # TODO 如果有缓存读取缓存，没有读取mysql
    if cache.exists(ch_key):
        total = int(cache.lrange(ch_key, 0, 0)[0])
        ch_while = cache.lrange(ch_key, 1, -1)
        weekly_report_list = [ast.literal_eval(x) for x in ch_while]
    else:
        if not hasattr(weekly_report, page["order_id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的排序id")

        # 连表查询
        a = aliased(weekly_report)
        b = aliased(SysUser)
        c = aliased(SysUser)
        d = aliased(weekly_type)
        e = aliased(weekly_project)
        db_weekly_report = db.query(a.id, a.start_time, d.name.label("weekly_type"), a.applicant, e.name.label("weekly_project"), a.operation_text,
                                    a.result, b.account.label("create_by_user"), a.create_time,
                                    c.account.label("chage_by_user"), a.last_change_time).outerjoin(b,
                                                                                                               a.create_by_id == b.id).outerjoin(
            c, a.change_by_id == c.id).outerjoin(d, a.type_id == d.id).outerjoin(e, a.project_id == e.id).filter(a.state == 1)

        # TODO 过滤创建者
        if creater:
            db_weekly_report = db_weekly_report.filter(b.account == creater)

        # TODO 过滤申请人
        if applicant:
            db_weekly_report = db_weekly_report.filter(a.applicant == applicant)

        # TODO 过滤创建时间
        if create_start_time:
            db_weekly_report = db_weekly_report.filter(a.create_time >= create_start_time)
        if create_end_time:
            db_weekly_report = db_weekly_report.filter(a.create_time <= create_end_time)

        # TODO 过滤操作开始时间
        if start_time:
            db_weekly_report = db_weekly_report.filter(a.start_time >= start_time)
        if end_time:
            db_weekly_report = db_weekly_report.filter(a.start_time <= end_time)

        # TODO 不是超级管理员，只能看到自己的奏报
        if not user["is_super"]:
            db_weekly_report = db_weekly_report.filter(b.account == user['account'])

        # TODO 总的角色数
        total = db_weekly_report.count()
        # TODO 获取分页后的角色数据
        if page["desc"]:
            order = desc(getattr(a, page["order_id"]))
        else:
            order = getattr(a, page["order_id"])
        result = db_weekly_report.order_by(order).limit(page["page_size"]).offset(
            page["offset"]).all()
        weekly_report_list = orm_all_to_dict(result)

        # 写入缓存
        ch_while_list = [str(x) for x in weekly_report_list]
        if ch_while_list:
            cache.rpush(ch_key, *ch_while_list)
        cache.lpush(ch_key, total)
        cache.expire(ch_key, config.CH_TIMEOUT)

    return JSONResponse({"total": total, "detail": weekly_report_list}, status_code=status.HTTP_200_OK)
