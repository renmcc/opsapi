from fastapi import Request
from db.db_caches import cache
from public.logger import logger
from public.str_utils import encrypt_password
import ast

def get_token_key(request):
    """获取当前后台登录用户的token_key"""
    access_token = None
    try:
        authorization: str = request.headers.get("Authorization")
        access_token = authorization.split(" ")[1] if authorization else None
    except Exception as e:
        logger.error(e)
    finally:
        return access_token


def get_current_user(request: Request):
    """获取当前后台登录用户"""
    value = None
    try:
        token_key = get_token_key(request)
        token_value = cache.get(token_key) if token_key else None
        token_value = token_value if token_value else None
        value = ast.literal_eval(token_value) if token_value else None
    except Exception as e:
        logger.error(e)
    finally:
        return value



