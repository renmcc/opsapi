from fastapi import APIRouter, Request, Depends, status, HTTPException, Query
from typing import Optional
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from public.logger import logger
from db.db_base import DbHandleBase
from apps.system.model import SysUser, SysRole
from apps.system.form import UserRequestForm, UserUpdateForm, UserDeleteForm, RestPasswdForm, RestSelfPasswdForm, \
    SelfUpdateForm
from public.str_utils import encrypt_password
from apps.system.sys_auth import oauth2_scheme
from public.oppose_crawler import backstage, pagination, check_perm
from public.get_data_by_cache import get_token_key, get_current_user
from public.data_utils import orm_one_to_dict, orm_all_to_dict
from db.session import get_db
import ast
from db.db_caches import cache
from core import config
from public.str_utils import md5_encrypt
import time

__author__ = 'ren_mcc'
router = APIRouter()


@router.post('/add-user', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="添加用户",
             description="""
    添加用户
    "account": 账号
    "password": 密码
    "user_name": 用户名
    "phone": 手机号
    "email": 邮箱
    "roles": 角色id列表
    "remarks": 备注
    """)
async def add_user(request: Request, form: UserRequestForm, db: Session = Depends(get_db)):
    # 判断用户是否存在
    if db.query(SysUser.id).filter(SysUser.account == form.account, SysUser.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户已存在")

    # 角色id有误退出
    db_roles = db.query(SysRole.id).filter(SysRole.id.in_(form.roles), SysRole.state == 1).count()
    if db_roles != len(form.roles):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色id有误")

    # 获取有效的角色id
    db_role = db.query(SysRole.id, SysRole.role_name).filter(SysRole.id.in_(form.roles), SysRole.state == 1).all()
    db_role_list = orm_all_to_dict(db_role)

    # 添加用户到数据库
    user = get_current_user(request)
    db_user = SysUser()
    db_user.account = form.account
    db_user.password = encrypt_password(form.password, form.account)
    db_user.user_name = form.user_name
    db_user.is_super = form.is_super
    db_user.phone = form.phone
    db_user.email = form.email
    db_user.roles = db_role_list
    db_user.remarks = form.remarks
    handle_db = DbHandleBase()
    handle_db.create(db, user, db_user)

    # TODO 清除缓存
    keys = cache.keys("user_*")
    if keys:
        cache.delete(*keys)

    return JSONResponse({'detail': '创建用户成功'}, status_code=status.HTTP_201_CREATED)


@router.put('/update-user', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)],
            name="更新用户信息", description="""
    更新用户信息
    "account": 账号
    "user_name": 用户名
    "phone": 手机号
    "email": 邮箱
    "roles": 角色id列表
    "remarks": 备注
    """)
