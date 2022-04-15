#!/usr/bin/env python
#coding:utf-8
#__time__: 2021/4/6 18:41
#__author__ = 'ren_mcc'

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime

class WeeklyTypeRequestForm(BaseModel):
    name: Optional[str] = Field(..., min_length=1, max_length=10, title="处理类型名称", description="处理类型名称")
    remarks: Optional[str] = Field(..., min_length=0, max_length=50, title="描述", description="描述")

    class Config:
        schema_extra = {
            "example": {
                "name": "系统数据统计",
                "remarks": ""
            }
        }


class WeeklyProjectRequestForm(BaseModel):
    name: Optional[str] = Field(..., min_length=1, max_length=20, title="处理项目名称", description="处理项目名称")
    remarks: Optional[str] = Field(..., min_length=0, max_length=50, title="描述", description="描述")

    class Config:
        schema_extra = {
            "example": {
                "name": "阿里云法眼",
                "remarks": ""
            }
        }


class WeeklyReportRequestForm(BaseModel):
    start_time: Optional[datetime] = Field(..., title="处理开始时间", description="处理开始时间")
    type_id: Optional[int] = Field(None, ge=0, le=100, title="处理类型id", description="处理类型id")
    applicant: Optional[str] = Field(..., min_length=1, max_length=10, title="申请人或报告人", description="申请人或报告人")
    project_id: Optional[int] = Field(None, ge=0, le=100, title="处理项目id", description="处理项目id")
    operation_text: Optional[str] = Field(..., min_length=0, max_length=500, title="操作内容", description="操作内容")
    result: Optional[str] = Field(..., min_length=0, max_length=10, title="处理结果", description="处理结果")

    class Config:
        schema_extra = {
            "example": {
                "start_time": "2021-04-07 11:11:11",
                "type_id": 1,
                "applicant": "某某",
                "project_id": 1,
                "operation_text": "明细统计",
                "result": "完成工单"
            }
        }


class WeeklyReportUpdateRequestForm(BaseModel):
    id: Optional[int] = Field(..., ge=1, title="id", description="id")
    start_time: Optional[datetime] = Field(..., title="处理开始时间", description="处理开始时间")
    type_id: Optional[int] = Field(None, ge=0, le=100, title="处理类型id", description="处理类型id")
    applicant: Optional[str] = Field(..., min_length=1, max_length=10, title="申请人或报告人", description="申请人或报告人")
    project_id: Optional[int] = Field(None, ge=0, le=100, title="处理项目id", description="处理项目id")
    operation_text: Optional[str] = Field(..., min_length=0, max_length=500, title="操作内容", description="操作内容")
    result: Optional[str] = Field(..., min_length=0, max_length=10, title="处理结果", description="处理结果")

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "start_time": "2021-04-07 11:11:11",
                "type_id": 1,
                "applicant": "某某",
                "project_id": 1,
                "operation_text": "明细统计",
                "result": "完成工单"
            }
        }