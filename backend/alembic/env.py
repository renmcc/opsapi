import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")

from core import config as db_conf
from db.migrate_db import BaseDB
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# 自定义
__author__ = 'ren_mcc'

# 在此添加model后，让程序自动生成
target_metadata = BaseDB.metadata

# 这是Alembic Config对象，它提供访问正在使用的.ini文件中的值。
config = context.config

# 记录日志文件
fileConfig(config.config_file_name)


# 还可获取在config中定义的其他配置值，获取方式
# value = config.get_main_option("设置的key")


def run_migrations_offline():
    # MySQL 连接
    url = db_conf.DB_CONN_URI
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section)
    configuration['sqlalchemy.url'] = db_conf.DB_CONN_URI
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        """
        设置compare_type为True可以检查出类型字段的改变比如字段长度
        设置compare_server_default可以检查出设置的字段默认值的改变
        """
        context.configure(connection=connection, target_metadata=target_metadata,
                          compare_type=True, compare_server_default=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

