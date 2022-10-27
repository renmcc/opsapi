import hashlib
from core.config import SECRET_KEY

__author__ = 'ren_mcc'


def md5_encrypt(pwd: str):

    md5_hash = hashlib.md5()
    if pwd:
        pwd = pwd.encode("utf8")
    md5_hash.update(pwd)
    return md5_hash.hexdigest()


def sha1_encrypt(pwd: str):

    sha1_hash = hashlib.sha1()
    if pwd:
        pwd = pwd.encode('utf8')
    sha1_hash.update(pwd)
    return sha1_hash.hexdigest()


def encrypt_password(pwd: str, loginname: str):
    """加密密码"""
    # 先用 md5 加密
    md5_value = md5_encrypt(pwd + SECRET_KEY)
    # 再用 sha1 加密
    final_pwd = sha1_encrypt(md5_value + loginname)

    return final_pwd


a = encrypt_password("910202", "admin")
print(a)