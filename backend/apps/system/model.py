from sqlalchemy import String, Column, SmallInteger, Date, Boolean, Integer, UniqueConstraint, JSON
from db.db_base import BaseModel

__author__ = 'ren_mcc'

class SysUser(BaseModel):
    # 表名
    _table_name_ = 'sys_user'
    __table_args__ = ({'comment': '后台用户表'})

    account = Column(String(length=40), nullable=False, comment='账号')
    password = Column(String(length=80), nullable=False, comment='密码')
    user_name = Column(String(length=50), nullable=False, comment='用户名')
    is_super = Column(SmallInteger, default=0, comment="超级管理员")
    phone = Column(String(length=15), nullable=False, comment='手机号码')
    email = Column(String(length=30), nullable=True, comment='邮箱')
    roles = Column(JSON, nullable=False, default=[], comment='角色id')
    remarks = Column(String(length=200), nullable=True, comment='备注说明')


class SysRole(BaseModel):
    # 表名
    _table_name_ = 'sys_role'

    role_name = Column(String(length=30), nullable=False, comment='角色名称')
    remarks = Column(String(length=200), nullable=True, comment='备注说明')

    __table_args__ = (
        # UniqueConstraint("state", "role_name"),  # 联合唯一
        {'comment': '后台角色表'}
    )


class SysApi(BaseModel):
    # 表名
    _table_name_ = 'sys_api'

    path = Column(String(length=50), nullable=False, comment="api接口uri")
    method = Column(String(length=10), nullable=True, comment="api接口方法")
    name = Column(String(length=50), nullable=False, comment="api名称描述")

    __table_args__ = (
        # UniqueConstraint("state", "path"),  # 联合唯一
        {'comment': '后台权限表'}
    )


class SysRolePermission(BaseModel):
    """
    role和api的多对多关系表
    """
    _table_name_ = 'sys_role_permission_rel'
    __table_args__ = ({'comment': '角色API权限表'})
    role_id = Column(Integer, index=True, comment='角色id')
    api_id = Column(Integer, index=True, comment='Api_id')


class SysMenu(BaseModel):
    # 表名
    _table_name_ = 'sys_menu'
    __table_args__ = ({'comment': '菜单表'})

    parent_id = Column(Integer, index=True, comment='父级菜单id, 0表示最顶级菜单')
    menu_name = Column(String(length=30), nullable=False, comment='菜单名称')
    menu_code = Column(String(length=100), nullable=False, comment='组件路径(前端请求文件的路径里),目录可填Layout')
    menu_url = Column(String(length=100), nullable=False, comment='权限标识,即标识每一个操作权限')
    menu_icon = Column(String(length=100), nullable=True, comment='图标，meta里面的icon')
    menu_type = Column(SmallInteger, default=1, comment='资源类型,0为目录、1为菜单、2为按钮')


class SysRoleMenu(BaseModel):
    # 表名
    _table_name_ = 'sys_role_menu_rel'
    __table_args__ = ({'comment': '角色菜单表'})

    role_id = Column(Integer, index=True, comment='角色id')
    menu_id = Column(Integer, index=True, comment='菜单id')


class SysOperationLog(BaseModel):
    _table_name_ = 'sys_operation_log'
    operation_url = Column(String(length=500), nullable=True, comment='操作链接')
    request_body = Column(JSON, nullable=True, comment="请求体")
    is_doc = Column(Boolean, nullable=True, comment='是否是doc操作')
    ip = Column(String(length=300), nullable=True, comment='操作ip')
    browser = Column(String(length=300), nullable=True, comment='浏览器')
    account = Column(String(length=50), nullable=True, comment='操作用户')
    access_token = Column(String(length=50), nullable=True, comment='访问token')


class SysLoginLog(BaseModel):
    _table_name_ = 'sys_login_log'
    account = Column(String(length=30), nullable=True, comment='登陆账号')
    user_name = Column(String(length=100), nullable=True, comment='用户名')
    login_ip = Column(String(length=30), nullable=True, comment='操作ip')
    browser = Column(String(length=300), nullable=True, comment='浏览器')
    is_success = Column(Boolean, default=False, nullable=True, comment='是否成功登陆')
    access_token = Column(String(length=50), nullable=True, comment='访问token')


class SysDocWhileList(BaseModel):
    _table_name_ = 'sys_doc_while_list'
    while_ip = Column(String(length=30), nullable=True, comment='允许ip')
    remarks = Column(String(length=200), nullable=True, comment='备注说明')