from fastapi import APIRouter
from apps.system import sys_auth, sys_info, sys_role, sys_menu, sys_user, sys_log, sys_while


__author__ = 'ren_mcc'
router = APIRouter()

# 系统、权限路由
router.include_router(sys_auth.router, prefix='/auth', tags=["系统认证"])
router.include_router(sys_info.router, prefix='/info', tags=["系统信息"])
router.include_router(sys_while.router, prefix='/while', tags=["白名单"])
router.include_router(sys_menu.router, prefix='/menu', tags=["系统前端菜单"])
router.include_router(sys_role.router, prefix='/role', tags=["系统角色"])
router.include_router(sys_user.router, prefix='/user', tags=["系统用户"])
router.include_router(sys_log.router, prefix='/log', tags=["系统日志"])