async def update_user(request: Request, form: UserRequestForm, db: Session = Depends(get_db)):
    # 判断用户是否存在
    if not db.query(SysUser.id).filter(SysUser.account == form.account, SysUser.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户不存在或已经删除")

    # 角色id有误退出
    db_roles = db.query(SysRole.id).filter(SysRole.id.in_(form.roles), SysRole.state == 1).count()
    if db_roles != len(form.roles):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色id有误")

    # 获取有效的角色id
    db_role = db.query(SysRole.id, SysRole.role_name).filter(SysRole.id.in_(form.roles), SysRole.state == 1).all()
    db_role_list = orm_all_to_dict(db_role)

    # 更新用户信息
    user = get_current_user(request)
    db_user = db.query(SysUser).filter(SysUser.account == form.account, SysUser.state == 1).first()
    db_user.user_name = form.user_name
    db_user.password = encrypt_password(form.password, form.account)
    db_user.is_super = form.is_super
    db_user.phone = form.phone
    db_user.email = form.email
    db_user.roles = db_role_list
    db_user.remarks = form.remarks
    handle_db = DbHandleBase()
    handle_db.update(db, user, db_user)

    # TODO 清除缓存
    keys = cache.keys("user_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '更新用户成功'}, status_code=status.HTTP_200_OK)


@router.delete('/del-user', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="删除用户",
               description="""
    删除用户
    "account": 账号
    """)
async def del_user(request: Request, form: UserDeleteForm, db: Session = Depends(get_db)):
    # 判断用户是否存在
    if not db.query(SysUser.id).filter(SysUser.account == form.account, SysUser.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户不存在或已经删除")

    # 删除用户
    user = get_current_user(request)
    db_user = db.query(SysUser).filter(SysUser.account == form.account, SysUser.state == 1).first()
    handle_db = DbHandleBase()
    handle_db.delete(db, user, db_user)
    # TODO 清除缓存
    keys = cache.keys("user_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '删除用户成功'}, status_code=status.HTTP_200_OK)


@router.get('/get-user', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)],
            name="获取用户信息", description="""
    获取用户信息
    """)
async def get_user(request: Request, db: Session = Depends(get_db),
                   account: Optional[str] = Query(None, min_length=2, max_length=20, title="账号",
                                                  description="账号"),
                   page: dict = Depends(pagination)):
    # 缓存key
    ch_key = "user_" + md5_encrypt(str(request.url))
    # TODO 如果有缓存读取缓存，没有读取mysql
    if cache.exists(ch_key):
        total = int(cache.lrange(ch_key, 0, 0)[0])
        ch_menu = cache.lrange(ch_key, 1, -1)
        user_list = [ast.literal_eval(x) for x in ch_menu]
    else:
        if not hasattr(SysUser, page["order_id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的排序id")

        db_user = db.query(SysUser.id, SysUser.account, SysUser.user_name, SysUser.password, SysUser.phone,
                           SysUser.email,
                           SysUser.is_super,
                           SysUser.remarks, SysUser.create_time,
                           SysUser.roles).filter(SysUser.state == 1)
        if account:
            db_user = db_user.filter(SysUser.account == account)
        # TODO 总的角色数
        total = db_user.count()

        # TODO 获取分页后的用户数据
        result = db_user.order_by(page["order_by"]).limit(page["page_size"]).offset(page["offset"]).all()
        user_list = orm_all_to_dict(result)

        # 写入缓存
        ch_result_list = [str(x) for x in user_list]
        if ch_result_list:
            cache.rpush(ch_key, *ch_result_list)
        cache.lpush(ch_key, total)
        cache.expire(ch_key, config.CH_TIMEOUT)

    return JSONResponse({"total": total, "detail": user_list}, status_code=status.HTTP_200_OK)


@router.get('/get-self', dependencies=[Depends(backstage), Depends(oauth2_scheme)], name="获取个人账户信息", description="""
    获取个人账户信息
    """)
async def get_self(request: Request, db: Session = Depends(get_db)):
    # 获取用户
    user = get_current_user(request)
    # 缓存key
    ch_key = "user_" + md5_encrypt(str(user))
    # TODO 如果有缓存读取缓存，没有读取mysql
    if cache.exists(ch_key):
        result = cache.get(ch_key)
        user_info = ast.literal_eval(result)
    else:
        db_user = db.query(SysUser.id, SysUser.account, SysUser.user_name, SysUser.phone, SysUser.email,
                           SysUser.remarks, SysUser.create_time,
                           SysUser.roles).filter(SysUser.state == 1, SysUser.account == user["account"]).first()

        user_info = orm_one_to_dict(db_user)

        # 写入缓存
        if user_info:
            cache.set(ch_key, str(user_info))
        cache.expire(ch_key, config.CH_TIMEOUT)

    return JSONResponse({"detail": user_info}, status_code=status.HTTP_200_OK)


@router.put('/update-self', dependencies=[Depends(backstage), Depends(oauth2_scheme)], name="更新个人信息", description="""
    更新个人信息
    "user_name": 用户名
    "phone": 手机号
    "email": 邮箱
    "remarks": 备注
    """)
async def update_self(request: Request, form: SelfUpdateForm, db: Session = Depends(get_db)):
    # 获取用户
    user = get_current_user(request)
    account = user["account"] if user else ""
    # 判断用户是否存在
    if not db.query(SysUser.id).filter(SysUser.account == account, SysUser.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户不存在或已经删除")

    # 更新用户信息
    db_user = db.query(SysUser).filter(SysUser.account == account, SysUser.state == 1).first()
    db_user.user_name = form.user_name
    db_user.phone = form.phone
    db_user.email = form.email
    db_user.remarks = form.remarks
    handle_db = DbHandleBase()
    handle_db.update(db, user, db_user)

    # TODO 清除缓存
    keys = cache.keys("user_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '更新个人信息成功'}, status_code=status.HTTP_200_OK)


@router.put('/reset-passwd', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)],
            name="重置密码", description="""
    重置密码
    "account": 账号,
    "new_pwd": 新密码,
    "retry_pwd": 新密码
    """)
async def reset_passwd(request: Request, form: RestPasswdForm, db: Session = Depends(get_db)):
    # 判断用户是否存在
    if not db.query(SysUser.id).filter(SysUser.account == form.account,
                                       SysUser.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账号不存在")

    # 更新user表
    user = get_current_user(request)
    db_user = db.query(SysUser).filter(SysUser.account == form.account, SysUser.state == 1).first()
    db_user.password = encrypt_password(form.new_pwd, form.account)
    handle_db = DbHandleBase()
    handle_db.update(db, user, db_user)

    return JSONResponse({'detail': '密码重置成功'}, status_code=status.HTTP_200_OK)


@router.put('/reset-selfpasswd', dependencies=[Depends(backstage), Depends(oauth2_scheme)], name="重置个人密码", description="""
    重置个人密码
    "old_pwd": 原始密码,
    "new_pwd": 新密码,
    "retry_pwd": 新密码
    """)
async def reset_selfpasswd(request: Request, form: RestSelfPasswdForm, db: Session = Depends(get_db)):
    # 判断新密码是否一致
    if form.new_pwd != form.retry_pwd:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="新密码不一致")

    # 判断密码是否正确
    user = get_current_user(request)
    if not db.query(SysUser.id).filter(SysUser.account == user["account"],
                                       SysUser.password == encrypt_password(form.old_pwd, user["account"]),
                                       SysUser.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="原始密码错误")

    # 更新user表
    db_user = db.query(SysUser).filter(SysUser.account == user["account"], SysUser.state == 1).first()
    db_user.password = encrypt_password(form.new_pwd, user["account"])
    handle_db = DbHandleBase()
    handle_db.update(db, user, db_user)

    return JSONResponse({'detail': '密码重置成功'}, status_code=status.HTTP_200_OK)
