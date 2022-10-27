# 系统设置
NAME = '运维管理系统'
LOGO = '/media/logo/logo.jpg'
HEADER_IMG = '/media/logo/header.jpg'
DOC_TITLE = '运维系统API文档'
DOC_VERSION = '1.0.0'
DOC_URL = '/docs'

# 数据库连接, 多个数据库可用元组
# '数据库类型+数据库驱动名称://用户名:数据库密码@数据库连接地址:端口号/数据库名'
DB_CONN_URI = "mysql+pymysql://ops:910202@192.168.10.10:3306/opsapi?charset=utf8mb4"

# redis连接
REDIS_HOST = "192.168.10.10"
REDIS_PORT = 6379
REDIS_DB = 0
CH_TOKEN_TIMEOUT = 24 * 60 * 60    # token缓存时间默认24小时
CH_TIMEOUT = 60 * 30   # 缓存时间默认30分钟

# 跨域白名单
# -----------------------跨域支持-------------------------------------
CORS_ORIGINS = ['http://localhost:8000', "http://127.0.0.1"]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['*']
CORS_ALLOW_HEADERS = ['*']

# 全局白名单
ALLOW_HOSTS = ["*"]
# doc白名单
DOC_ALLOW_HOST = ["127.0.0.1"]

# 加密sort
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"

# 分页
PAGE_SIZE = 50

# 媒体目录
STATIC_DIR = '/static'
