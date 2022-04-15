from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

__author__ = 'ren_mcc'


class LoginForm(BaseModel):
    account: Optional[str] = Field(..., title="登录账号", max_length=10, min_length=3)
    password: Optional[str] = Field(..., title="登录密码", max_length=10, min_length=3)

    class Config:
        schema_extra = {
            "example": {
                "account": "test",
                "password": "123"
            }
        }


class DeptRequestForm(BaseModel):
    parent_id: Optional[int] = Field(..., ge=1, le=100, title="父级部门id", description="父级部门id")
    department_name: Optional[str] = Field(..., min_length=2, max_length=10, title="部门名称", description="部门名称")
    remarks: Optional[str] = Field(None, min_length=2, max_length=50, title="部门描述", description="部门描述")

    class Config:
        schema_extra = {
            "example": {
                "parent_id": 1,
                "department_name": "运维部",
                "remarks": "天威诚信运营中心-系统运维部"
            }
        }


class MenuRequestForm(BaseModel):
    parent_id: Optional[int] = Field(..., ge=0, le=100, title="父级菜单id", description="父级菜单id, 0表示最顶级菜单")
    menu_name: Optional[str] = Field(..., min_length=2, max_length=10, title="菜单名称", description="菜单名称")
    menu_code: Optional[str] = Field(..., min_length=2, max_length=100, title="组件路径", description="组件路径")
    menu_url: Optional[str] = Field(..., min_length=2, max_length=100, title="权限标识", description="权限标识")
    menu_icon: Optional[str] = Field(None, min_length=0, max_length=100, title="图标", description="图标")
    menu_type: Optional[int] = Field(..., ge=0, le=2, title="资源类型", description="资源类型,0为目录、1为菜单、2为按钮")

    class Config:
        schema_extra = {
            "example": {
                "parent_id": 0,
                "menu_name": "系统管理",
                "menu_code": "/system",
                "menu_url": "/system",
                "menu_icon": "",
                "menu_type": 1,
            }
        }


class RoleRequestForm(BaseModel):
    role_name: Optional[str] = Field(..., min_length=2, max_length=10, title="角色名称", description="角色名称")
    remarks: Optional[str] = Field(None, min_length=2, max_length=50, title="角色描述", description="角色描述")
    menu_id_list: List[int] = []
    permission_id_list: List[int] = []

    class Config:
        schema_extra = {
            "example": {
                "role_name": "admin",
                "remarks": "管理员角色",
                "menu_id_list": [],
                "permission_id_list": []
            }
        }


class UserRequestForm(BaseModel):
    account: Optional[str] = Field(..., min_length=2, max_length=10, title="账号", description="账号")
    password: Optional[str] = Field(..., min_length=2, max_length=20, title="密码", description="密码")
    user_name: Optional[str] = Field(..., min_length=2, max_length=10, title="用户名", description="用户名")
    is_super: Optional[int] = Field(..., ge=0, le=1, title="超级用户", description="超级用户")
    phone: Optional[str] = Field(..., min_length=11, max_length=11,
                                 regex="^(13\d|14[5|7]|15\d|166|17[3|6|7]|18\d)\d{8}$", title="手机号", description="手机号")
    email: Optional[EmailStr] = Field(None, title="邮箱", description="邮箱")
    roles: List[int] = Field(..., ge=1, le=100, title="角色id", description="角色id")
    remarks: Optional[str] = Field(None, min_length=0, max_length=50, title="描述", description="描述")

    class Config:
        schema_extra = {
            "example": {
                "account": "admin",
                "password": "123",
                "user_name": "管理员",
                "is_super": 0,
                "phone": "15810511111",
                "email": "ren_mcc@foxmail.com",
                "roles": [1, 2],
                "remarks": "管理员账号"
            }
        }


class UserUpdateForm(BaseModel):
    account: Optional[str] = Field(..., min_length=2, max_length=10, title="账号", description="账号")
    user_name: Optional[str] = Field(..., min_length=2, max_length=10, title="用户名", description="用户名")
    is_super: Optional[int] = Field(..., ge=0, le=1, title="超级用户", description="超级用户")
    phone: Optional[str] = Field(..., min_length=11, max_length=11,
                                 regex="^(13\d|14[5|7]|15\d|166|17[3|6|7]|18\d)\d{8}$", title="手机号", description="手机号")
    email: Optional[EmailStr] = Field(None, title="邮箱", description="邮箱")
    roles: List[int] = Field(..., ge=1, le=100, title="角色id", description="角色id")
    remarks: Optional[str] = Field(None, min_length=1, max_length=50, title="描述", description="描述")

    class Config:
        schema_extra = {
            "example": {
                "account": "admin",
                "user_name": "管理员",
                "is_super": 0,
                "phone": "15810511111",
                "email": "ren_mcc@foxmail.com",
                "roles": [1, 2],
                "remarks": "管理员账号"
            }
        }


class SelfUpdateForm(BaseModel):
    user_name: Optional[str] = Field(..., min_length=2, max_length=10, title="用户名", description="用户名")
    phone: Optional[str] = Field(..., min_length=11, max_length=11,
                                 regex="^(13\d|14[5|7]|15\d|166|17[3|6|7]|18\d)\d{8}$", title="手机号", description="手机号")
    email: Optional[EmailStr] = Field(None, title="邮箱", description="邮箱")
    remarks: Optional[str] = Field(None, min_length=1, max_length=50, title="描述", description="描述")

    class Config:
        schema_extra = {
            "example": {
                "user_name": "管理员",
                "phone": "15810511111",
                "email": "ren_mcc@foxmail.com",
                "remarks": "管理员账号"
            }
        }


class UserDeleteForm(BaseModel):
    account: Optional[str] = Field(..., min_length=2, max_length=10, title="账号", description="账号")

    class Config:
        schema_extra = {
            "example": {
                "account": "admin"
            }
        }


class RestPasswdForm(BaseModel):
    account: Optional[str] = Field(..., min_length=2, max_length=10, title="账号", description="账号")
    new_pwd: Optional[str] = Field(..., min_length=2, max_length=10, title="新密码", description="新密码")
    retry_pwd: Optional[str] = Field(..., min_length=2, max_length=10, title="确认密码", description="确认密码")

    class Config:
        schema_extra = {
            "example": {
                "account": "admin",
                "new_pwd": "1234",
                "retry_pwd": "1234"
            }
        }


class RestSelfPasswdForm(BaseModel):
    old_pwd: Optional[str] = Field(..., min_length=2, max_length=10, title="原始密码", description="原始密码")
    new_pwd: Optional[str] = Field(..., min_length=2, max_length=10, title="新密码", description="新密码")
    retry_pwd: Optional[str] = Field(..., min_length=2, max_length=10, title="确认密码", description="确认密码")

    class Config:
        schema_extra = {
            "example": {
                "old_pwd": "123",
                "new_pwd": "1234",
                "retry_pwd": "1234"
            }
        }


class WhileRequestForm(BaseModel):
    while_ip: Optional[str] = Field(..., min_length=1, max_length=20, title="ip地址", description="ip地址")
    remarks: Optional[str] = Field(..., min_length=2, max_length=50, title="描述", description="描述")


    class Config:
        schema_extra = {
            "example": {
                "while_ip": "127.0.0.1",
                "remarks": "本机ip地址"
            }
        }