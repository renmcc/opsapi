from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from core import config

__author__ = 'ren_mcc'

engine = create_engine(config.DB_CONN_URI,
                       pool_pre_ping=True,
                       echo=True,
                       echo_pool=True,
                       max_overflow=0,  # 超过连接池大小外最多创建的连接
                       pool_size=100)  # 连接池大小
# 创建连接工厂，关闭自动提交和自动刷新， 工厂（给它传值，它会返回一个结果给你）
session_factory = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
# 类似单例模式，线程安全
SessionLocal = scoped_session(session_factory)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
