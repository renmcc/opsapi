import time
from fastapi import APIRouter, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core import config
from db.db_caches import cache
from db.db_base import DbHandleBase
from public.str_utils import encrypt_password
from public.oppose_crawler import backstage
from public.data_utils import orm_one_to_dict
from public.get_data_by_cache import get_token_key
from apps.system.model import SysUser, SysLoginLog
from apps.system import form
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from db.session import get_db
from middleware.request_limit import limiter

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/system/auth/login_doc")

__author__ = 'ren_mcc'

router = APIRouter()


@router.post('/login', name="登录", description="""
    登录接口
    account：必须大于3个字符，小于10个字符
    password：  必须大于3个字符，小于10个字符
    """)
@limiter.limit("10/minute")
async def login(request: Request, form_data: form.LoginForm, db: Session = Depends(get_db)):
    session_user = db.query(SysUser.id, SysUser.account, SysUser.user_name, SysUser.is_super, SysUser.roles).filter(
        SysUser.account == form_data.account,
        SysUser.password == encrypt_password(form_data.password, form_data.account), SysUser.state == 1).first()
    # TODO 格式化db查询数据
    user = orm_one_to_dict(session_user)
    # 记录登录日志
    new_log = SysLoginLog()
    new_log.account = form_data.account
    new_log.login_ip = request.scope['client'][0] if request.scope and request.scope['client'] else ''
    for raw in request.headers.raw:
        if bytes.decode(raw[0]) == 'user-agent':
            new_log.browser = bytes.decode(raw[1])
    # TODO 创建数据库描述符
    db_handle = DbHandleBase()
    # TODO 用户不存在或密码错误直接退出
    if not user:
        new_log.is_success = False
        # TODO 写入登录日志
        db_handle.create(db, user, new_log)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="账号不存在,或密码错误", headers={"WWW-Authenticate": "Bearer"})
    # TODO 生成token
    access_token = encrypt_password(str(user['id']) + str(time.time()), form_data.account)
    new_log.user_name = user['user_name']
    new_log.is_success = True
    new_log.access_token = access_token
    new_log.account = user['account']
    # TODO 写入登录日志
    db_handle.create(db, user, new_log)
    # TODO 写入redis
    user["login_ip"] = new_log.login_ip
    user["browser"] = new_log.browser
    cache.set(access_token, str(user), config.CH_TOKEN_TIMEOUT)
    return JSONResponse({'access_token': access_token}, status_code=status.HTTP_200_OK)


@router.get('/login-out', dependencies=[Depends(backstage), Depends(oauth2_scheme)],
            name="登出", description="退出登录")
def login_out(request: Request):
    token_key = get_token_key(request)
    if cache.exists(token_key):
        cache.delete(token_key)
        menu_key = 'menu' + token_key[5:]
        cache.delete(menu_key) if cache.exists(menu_key) else None
    return JSONResponse({'detail': "登出成功"}, status_code=status.HTTP_200_OK)


@router.post('/login_doc', include_in_schema=False, name="doc登录")
@limiter.limit("10/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    登录
    account：必须大于3个字符，小于10个字符
    password：必须大于3个字符，小于10个字符
    """
    session_user = db.query(SysUser.id, SysUser.account, SysUser.user_name, SysUser.is_super, SysUser.roles).filter(
        SysUser.account == form_data.username,
        SysUser.password == encrypt_password(form_data.password, form_data.username), SysUser.state == 1).first()
    # 格式化db查询数据
    user = orm_one_to_dict(session_user)
    # 记录登录日志
    new_log = SysLoginLog()
    new_log.account = form_data.username
    new_log.login_ip = request.scope['client'][0] if request.scope and request.scope['client'] else ''
    for raw in request.headers.raw:
        if bytes.decode(raw[0]) == 'user-agent':
            new_log.browser = bytes.decode(raw[1])
    # 创建数据库描述符
    db_handle = DbHandleBase()
    # 用户不存在或密码错误直接退出
    if not user:
        new_log.is_success = False
        # 写入登录日志
        db_handle.create(db, user, new_log)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="账号不存在,或密码错误", headers={"WWW-Authenticate": "Bearer"})
    # 生成token
    access_token = encrypt_password(str(user['id']) + str(time.time()), form_data.username)
    new_log.user_name = user['user_name']
    new_log.is_success = True
    new_log.access_token = access_token
    # 写入登录日志
    db_handle.create(db, user, new_log)
    # 写入redis
    user["login_ip"] = new_log.login_ip
    user["browser"] = new_log.browser
    cache.set(access_token, str(user), config.CH_TOKEN_TIMEOUT)
    return {'status_code': status.HTTP_200_OK, "access_token": access_token, "token_type": "Bearer"}
