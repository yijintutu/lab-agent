from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)  # 导入类型映射标记 Mapped 和列映射函数 mapped_column，用于声明模型字段
from sqlalchemy import String  # 导入字符串列类型 String，对应数据库中的 VARCHAR
from app.database import (
    Base,
)  # 导入项目公共基类 Base，User 继承后自动拥有 id、create_time、update_time 等公共字段


class User(Base):  # 定义 User 模型类，继承 Base，对应数据库中的用户表
    __tablename__ = "users"  # 指定该模型映射到数据库中的表名 users
    __table_args__ = {
        "comment": "用户信息表"
    }  # 设置表级参数，这里给 users 表添加数据库注释“用户信息表”

    username: Mapped[str] = mapped_column(
        String(50), comment="账号", nullable=False
    )  # 账号字段，字符串最大长度 50，非空，列注释为“账号”
    password: Mapped[str] = mapped_column(
        String(255), comment="密码", nullable=False
    )  # 密码字段，字符串最大长度 255，非空，列注释为“密码”
    name: Mapped[str] = mapped_column(
        String(50), comment="名称", nullable=False
    )  # 名称字段，字符串最大长度 50，非空，列注释为“名称”
    role: Mapped[str] = mapped_column(  # 开始定义角色字段，Python 类型为字符串
        String(50),
        comment="角色：student-用户，admin-管理员",
        nullable=False,  # 字符串最大长度 50，非空，列注释说明角色取值含义
    )  # 角色字段定义结束
    email: Mapped[str | None] = mapped_column(
        String(50), comment="邮箱"
    )  # 邮箱字段，可为空；Mapped[str | None] 让 SQLAlchemy 推断该列允许 NULL
    phone: Mapped[str | None] = mapped_column(
        String(50), comment="手机号"
    )  # 手机号字段，可为空；最大长度 50，列注释为“手机号”
    avatar: Mapped[str | None] = mapped_column(
        String(50), comment="头像"
    )  # 头像字段，可为空；最大长度 50，列注释为“头像”
    status: Mapped[int] = mapped_column(
        default=1, comment="状态：0-禁用，1-正常"
    )  # 状态字段，整数类型由 Mapped[int] 推断；默认值为 1，列注释说明 0 禁用、1 正常
