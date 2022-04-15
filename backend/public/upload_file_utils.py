from fastapi import APIRouter, File, UploadFile, Form, status, HTTPException
from fastapi.responses import JSONResponse
from core import config
import os, time, random
from pathlib import Path

__author__ = 'ren_mcc'
router = APIRouter()


@router.post('/upload_file')
async def upload_file(file: UploadFile = File(...)):
    # TODO 判断文件夹是否定义
    insert_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), config.STATIC_DIR)
    static_dir = Path(insert_file_path)
    if not static_dir.exists():
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="静态文件根目录未创建")

    # TODO 判断上传文件文件大小
    if (file.spool_max_size / 1024 / 1024) > 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="上传的头像不能大于1mb")

    # 插入表的字段的路径
    file_name = '运维管理系统_' + str(time.time()).split('.')[0] + str(random.randrange(1, 999, 3)) + '.' + file.filename.split('.')[len(file.filename.split('.')) - 1]
    # 文件后缀
    # name_suffix = '.' + file.filename.split('.')[len(file.filename.split('.')) - 1]
    # 获取静态文件夹的目录
    if not save_path:
        insert_file_path = os.path.join(insert_file_path, file_name)
        # 返回前端供入库的路径
        file_path = os.path.join(config.STATIC_DIR, file_name)
    else:
        save_path = save_path[1:] if save_path[0] == '/' or save_path[0] == '\\' else save_path
        insert_file_path = os.path.join(os.path.join(insert_file_path, save_path))
        if not os.path.exists(insert_file_path):
            os.makedirs(insert_file_path)
        insert_file_path = os.path.join(insert_file_path, file_name)
        file_path = os.path.join(config.STATIC_DIR, os.path.join(save_path, file_name))
    file_content = await file.read()
    with open(insert_file_path, 'wb') as f:
        f.write(file_content)
    f.close()

    return JSONResponse({'code': status.HTTP_200_OK, 'file_name': file_name, 'file_path': ('/' + file_path).replace('\\', '/')})
