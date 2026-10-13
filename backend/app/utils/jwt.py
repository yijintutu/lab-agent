from datetime import (
    datetime,
    timedelta,
)  # 从 datetime 模块导入 datetime 类（获取当前时间）和 timedelta 类（表示时间间隔）
import jwt  # 导入 PyJWT 库，用来生成和解析 JWT
from app.config import (
    settings,
)  # 从项目配置模块导入 settings，里面保存 JWT 密钥、算法、过期小时数等配置


def create_access_token(
    user_id: int,
) -> str:  # 定义创建访问令牌的函数：接收用户 ID，返回字符串类型的 token
    """创建JWT token"""  # 函数的文档字符串，说明这个函数用于创建 JWT token
    expire = datetime.now() + timedelta(
        hours=settings.JWT_EXPIRE_HOURS
    )  # 计算过期时间：当前时间 + 配置的过期小时数

    payload = {
        "user_id": user_id,
        "exp": expire,
    }  # exp是固定key，不能写成别的；构造 JWT 负载，user_id 是自定义用户标识，exp 是标准过期时间字段

    return jwt.encode(  # 调用 jwt.encode 生成 JWT，并把结果作为字符串返回
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,  # 传入负载、签名密钥和签名算法
    )  # jwt.encode 调用结束


def decode_access_token(
    token: str,
) -> dict:  # 定义解析访问令牌的函数：接收 token 字符串，返回解析后的字典
    """解析jwt token"""  # 函数的文档字符串，说明这个函数用于解析 JWT token
    return jwt.decode(  # 调用 jwt.decode 解析 token，并返回其中的负载数据
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],  # 传入 token、密钥，以及允许使用的算法列表
    )  # jwt.decode 调用结束
