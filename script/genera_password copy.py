from passlib.context import CryptContext


"""加密方式"""
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return pwd_context.hash(password)


ret = get_password_hash("secret")
print(ret)

ret2 = pwd_context.verify(
    "secret", "$2b$12$ExpV4Oc.DyIWJ4fhXACZfeaR/RymWRrF5YImLvP3tkM1I0khxwZki")
print(ret2)
