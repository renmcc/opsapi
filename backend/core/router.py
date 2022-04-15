from fastapi import APIRouter
from apps.system import urls as system_urls
from apps.weekly import urls as weekly_urls
from public.upload_file_utils import router as upload_router
from core.config import STATIC_DIR


__author__ = 'ren_mcc'
api_router = APIRouter()

# 全局路由
api_router.include_router(system_urls.router, prefix='/system')
api_router.include_router(weekly_urls.router, prefix='/weekly')
# api_router.include_router(upload_router, prefix=STATIC_DIR, tags=["上传文件"])
