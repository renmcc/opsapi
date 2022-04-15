from fastapi import APIRouter, Request, Depends, status, Query, HTTPException
import ast
from apps.system.model import SysMenu as Menu
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from apps.system.form import MenuRequestForm
from db.db_base import DbHandleBase
from public.oppose_crawler import backstage, pagination, check_perm
from public.get_data_by_cache import get_token_key, get_current_user
from public.data_utils import orm_one_to_dict, orm_all_to_dict, get_tree_data, sql_one_to_dict
from apps.system.sys_auth import oauth2_scheme
from typing import Optional
from sqlalchemy import or_
from db.session import get_db
from db.db_caches import cache
from core import config
from public.str_utils import md5_encrypt

__author__ = 'ren_mcc'
router = APIRouter()


@router.post('/add-menu', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="添加菜单", description="""
    添加菜单
    parent_id：父级菜单id
    menu_name：菜单名称
    menu_code：组件路径(前端请求文件的路径里),目录可填Layout
    menu_url：权限标识,即标识每一个操作权限
    menu_icon：图标，meta里面的icon
    menu_type：资源类型,0为目录、1为菜单、2为按钮")
    """)
async def add_menu(request: Request, form: MenuRequestForm, db: Session = Depends(get_db)):
    # 判断是否存在
    if db.query(Menu.id).filter(Menu.menu_name == form.menu_name, Menu.parent_id == form.parent_id,
                                Menu.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="菜单已存在")
    # 如果添加的不是父级菜单，需要判断下父级菜单是否存在
    if form.parent_id != 0:
        if not db.query(Menu.id).filter(Menu.id == form.parent_id, Menu.state == 1).scalar():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="父级菜单不存在,或已删除")
    db_menu = Menu()
    db_menu.parent_id = form.parent_id
    db_menu.menu_name = form.menu_name
    db_menu.menu_code = form.menu_code
    db_menu.menu_url = form.menu_url
    db_menu.menu_icon = form.menu_icon
    db_menu.menu_type = form.menu_type
    user = get_current_user(request)
    handle_db = DbHandleBase()
    handle_db.create(db, user, db_menu)
    # TODO 清除缓存
    keys = cache.keys("menu_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '创建菜单成功'}, status_code=status.HTTP_200_OK)


@router.put('/update-menu', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="更新菜单", description="""
    更新菜单
    parent_id：父级菜单id，0表示最顶级菜单
    menu_name：菜单名称
    menu_code：组件路径(前端请求文件的路径里),目录可填Layout
    menu_url：权限标识,即标识每一个操作权限
    menu_icon：图标，meta里面的icon
    menu_type：资源类型,0为目录、1为菜单、2为按钮")
    """)
async def update_menu(request: Request, form: MenuRequestForm, db: Session = Depends(get_db)):
    # 判断是否存在
    if not db.query(Menu.id).filter(Menu.menu_name == form.menu_name, Menu.parent_id == form.parent_id,
                                    Menu.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="菜单不存在")
    db_menu = db.query(Menu).filter(Menu.menu_name == form.menu_name, Menu.state == 1).first()
    db_menu.parent_id = form.parent_id
    db_menu.menu_name = form.menu_name
    db_menu.menu_code = form.menu_code
    db_menu.menu_url = form.menu_url
    db_menu.menu_icon = form.menu_icon
    db_menu.menu_type = form.menu_type
    user = get_current_user(request)
    handle_db = DbHandleBase()
    handle_db.update(db, user, db_menu)
    # TODO 清除缓存
    keys = cache.keys("menu_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '更新菜单成功'}, status_code=status.HTTP_200_OK)


@router.delete('/del-menu', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="删除菜单", description="""
    删除菜单
    menu_id: 删除的菜单id，包括所有子id
    """)
async def del_menu(request: Request, db: Session = Depends(get_db),
                   menu_id: Optional[int] = Query(..., ge=1, le=100, title="菜单id", description="菜单id")):
    if not db.query(Menu).filter(Menu.id == menu_id, Menu.state == 1).scalar():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到该菜单信息或已删除")
    user = get_current_user(request)
    handle_db = DbHandleBase()
    db_menu_list = db.query(Menu).filter(or_(Menu.id == menu_id, Menu.parent_id == menu_id), Menu.state == 1).all()
    handle_db.batch_delete(db, user, db_menu_list)
    # TODO 清除缓存
    keys = cache.keys("menu_*")
    if keys:
        cache.delete(*keys)
    return JSONResponse({'detail': '删除成功'}, status_code=status.HTTP_200_OK)


@router.get('/get-menu', dependencies=[Depends(backstage), Depends(oauth2_scheme), Depends(check_perm)], name="菜单列表",
            description="""
    菜单列表
    menu_name: 主菜单的名称,不填查询所有
    """)
async def get_menu_list(request: Request, db: Session = Depends(get_db),
                        menu_name: Optional[str] = Query(None, min_length=2, max_length=10, title="菜单名称",
                                                         description="菜单名称"), page: dict = Depends(pagination)):
    # 缓存key
    ch_key = "menu_" + md5_encrypt(str(request.url))
    # TODO 如果有缓存读取缓存，没有读取mysql
    if cache.exists(ch_key):
        total = int(cache.lrange(ch_key, 0, 0)[0])
        ch_menu = cache.lrange(ch_key, 1, -1)
        parent_menu_list = [ast.literal_eval(x) for x in ch_menu]
    else:
        if not hasattr(Menu, page["order_id"]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的排序id")
        # 获取顶级菜单
        db_parent_menu = db.query(Menu.id, Menu.parent_id, Menu.menu_name, Menu.menu_code, Menu.menu_url,
                                  Menu.menu_icon,
                                  Menu.menu_type).filter(Menu.parent_id == 0, Menu.state == 1)
        # 输入了菜单名，过滤菜单名
        if menu_name:
            db_parent_menu = db_parent_menu.filter(Menu.menu_name == menu_name, Menu.state == 1)
        # TODO 获取顶级菜单
        total = db_parent_menu.count()
        db_parent_menu = db_parent_menu.order_by(page["order_by"]).limit(page["page_size"]).offset(page["offset"]).all()

        parent_menu_list = orm_all_to_dict(db_parent_menu)
        if not parent_menu_list:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="找不到该菜单信息或已删除")

        # TODO 获取顶级菜单的子菜单
        # 获取顶级菜单id
        result_ids = [x[0] for x in db_parent_menu]
        db_child_menu = db.query(Menu.parent_id, Menu.id, Menu.parent_id, Menu.menu_name, Menu.menu_code, Menu.menu_url,
                                 Menu.menu_icon,
                                 Menu.menu_type).filter(Menu.parent_id.in_(result_ids),
                                                        Menu.state == 1).order_by(
            page["order_by"]).all()
        db_child_menu_list = orm_all_to_dict(db_child_menu)
        # 顶级菜单添加子菜单字段
        for x in parent_menu_list:
            x["childs"] = []
        # 子菜单添加到顶级菜单

        for child_menu in db_child_menu_list:
            parent_id = child_menu.pop("parent_id")
            for parent_menu in parent_menu_list:
                if parent_menu["id"] == parent_id:
                    parent_menu["childs"].append(child_menu)

        # TODO 写入缓存
        ch_result = [str(x) for x in parent_menu_list]
        if ch_result:
            cache.rpush(ch_key, *ch_result)
        cache.lpush(ch_key, total)
        cache.expire(ch_key, config.CH_TIMEOUT)

    return JSONResponse({"total": total, 'detail': parent_menu_list}, status_code=status.HTTP_200_OK)
