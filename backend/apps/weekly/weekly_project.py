#!/usr/bin/env python
# coding:utf-8
# __time__: 2021/4/7 10:31
# __author__ = 'ren_mcc'

from fastapi import APIRouter, Request, Depends, status, Query, HTTPException
from apps.weekly.model import weekly_project
from apps.system.model import SysUser
from apps.weekly.form import WeeklyProjectRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.orm import aliased
from sqlalchemy import desc
from db.db_base import DbHandleBase
from fastapi.responses import JSONResponse
from public.oppose_crawler import backstage, pagination, check_perm
from public.data_utils import orm_all_to_dict
from public.get_data_by_cache import get_current_user
from apps.system.sys_auth import oauth2_scheme
from typing import Optional
from db.session import get_db
import ast
from db.db_caches import cache
from core import config
from public.str_utils import md5_encrypt


router = APIRouter()


@router.post('/add-weekly-project', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="添加处理项目",
             description="""
    添加处理项目
    """)
async def add_weekly_project(request: Request, form: WeeklyProjectRequestForm, db: Session = Depends(get_db)):
    # 如果处理项目已经存在退出
    if db.query(weekly_project.id).filter(weekly_project.name == form.name, weekly_project.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="处理项目已经存在")

    # 添加角色到数据库
    user = get_current_user(request)
    db_weekly_project = weekly_project()
    db_weekly_project.name = form.name
    db_weekly_project.remarks = form.remarks
    handle_db = DbHandleBase()
    handle_db.create(db, user, db_weekly_project)

    # TODO 清除缓存
    keys = cache.keys("weeklyProject_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '添加处理项目成功'}, status_code=status.HTTP_201_CREATED)


@router.put('/update-weekly-project', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="更新处理项目",
            description="""
    更新处理项目
    """)
async def update_weekly_project(request: Request, form: WeeklyProjectRequestForm, db: Session = Depends(get_db)):
    # 如果处理项目不存在退出
    if not db.query(weekly_project.id).filter(weekly_project.name == form.name, weekly_project.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="处理项目不存在")

    # TODO 更新ip到数据库
    user = get_current_user(request)
    db_weekly_project = db.query(weekly_project).filter(weekly_project.name == form.name, weekly_project.state == 1).first()
    db_weekly_project.remarks = form.remarks
    handle_db = DbHandleBase()
    handle_db.update(db, user, db_weekly_project)

    # TODO 清除缓存
    keys = cache.keys("weeklyProject_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '更新处理项目成功'}, status_code=status.HTTP_200_OK)


@router.delete('/del-weekly-project', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="删除处理项目",
               description="""
    删除处理项目
    """)
async def del_weekly_project(request: Request, db: Session = Depends(get_db),
                        project_id: Optional[int] = Query(..., ge=1, le=100, title="处理项目id", description="处理项目id")):
    # 如果处理项目id不存在退出
    if not db.query(weekly_project.id).filter(weekly_project.id == project_id, weekly_project.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="找不到该id信息或已删除")

    # TODO 删除角色
    user = get_current_user(request)
    handle_db = DbHandleBase()
    # 获取角色对象
    db_weekly_project = db.query(weekly_project).filter(weekly_project.id == project_id, weekly_project.state == 1).first()
    handle_db.delete(db, user, db_weekly_project)
    # TODO 清除缓存
    keys = cache.keys("weeklyProject_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '删除成功'}, status_code=status.HTTP_200_OK)


@router.get('/get-weekly-project', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="获取处理项目",
            description="""
    获取处理项目
    name：处理项目名称
    page：页码
    page_size：每页最大行数
    """)
async def get_weekly_project(request: Request, db: Session = Depends(get_db),
                        project_name: Optional[str] = Query(None, min_length=2, max_length=20, title="处理项目名称",
                                                         description="处理项目名称"),
                        page: dict = Depends(pagination)):
    # 缓存key
    ch_key = "weeklyProject_" + md5_encrypt(str(request.url))
    # TODO 如果有缓存读取缓存，没有读取mysql
    if cache.exists(ch_key):
        total = int(cache.lrange(ch_key, 0, 0)[0])
        ch_while = cache.lrange(ch_key, 1, -1)
        weekly_project_list = [ast.literal_eval(x) for x in ch_while]
    else:
        if not hasattr(weekly_project, page["order_id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的排序id")

        # 连表查询
        a = aliased(weekly_project)
        b = aliased(SysUser)
        c = aliased(SysUser)
        db_weekly_project = db.query(a.id, a.name, a.remarks, b.account.label("create_by_user"), a.create_time,
                           c.account.label("chage_by_user"), a.last_change_time, a.remarks).outerjoin(b,
                                                                                                      a.create_by_id == b.id).outerjoin(
            c,
            a.change_by_id == c.id).filter(
            a.state == 1)
        if project_name:
            db_weekly_project = db_weekly_project.filter(a.name == project_name)
        # TODO 总的角色数
        total = db_weekly_project.count()
        # TODO 获取分页后的角色数据
        if page["desc"]:
            order = desc(getattr(a, page["order_id"]))
        else:
            order = getattr(a, page["order_id"])
        result = db_weekly_project.order_by(order).limit(page["page_size"]).offset(
            page["offset"]).all()
        weekly_project_list = orm_all_to_dict(result)


        # 写入缓存
        ch_while_list = [str(x) for x in weekly_project_list]
        if ch_while_list:
            cache.rpush(ch_key, *ch_while_list)
        cache.lpush(ch_key, total)
        cache.expire(ch_key, config.CH_TIMEOUT)

    return JSONResponse({"total": total, "detail": weekly_project_list}, status_code=status.HTTP_200_OK)
