from fastapi import APIRouter, Request, Depends, status, Query, HTTPException
from apps.system.model import SysDocWhileList, SysUser
from sqlalchemy.orm import Session
from sqlalchemy.orm import aliased
from sqlalchemy import desc
from apps.system.form import WhileRequestForm
from db.db_base import DbHandleBase
from fastapi.responses import JSONResponse
from public.oppose_crawler import backstage, pagination, check_perm
from public.data_utils import orm_all_to_dict, orm_one_to_dict
from public.get_data_by_cache import get_current_user
from apps.system.sys_auth import oauth2_scheme
from typing import Optional
from db.session import get_db
import ast
from db.db_caches import cache
from core import config
from public.str_utils import md5_encrypt

__author__ = 'ren_mcc'
router = APIRouter()


@router.post('/add-while', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="添加白名单",
             description="""
    添加白名单
    """)
async def add_while(request: Request, form: WhileRequestForm, db: Session = Depends(get_db)):
    # 如果ip已经存在退出
    if db.query(SysDocWhileList.id).filter(SysDocWhileList.while_ip == form.while_ip, SysDocWhileList.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ip已存在")

    # 添加角色到数据库
    user = get_current_user(request)
    db_role = SysDocWhileList()
    db_role.while_ip = form.while_ip
    db_role.remarks = form.remarks
    handle_db = DbHandleBase()
    handle_db.create(db, user, db_role)

    # TODO 清除缓存
    keys = cache.keys("while_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '添加白名单成功'}, status_code=status.HTTP_201_CREATED)


@router.put('/update-while', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="更新白名单",
            description="""
    更新白名单
    """)
async def update_role(request: Request, form: WhileRequestForm, db: Session = Depends(get_db)):
    # 如果角色不存在退出
    if not db.query(SysDocWhileList.id).filter(SysDocWhileList.while_ip == form.while_ip, SysDocWhileList.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ip不存在")

    # TODO 更新ip到数据库
    user = get_current_user(request)
    db_role = db.query(SysDocWhileList).filter(SysDocWhileList.while_ip == form.while_ip, SysDocWhileList.state == 1).first()
    db_role.remarks = form.remarks
    handle_db = DbHandleBase()
    handle_db.update(db, user, db_role)

    # TODO 清除缓存
    keys = cache.keys("while_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '更新白名单成功'}, status_code=status.HTTP_200_OK)


@router.delete('/del-while', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="删除白名单",
               description="""
    删除白名单
    """)
async def del_while(request: Request, db: Session = Depends(get_db),
                        while_id: Optional[int] = Query(..., ge=1, le=100, title="白名单id", description="白名单id")):
    # 如果白名单id不存在退出
    if not db.query(SysDocWhileList.id).filter(SysDocWhileList.id == while_id, SysDocWhileList.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="找不到该id信息或已删除")

    # TODO 删除角色
    user = get_current_user(request)
    handle_db = DbHandleBase()
    # 获取角色对象
    db_while = db.query(SysDocWhileList).filter(SysDocWhileList.id == while_id, SysDocWhileList.state == 1).first()
    handle_db.delete(db, user, db_while)
    # TODO 清除缓存
    keys = cache.keys("while_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '删除成功'}, status_code=status.HTTP_200_OK)


@router.get('/get-while', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="获取白名单",
            description="""
    获取白名单
    while_ip：白名单ip
    page：页码
    page_size：每页最大行数
    """)
async def get_role_list(request: Request, db: Session = Depends(get_db),
                        while_ip: Optional[str] = Query(None, min_length=2, max_length=20, title="白名单ip",
                                                         description="白名单ip"),
                        page: dict = Depends(pagination)):
    # 缓存key
    ch_key = "while_" + md5_encrypt(str(request.url))
    # TODO 如果有缓存读取缓存，没有读取mysql
    if cache.exists(ch_key):
        total = int(cache.lrange(ch_key, 0, 0)[0])
        ch_while = cache.lrange(ch_key, 1, -1)
        while_ip_list = [ast.literal_eval(x) for x in ch_while]
    else:
        if not hasattr(SysDocWhileList, page["order_id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的排序id")

        # 连表查询
        a = aliased(SysDocWhileList)
        b = aliased(SysUser)
        c = aliased(SysUser)
        db_while = db.query(a.id, a.while_ip, b.account.label("create_by_user"), a.create_time,
                           c.account.label("chage_by_user"), a.last_change_time, a.remarks).outerjoin(b,
                                                                                                      a.create_by_id == b.id).outerjoin(
            c,
            a.change_by_id == c.id).filter(
            a.state == 1)
        if while_ip:
            db_while = db_while.filter(a.while_ip == while_ip)
        # TODO 总的角色数
        total = db_while.count()
        # TODO 获取分页后的角色数据
        if page["desc"]:
            order = desc(getattr(a, page["order_id"]))
        else:
            order = getattr(a, page["order_id"])
        result = db_while.order_by(order).limit(page["page_size"]).offset(
            page["offset"]).all()
        while_ip_list = orm_all_to_dict(result)


        # 写入缓存
        ch_while_list = [str(x) for x in while_ip_list]
        if ch_while_list:
            cache.rpush(ch_key, *ch_while_list)
        cache.lpush(ch_key, total)
        cache.expire(ch_key, config.CH_TIMEOUT)

    return JSONResponse({"total": total, "detail": while_ip_list}, status_code=status.HTTP_200_OK)
