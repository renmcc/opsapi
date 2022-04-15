#!/usr/bin/env python
#coding:utf-8
#__time__: 2021/4/6 18:44
#__author__ = 'ren_mcc'

from sqlalchemy import String, Column, SmallInteger, DateTime, Boolean, Integer, UniqueConstraint, JSON
from db.db_base import BaseModel

class weekly_type(BaseModel):
    # 表名
    _table_name_ = 'weekly_type'
    __table_args__ = ({'comment': '周报类型表'})

    name = Column(String(length=40), nullable=False, comment='类别名称')
    remarks = Column(String(length=200), nullable=True, comment='备注说明')


class weekly_project(BaseModel):
    # 表名
    _table_name_ = 'weekly_project'
    __table_args__ = ({'comment': '周报项目表'})

    name = Column(String(length=40), nullable=False, comment='项目名称')
    remarks = Column(String(length=200), nullable=True, comment='备注说明')


class weekly_report(BaseModel):
    # 表名
    _table_name_ = 'weekly_report'
    __table_args__ = ({'comment': '周报表'})

    start_time = Column(DateTime, nullable=True, comment='开始时间')
    type_id = Column(Integer, nullable=True, comment='类型id')
    applicant = Column(String(length=40), nullable=True, comment='申请人')
    project_id = Column(Integer, nullable=True, comment='项目id')
    operation_text = Column(String(length=500), nullable=True, comment='操作内容')
    result = Column(String(length=40), nullable=True, comment='处理结果')

