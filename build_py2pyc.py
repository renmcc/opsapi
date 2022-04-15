# build_py2pyc.py

import datetime
from pathlib import Path
import os
import sys
import shutil
import compileall


def package(root_path="./test_project/", version="1.0.0"):
    """
    编译项目目录包括子目录里的所有py文件成pyc文件到新的文件夹下
    :param root_path: 需编译的目录
    :version: 项目版本号
    :return:
    """
    root = Path(root_path)
    dest = Path(root.parent / f"{root.name}_{version}")  # 目标文件夹名称

    if os.path.exists(dest):
        shutil.rmtree(dest)

    shutil.copytree(root, dest)  # 复制开发项目到发布项目

    # 先删除发布项目目录下的pyc文件和__pycache__文件夹
    for src_file in dest.rglob("*.pyc"):
        os.remove(src_file)
    for src_file in dest.rglob("__pycache__"):
        shutil.rmtree(src_file)

    compileall.compile_dir(dest, force=True)  # 将项目下的py都编译成pyc文件

    for src_file in dest.glob("**/*.pyc"):  # 遍历所有pyc文件
        relative_path = src_file.relative_to(dest)  # pyc文件对应模块文件夹名称
        # 在目标文件夹下创建同名模块文件夹
        dest_folder = dest / str(relative_path.parent.parent)
        os.makedirs(dest_folder, exist_ok=True)
        dest_file = dest_folder / \
            (src_file.stem.rsplit(".", 2)[0] + src_file.suffix)  # 创建同名文件
        print(f"install {relative_path}")
        shutil.copyfile(src_file, dest_file)  # 将pyc文件复制到同名文件

    # 清除源py文件
    for src_file in dest.rglob("*.py"):
        os.remove(src_file)
    # 清除__pycache__文件夹
    for src_file in dest.rglob("__pycache__"):
        shutil.rmtree(src_file)


if __name__ == '__main__':
    # 指定项目目录和发布的版本号
    package(root_path="./backend", version="1.0.0")
