from fastapi import (
    Depends,
    HTTPException,
    status,
)  # 导入 FastAPI 的依赖注入、HTTP 异常和状态码常量
from fastapi.security import (
    OAuth2PasswordBearer,
)  # 导入 OAuth2 密码承载认证工具，用于从请求头提取 Bearer token
from sqlalchemy.orm import (
    Session,
)  # 导入 SQLAlchemy 的 Session 类型，用于数据库会话类型标注

from app.database import get_db  # 导入数据库会话依赖函数，FastAPI 会通过它注入 Session
from app.models.user import User  # 导入用户 ORM 模型，用于查询用户表
from app.utils.jwt import decode_access_token  # 导入之前实现的 JWT 解码函数
from app.common.exceptions import BusinessException

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login"  # 登录接口地址
)  # 创建 OAuth2 认证方案，告诉 FastAPI 从 Authorization: Bearer <token> 中取 token；tokenUrl 是登录接口地址（原代码这里拼写为 auth）


# 获取当前登录用户，并验证 JWT token 的合法性，返回查询到的用户对象，供后续接口使用
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:  # 函数返回 User 类型的 ORM 对象
    """JWT token 鉴权验证合法性"""
    try:  # 开始捕获 JWT 解码过程中可能出现的异常
        payload = decode_access_token(
            token
        )  # 调用 JWT 解码函数，验证签名和过期时间，并取出 payload 字典
    except Exception:  # 捕获所有异常，例如 token 过期、签名错误、格式错误等
        raise HTTPException(  # 抛出 HTTP 401 异常，中断请求
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已失效，请重新登录",  # 状态码 401，提示登录失效
        )  # HTTPException 参数结束
    # 获取到用户ID
    user_id = payload.get(
        "user_id"
    )  # 从 payload 字典中安全读取 user_id 字段，取不到返回 None
    if not user_id:  # 如果 user_id 不存在或为假值，则视为无效凭证
        raise HTTPException(  # 抛出 HTTP 401 异常
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的登录凭证",  # 状态码 401，提示凭证无效
        )  # HTTPException 参数结束
    # 从数据库根据用户ID查询用户信息
    user = (
        db.query(User).filter(User.id == user_id).first()
    )  # 使用 SQLAlchemy 查询 User 表，按 id 过滤，取唯一条记录

    if not user:  # 如果用户不存在，则视为无效凭证
        raise HTTPException(  # 抛出 HTTP 401 异常
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的登录凭证",  # 状态码 401，提示凭证无效
        )

    if user.status != 1:  # 判断用户状态是否不等于 1
        raise HTTPException(  # 抛出 HTTP 401 异常
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户被禁用",  # 状态码 401，提示用户被禁用
        )  # HTTPException 参数结束
    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """只有管理员才能访问"""
    if current_user.role != "admin":
        raise BusinessException(message="无权限访问", code=403)
    return current_user
