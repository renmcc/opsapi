from fastapi import APIRouter, Request, Depends, status, Query, HTTPException
from apps.system.model import SysRole, SysRolePermission, SysRoleMenu, SysMenu, SysApi, SysUser
from sqlalchemy.orm import Session
from sqlalchemy.orm import aliased
from sqlalchemy import desc
from apps.system.form import RoleRequestForm
from sqlalchemy import func
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


@router.post('/add-role', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="添加角色",
             description="""
    添加角色
    """)
async def add_role(request: Request, form: RoleRequestForm, db: Session = Depends(get_db)):
    # 如果角色已经存在退出
    if db.query(SysRole.id).filter(SysRole.role_name == form.role_name, SysRole.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色已存在")

    # 菜单id有误退出
    db_menu = db.query(SysMenu.id).filter(SysMenu.id.in_(form.menu_id_list), SysMenu.state == 1).count()
    if db_menu != len(form.menu_id_list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="菜单id有误")

    # 权限id有误退出
    db_perm = db.query(SysApi.id).filter(SysApi.id.in_(form.permission_id_list), SysApi.state == 1).count()
    if db_perm != len(form.permission_id_list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="权限id有误")

    # 添加角色到数据库
    user = get_current_user(request)
    db_role = SysRole()
    db_role.role_name = form.role_name
    db_role.remarks = form.remarks
    handle_db = DbHandleBase()
    handle_db.create(db, user, db_role)

    # 获取添加角色的role_id
    db_role = db.query(SysRole.id).filter(SysRole.role_name == form.role_name, SysRole.state == 1).first()
    db_role_info = orm_one_to_dict(db_role)

    # TODO 处理菜单id
    if form.menu_id_list:
        db_menu = db.query(SysMenu.id, SysMenu.parent_id).filter(SysMenu.id.in_(set(form.menu_id_list)),
                                                                 SysMenu.state == 1).all()
        db_menu_list = orm_all_to_dict(db_menu)

        # 处理父子菜单id
        menu_list = []
        for menu in db_menu_list:
            if menu["parent_id"] != 0:
                menu_list.append(menu["parent_id"])
            menu_list.append(menu["id"])
        menu_list = set(menu_list)

        # 添加角色菜单权限到数据库
        db_sys_menus = []
        for menu_id in menu_list:
            new_role_menu = SysRoleMenu()
            new_role_menu.menu_id = menu_id
            new_role_menu.role_id = db_role_info["id"]
            db_sys_menus.append(new_role_menu)
        handle_db.batch_create(db, user, db_sys_menus)

    # 处理APIid
    if form.permission_id_list:
        # 获取有效的api权限id
        db_perm = db.query(SysApi.id).filter(SysApi.id.in_(set(form.permission_id_list)),
                                             SysApi.state == 1).all()
        db_perm_list = orm_all_to_dict(db_perm)

        # 添加角色权限到数据库
        db_role_perm_list = []
        for perm in db_perm_list:
            db_role_perm = SysRolePermission()
            db_role_perm.role_id = db_role_info["id"]
            db_role_perm.api_id = perm["id"]
            db_role_perm_list.append(db_role_perm)
        handle_db.batch_create(db, user, db_role_perm_list)
    # TODO 清除缓存
    keys = cache.keys("role_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '创建角色成功'}, status_code=status.HTTP_201_CREATED)


@router.put('/update-role', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="更新角色",
            description="""
    更新角色
    """)
async def update_role(request: Request, form: RoleRequestForm, db: Session = Depends(get_db)):
    # 如果角色不存在退出
    if not db.query(SysRole.id).filter(SysRole.role_name == form.role_name, SysRole.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色不存在")

    # 菜单id有误退出
    db_menu = db.query(SysMenu.id).filter(SysMenu.id.in_(form.menu_id_list), SysMenu.state == 1).count()
    if db_menu != len(form.menu_id_list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="菜单id有误")

    # 权限id有误退出
    db_perm = db.query(SysApi.id).filter(SysApi.id.in_(form.permission_id_list), SysApi.state == 1).count()
    if db_perm != len(form.permission_id_list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="权限id有误")

    # TODO 更新角色信息到数据库
    user = get_current_user(request)
    db_role = db.query(SysRole).filter(SysRole.role_name == form.role_name, SysRole.state == 1).first()
    db_role.remarks = form.remarks
    handle_db = DbHandleBase()
    handle_db.update(db, user, db_role)

    # TODO 处理菜单权限
    # 获取有效的菜单id
    db_menu = db.query(SysMenu.id, SysMenu.parent_id).filter(SysMenu.id.in_(set(form.menu_id_list)),
                                                             SysMenu.state == 1).all()
    db_menu_list = orm_all_to_dict(db_menu)

    # 处理父子菜单id,获取需要修改的id
    menu_list = []
    for menu in db_menu_list:
        if menu["parent_id"] != 0:
            menu_list.append(menu["parent_id"])
        menu_list.append(menu["id"])
    menu_list = set(menu_list)

    # 获取角色原有菜单id
    db_role_menu = db.query(SysRoleMenu.menu_id).filter(SysRoleMenu.role_id == db_role.id,
                                                        SysRoleMenu.state == 1).all()

    db_role_menu = [x[0] for x in db_role_menu] if db_role_menu else []

    # 获取需要添加或需要删除的菜单权限id
    add_menu_ids = list(set(menu_list).difference(set(db_role_menu)))
    del_menu_ids = list(set(db_role_menu).difference(set(menu_list)))

    # 添加角色菜单权限到数据库
    db_sys_menus = []
    for menu_id in add_menu_ids:
        new_role_menu = SysRoleMenu()
        new_role_menu.menu_id = menu_id
        new_role_menu.role_id = db_role.id
        db_sys_menus.append(new_role_menu)
    handle_db.batch_create(db, user, db_sys_menus)

    # 删除角色菜单权限到数据库
    db_role_menu_del = db.query(SysRoleMenu).filter(SysRoleMenu.menu_id.in_(del_menu_ids),
                                                    SysRoleMenu.state == 1).all()
    handle_db.batch_delete(db, user, db_role_menu_del)

    # TODO 处理API权限

    # 获取有效的api权限id
    db_perm = db.query(SysApi.id).filter(SysApi.id.in_(set(form.permission_id_list)),
                                         SysApi.state == 1).all()

    db_perm_list = [x[0] for x in db_perm] if db_perm else []

    # 获取角色原有api权限id
    db_role_permission = db.query(SysRolePermission.api_id).filter(SysRolePermission.role_id == db_role.id,
                                                                   SysRolePermission.state == 1).all()

    db_role_permission_list = [x[0] for x in db_role_permission] if db_role_permission else []

    # 获取需要添加或需要删除的api权限id
    add_perm_ids = list(set(db_perm_list).difference(set(db_role_permission_list)))
    del_perm_ids = list(set(db_role_permission_list).difference(set(db_perm_list)))

    # 添加角色api权限到数据库
    db_role_perm_list = []
    for perm_id in add_perm_ids:
        db_role_perm = SysRolePermission()
        db_role_perm.role_id = db_role.id
        db_role_perm.api_id = perm_id
        db_role_perm_list.append(db_role_perm)
    handle_db.batch_create(db, user, db_role_perm_list)

    # 删除角色api权限到数据库
    db_role_perm_del = db.query(SysRolePermission).filter(SysRolePermission.api_id.in_(del_perm_ids),
                                                          SysRolePermission.state == 1).all()
    handle_db.batch_delete(db, user, db_role_perm_del)

    # TODO 清除缓存
    keys = cache.keys("role_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '更新角色成功'}, status_code=status.HTTP_200_OK)


@router.delete('/del-role', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="删除角色",
               description="""
    删除角色
    """)
async def del_role_info(request: Request, db: Session = Depends(get_db),
                        role_id: Optional[int] = Query(..., ge=1, le=100, title="角色id", description="角色id")):
    # 如果角色不存在退出
    if not db.query(SysRole.id).filter(SysRole.id == role_id, SysRole.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="找不到该角色信息或已删除")

    user = get_current_user(request)
    handle_db = DbHandleBase()
    # 获取角色对象
    db_role = db.query(SysRole).filter(SysRole.id == role_id, SysRole.state == 1).first()

    # TODO 删除菜单权限
    db_role_menu = db.query(SysRoleMenu).filter(SysRoleMenu.role_id == db_role.id,
                                                SysRoleMenu.state == 1).all()
    handle_db.batch_delete(db, user, db_role_menu)

    # TODO 删除api权限
    db_role_perm = db.query(SysRolePermission).filter(SysRolePermission.role_id == db_role.id,
                                                      SysRolePermission.state == 1).all()
    handle_db.batch_delete(db, user, db_role_perm)

    # TODO 删除角色
    handle_db.delete(db, user, db_role)
    # TODO 清除缓存
    keys = cache.keys("role_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '删除成功'}, status_code=status.HTTP_200_OK)


@router.get('/get-role', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="获取角色信息",
            description="""
    获取角色信息
    role_name：角色名
    page：页码
    page_size：每页最大行数
    """)
async def get_role_list(request: Request, db: Session = Depends(get_db),
                        role_name: Optional[str] = Query(None, min_length=2, max_length=20, title="角色名",
                                                         description="角色名"),
                        page: dict = Depends(pagination)):
    # 缓存key
    ch_key = "role_" + md5_encrypt(str(request.url))
    # TODO 如果有缓存读取缓存，没有读取mysql
    if cache.exists(ch_key):
        total = int(cache.lrange(ch_key, 0, 0)[0])
        ch_menu = cache.lrange(ch_key, 1, -1)
        role_list = [ast.literal_eval(x) for x in ch_menu]
    else:
        if not hasattr(SysRole, page["order_id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的排序id")

        # db_role = db.query(SysRole.id, SysRole.role_name, SysUser.account.label("create_by_user"), SysRole.remarks, SysRole.create_time).filter(
        #     SysRole.state == 1, SysUser.state == 1, SysUser.id == SysRole.create_by_id)
        a = aliased(SysRole)
        b = aliased(SysUser)
        c = aliased(SysUser)
        db_role = db.query(a.id, a.role_name, b.account.label("create_by_user"), a.create_time,
                           c.account.label("chage_by_user"), a.last_change_time, a.remarks).outerjoin(b,
                                                                                                      a.create_by_id == b.id).outerjoin(
            c,
            a.change_by_id == c.id).filter(
            a.state == 1)
        if role_name:
            db_role = db_role.filter(a.role_name == role_name)
        # TODO 总的角色数
        total = db_role.count()
        # TODO 获取分页后的角色数据
        if page["desc"]:
            order = desc(getattr(a, page["order_id"]))
        else:
            order = getattr(a, page["order_id"])
        result = db_role.order_by(order).limit(page["page_size"]).offset(
            page["offset"]).all()
        role_list = orm_all_to_dict(result)

        # TODO 获取角色id列表
        role_id_list = []
        for ret in result:
            role_id_list.append(ret.id)

        # TODO 把menu数据汇总到角色数据中
        # 连表查询角色对应的menu数据
        db_role_menu = db.query(SysRoleMenu.role_id, SysMenu.id, SysMenu.parent_id, SysMenu.menu_name,
                                SysMenu.menu_code,
                                SysMenu.menu_url, SysMenu.menu_icon, SysMenu.menu_type).filter(
            SysMenu.id == SysRoleMenu.menu_id, SysRoleMenu.state == 1, SysMenu.state == 1,
            SysRoleMenu.role_id.in_(role_id_list)).all()

        db_role_menu_list = orm_all_to_dict(db_role_menu)

        # 获取子菜单
        for menu_list in db_role_menu_list:
            db_child_menu = db.query(SysMenu.id, SysMenu.parent_id, SysMenu.menu_name, SysMenu.menu_code,
                                     SysMenu.menu_url,
                                     SysMenu.menu_icon,
                                     SysMenu.menu_type).filter(SysMenu.parent_id == menu_list['id'],
                                                               SysMenu.state == 1).order_by(
                "id").all()
            menu_list_child = orm_all_to_dict(db_child_menu)
            menu_list["childs"] = menu_list_child

        # 整合数据
        for role in role_list:
            role["menus"] = []
        for perm in db_role_menu_list:
            role_id = perm.pop("role_id")
            for role in role_list:
                if role["id"] == role_id:
                    role["menus"].append(perm)

        # TODO 把api数据汇总到角色数据中
        # 连表查询角色对应的api数据
        db_role_perm = db.query(SysRolePermission.role_id, SysApi.id, SysApi.name, SysApi.method, SysApi.path).filter(
            SysApi.id == SysRolePermission.api_id, SysRolePermission.state == 1, SysApi.state == 1,
            SysRolePermission.role_id.in_(role_id_list)).all()

        db_role_perm_list = orm_all_to_dict(db_role_perm)
        # 整合数据
        for role in role_list:
            role["permissions"] = []
        for perm in db_role_perm_list:
            role_id = perm.pop("role_id")
            for role in role_list:
                if role["id"] == role_id:
                    role["permissions"].append(perm)

        # 写入缓存
        ch_role_list = [str(x) for x in role_list]
        if ch_role_list:
            cache.rpush(ch_key, *ch_role_list)
        cache.lpush(ch_key, total)
        cache.expire(ch_key, config.CH_TIMEOUT)

    return JSONResponse({"total": total, "detail": role_list}, status_code=status.HTTP_200_OK)
