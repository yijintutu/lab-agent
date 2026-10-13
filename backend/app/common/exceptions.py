from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.common.response import Response


class BusinessException(Exception):
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(message)


async def business_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, BusinessException)
    return JSONResponse(
        status_code=200,
        content=Response.error(code=exc.code, message=exc.message).model_dump(),
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, HTTPException)
    return JSONResponse(
        status_code=exc.status_code,
        content=Response.error(code=exc.status_code, message=exc.detail).model_dump(),
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return JSONResponse(
        status_code=422,
        content=Response.error(code=422, message="请求参数校验错误").model_dump(),
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=Response.error(code=500, message="服务器内部错误").model_dump(),
    )


# 教程代码有问题已经注释掉
'''from fastapi import (
    HTTPException,
    Request,
)  # 导入 FastAPI 的 HTTPException 异常类和 Request 请求对象类型
from fastapi.exceptions import (
    RequestValidationError,
)  # 导入请求参数校验失败时抛出的 RequestValidationError
from fastapi.responses import (
    JSONResponse,
)  # 导入 JSONResponse，用于返回 JSON 格式的 HTTP 响应

from app.common.response import (
    Response,
)  # 导入项目统一响应模型 Response，提供 success/error 等构造方法


class BusinessException(Exception):  # 定义自定义业务异常类，继承 Python 内置 Exception
    """自定义的业务异常"""

    def __init__(
        self, message: str, code: int = 500
    ):  # 初始化方法；message 是错误信息，code 是业务错误码，默认 500
        self.message = message  # 把错误信息保存到实例属性，便于处理器读取
        self.code = code  # 把业务错误码保存到实例属性，便于处理器读取
        super().__init__(
            message
        )  # 调用父类 Exception 的初始化方法，让异常本身携带 message


async def bussiness_excpetion_hadler(
    request: Request, exc: BusinessException
):  # 异步处理自定义业务异常；request 是请求对象，exc 是捕获到的异常
    """自定义业务异常处理器"""
    return JSONResponse(  # 返回一个 JSON 响应对象
        status_code=200,  # HTTP 状态码设为 200，表示请求已被服务器正常接收；业务成败看 body 里的 code
        content=Response.error(
            code=exc.code, message=exc.message
        ).model_dump(),  # 用统一错误格式构造响应，并转成字典
    )  # 结束 JSONResponse 构造


async def http_excpetion_hadler(
    request: Request, exc: HTTPException
):  # 异步处理 FastAPI/Starlette 的 HTTPException
    """Http异常处理器"""
    return JSONResponse(  # 返回 JSON 响应对象
        status_code=exc.status_code,  # HTTP 状态码沿用 HTTPException 自带的 status_code
        content=Response.error(
            code=exc.status_code, message=exc.detail
        ).model_dump(),  # 把异常详情包装成统一错误响应
    )  # 结束 JSONResponse 构造


async def validation_excpetion_hadler(
    request: Request, exc: RequestValidationError
):  # 异步处理请求参数校验异常
    """参数异常处理器"""  # 函数文档字符串，说明该函数负责处理 RequestValidationError
    return JSONResponse(  # 返回 JSON 响应对象
        status_code=422,  # HTTP 状态码设为 422，表示请求参数校验失败
        content=Response.error(
            code=422, message="请求参数校验错误"
        ).model_dump(),  # 返回统一的参数错误提示
    )  # 结束 JSONResponse 构造


async def global_excpetion_hadler(
    request: Request, exc: Exception
):  # 异步处理所有未被前面处理器捕获的异常
    """全局异常处理器"""  # 函数文档字符串，说明该函数是全局兜底异常处理器
    return JSONResponse(  # 返回 JSON 响应对象
        status_code=500,  # HTTP 状态码设为 500，表示服务器内部错误
        content=Response.error(
            code=500, message="服务器内部错误"
        ).model_dump(),  # 返回统一的服务器错误提示，避免泄露内部细节
    )  # 结束 JSONResponse 构造
'''
