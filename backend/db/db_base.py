from sqlalchemy import BigInteger, Column, DateTime, SmallInteger, String
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from fastapi import HTTPException, status
import time
import random
import datetime
from sqlalchemy.orm import Session
from public.logger import logger
from db.db_caches import cache

__author__ = 'ren_mcc'


class Base:
    """将表名改为小写"""
    @declared_attr
    def __tablename__(cls):
        # 如果有自定义表名就取自定义，没有就取小写类名
        table_name = cls._table_name_
        if not table_name:
            model_name = cls.__name__
            ls = []
            for index, char in enumerate(model_name):
                if char.isupper() and index != 0:
                    ls.append("_")
                ls.append(char)
            table_name = "".join(ls).lower()
        return table_name


BaseDB = declarative_base(cls=Base)


# 使用命令：alembic init alembic 初始化迁移数据库环境
# 这时会生成alembic文件夹 和 alembic.ini文件
class BaseModel(BaseDB):
    """
    表公共字段
    """
    __abstract__ = True

    id = Column(BigInteger, primary_key=True,
                unique=True, autoincrement=True, comment='主键ID')
    state = Column(SmallInteger, index=True, default=0,
                   comment='状态值, 0为已删除, 1为正常, 2为锁定')

    create_time = Column(DateTime, nullable=False, comment='创建时间')
    create_by_id = Column(BigInteger, nullable=True,
                          index=True, comment='创建者ID')

    last_change_time = Column(DateTime, nullable=True, comment='最后修改的时间')
    change_by_id = Column(BigInteger, nullable=True,
                          index=True, comment='最后修改者ID')

    deleted_time = Column(DateTime, nullable=True, comment='删除时间')
    deleted_by_id = Column(BigInteger, nullable=True,
                           index=True, comment='删除者id')


class DbHandleBase:
    """
    公共新增类
    """

    def __init__(self):
        self.now_time = datetime.datetime.now()

    # TODO 自定义单条记录新增方法
    def create(self, db: Session, user, obj):
        try:
            obj.state = 1
            obj.create_by_id = int(user['id']) if user else None
            obj.create_time = self.now_time
            db.add(obj)
            db.commit()
            # db.refresh(obj)
            # db.close()
        except Exception as e:
            db.rollback()
            logger.error(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建数据失败，已回退")

    # TODO 自定义单条记录更新方法
    def update(self, db: Session, user, obj):
        try:
            obj.change_by_id = int(user['id']) if user else None
            obj.last_change_time = self.now_time
            db.commit()
            # db.refresh(obj)
            # db.close()
        except Exception as e:
            db.rollback()
            logger.error(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新数据失败，已回退")

    # TODO 自定义单条记录删除方法
    def delete(self, db: Session, user, obj):
        try:
            obj.state = 0
            obj.deleted_by_id = int(user['id']) if user else None
            obj.deleted_time = self.now_time
            db.commit()
            # db.refresh(obj)
            # db.close()
        except Exception as e:
            db.rollback()
            logger.error(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除数据失败，已回退")

    # TODO 自定义批量记录新增方法
    def batch_create(self, db: Session, user, obj_list):
        try:
            for obj in obj_list:
                obj.state = 1
                obj.create_by_id = user['id'] if user else None
                obj.create_time = self.now_time
            db.add_all(obj_list)
            db.commit()
            # db.close()
        except Exception as e:
            db.rollback()
            logger.error(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建数据失败，已回退")



    # TODO 自定义批量记录更新方法
    def batch_update(self, db: Session, user, obj_list):
        try:
            for obj in obj_list:
                obj.change_by_id = user['id'] if user else None
                obj.last_change_time = self.now_time
            db.commit()
            # db.close()
        except Exception as e:
            db.rollback()
            logger.error(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新数据失败，已回退")


    # TODO 自定义批量记录删除方法
    def batch_delete(self, db: Session, user, obj_list):
        try:
            for obj in obj_list:
                obj.state = 0
                obj.deleted_time = self.now_time
                obj.deleted_by_id = user['id'] if user else None
            db.commit()
            # db.close()
        except Exception as e:
            db.rollback()
            logger.error(e)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除数据失败，已回退")
