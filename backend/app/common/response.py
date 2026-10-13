from typing import Any  # 从 typing 模块导入 Any，表示“任意类型”的类型注解
from pydantic import BaseModel  # 从 pydantic 导入 BaseModel，用它定义可校验的数据模型


class Response(BaseModel):  # 定义 Response 类，继承 BaseModel，表示统一响应结构
    """统一封装的返回格式"""

    code: int  # 响应状态码，声明为整数，Pydantic 会做类型校验
    message: str  # 响应提示信息，声明为字符串
    data: Any = None  # 响应携带的数据，类型任意，默认值为 None

    @classmethod  # 装饰器：把下面的方法标记为类方法，可通过类名直接调用
    def success(
        cls, message: str = "请求成功", data: Any = None
    ):  # 成功响应工厂方法；cls 代表当前类，message/data 有默认值
        return cls(
            code=200, message=message, data=data
        )  # 使用当前类创建实例，固定成功码 200，并传入消息和数据

    @classmethod  # 装饰器：把下面的方法标记为类方法
    def error(
        cls, code: int = 500, message: str = "请求失败"
    ):  # 失败响应工厂方法；默认错误码 500，默认消息“请求失败”
        return cls(
            code=code, message=message
        )  # 使用当前类创建实例，data 不传则使用默认值 None


class PageResponse(BaseModel):
    """分页的返回结果"""

    list: Any = []
    total: int = 0
