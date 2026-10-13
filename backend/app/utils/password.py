import bcrypt  # 导入 bcrypt 库，用来对密码做安全的哈希处理和校验


def hash_password(
    password: str,
) -> str:  # 定义函数：接收明文密码字符串，返回哈希后的字符串
    """对密码加密"""  # 函数文档字符串，说明这个函数用于处理密码；严格来说 bcrypt 是哈希，不是可逆加密
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )  # 把明文密码转成字节，生成随机盐，计算 bcrypt 哈希，再把字节结果转成字符串返回


def verify_password(
    password: str, hashed_password: str
) -> bool:  # 定义函数：接收用户输入的明文密码和数据库保存的哈希密码，返回布尔值
    """验证密码的有效性"""  # 第一个函数文档字符串，说明这个函数用于验证密码是否正确
    """  "123" -> "xxsdasdasdasfa"  """  # 这是一个普通字符串表达式，不是第二个文档字符串，也不会参与验证逻辑，只是放在这里没有实际作用
    return bcrypt.checkpw(
        password.encode("utf-8"), hashed_password.encode("utf-8")
    )  # 把明文密码和已保存的哈希密码都转成字节，交给 bcrypt 安全比对，返回 True 或 False
