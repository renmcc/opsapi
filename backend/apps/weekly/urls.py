#!/usr/bin/env python
# coding:utf-8
# __time__: 2021/4/7 10:32
# __author__ = 'ren_mcc'

from fastapi import APIRouter
from apps.weekly import weekly_type, weekly_project, weekly_report


router = APIRouter()

# 系统、权限路由
router.include_router(weekly_type.router, prefix='/type', tags=["周报处理类型"])
router.include_router(weekly_project.router, prefix='/project', tags=["周报处理项目"])
router.include_router(weekly_report.router, prefix='/report', tags=["周报"])

