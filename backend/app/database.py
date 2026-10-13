from sqlalchemy.orm import (
    sessionmaker,
    DeclarativeBase,
    Mapped,
    mapped_column,
)  # 从 SQLAlchemy ORM 导入：会话工厂、声明式基类、类型映射标记、列映射函数
from sqlalchemy import (
    create_engine,
    DateTime,
)  # 导入创建数据库引擎的函数，以及数据库 DateTime 时间类型
from app.config import settings  # 导入项目配置对象，里面通常保存 DATABASE_URL 等配置
from datetime import datetime  # 导入 Python 的 datetime 类，用于生成当前时间

engine = create_engine(
    settings.DATABASE_URL
)  # 根据配置中的数据库连接字符串创建数据库引擎，负责管理连接池和数据库通信

# 数据库session会话的连接工厂：调用 SessionLocal() 会创建一个新的数据库会话对象
SessionLocal = sessionmaker(
    bind=engine, autoflush=False
)  # 绑定上面的 engine；autoflush=False 表示查询前不自动把未提交数据刷入数据库


def get_db():  # 定义一个依赖函数，用来给每个请求提供独立的数据库会话
    db = SessionLocal()  # 从会话工厂创建一个新的数据库会话对象
    try:  # 使用 try/finally 保证无论后续是否出错，会话都能被关闭
        yield db  # 把会话交给调用方使用；yield 会让函数暂停，等调用方用完后再继续执行 finally
    finally:  # 无论 try 块中是否发生异常，都会执行这里的清理逻辑
        db.close()  # 关闭数据库会话，释放连接资源


class Base(
    DeclarativeBase
):  # 定义所有数据库模型的公共父类，继承 SQLAlchemy 2.0 的声明式基类
    id: Mapped[int] = (
        mapped_column(  # 声明公共主键字段 id，Python 类型是 int，并映射为数据库列
            primary_key=True,
            autoincrement=True,
            comment="主键ID",
            sort_order=-1,  # 主键、自增、数据库注释；sort_order=-1 让 id 在建表时排在第一列
        )
    )  # id 列定义结束
    create_time: Mapped[datetime] = (
        mapped_column(  # 声明公共创建时间字段，Python 类型是 datetime，并映射为数据库列
            DateTime,
            default=datetime.now,
            comment="创建时间",
            sort_order=1,  # 数据库类型为 DateTime；插入时默认调用 datetime.now；注释为创建时间；sort_order=1 让它排在业务字段之后
        )
    )  # create_time 列定义结束
    update_time: Mapped[datetime] = (
        mapped_column(  # 声明公共更新时间字段，Python 类型是 datetime，并映射为数据库列
            DateTime,
            default=datetime.now,
            onupdate=datetime.now,
            comment="更新时间",
            sort_order=2,  # 插入时默认当前时间；更新时自动调用 datetime.now 刷新；注释为更新时间；sort_order=2 让它排在时间字段最后
        )
    )  # update_time 列定义结束
