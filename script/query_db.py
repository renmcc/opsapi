import sys
import os
from pathlib import Path

project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, project_dir)

from db.session import SessionLocal
from sqlalchemy.orm import aliased
from sqlalchemy.orm import Session
from public.str_utils import encrypt_password
from public.data_utils import get_tree_data, orm_one_to_dict, sql_all_to_dict, orm_all_to_dict
from apps.system.model import SysUser, SysRole
from apps.system.model import SysMenu as Menu, SysRoleMenu as roleMenu


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


db: Session = get_db()

# session_user = db.query(SysUser.id, SysUser.account, SysUser.user_name, SysUser.role_id).filter(
#     SysUser.account == "test1", SysUser.password == encrypt_password("123")).first()
# user = orm_one_to_dict(session_user)
# print(user)


# all_menu_list = db.query(Menu.id, Menu.parent_id, Menu.menu_name, Menu.menu_code, Menu.menu_url, Menu.menu_icon,
#                          Menu.menu_type).join(roleMenu, Menu.id == roleMenu.menu_id).filter(
#     roleMenu.state == 1, Menu.state == 1, roleMenu.role_id == 1).order_by('idx').all()
#
# ret = orm_one_to_dict(all_menu_list)
# print(ret)

# db_dept = db.execute("select c.id, c.department_name, c.parent_id, c.idx, c.remarks, p.department_name "
#                      "as parent_name from sys_department as c left join sys_department as p on "
#                      "p.id=c.parent_id where c.state=1 and c.id=:cid;", params={'cid': 1})

#
# db_dept = db.query(Dept.id, Dept.department_name, Dept.parent_id, Dept.remarks).filter(Dept.state == 1, Dept.id == 1).order_by('id').scalar()
#
# ret = orm_one_to_dict(db_dept)
# print(ret)


# db_dept = db.query(Dept.department_name, Dept.remarks, Dept.parent_id, ).filter(Dept.id == 1, Dept.state == 1).first()
# ret = orm_one_to_dict(db_dept)
# print(db_dept)
a = aliased(SysRole)
b = aliased(SysUser)
c = aliased(SysUser)
db_dept = db.query(a.id, a.role_name, b.account.label("create_by_user"), c.account.label("chage_by_user")).outerjoin(b, a.create_by_id == b.id).outerjoin(c, a.change_by_id == c.id).filter(a.state == 1).all()
ret = orm_all_to_dict(db_dept)
print(ret)
