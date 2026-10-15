import os

os.environ["LANGGRAPH_STRICT_MSGPACK"] = "true"

from fastapi import FastAPI  # 从 FastAPI 框架导入 FastAPI 类，用来创建 Web 应用实例
from app.models.user import (
    User,
)  # 导入 User 模型；虽然这里没有直接使用它，但导入后 SQLAlchemy 才会把 User 注册到 Base.metadata
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.models.reservation import Reservation
from app.models.reservation_idempotency import ReservationIdempotency
from app.database import (
    Base,
    engine,
)  # 从 app.database 导入 Base 基类和 engine 数据库引擎
from app.api import api  # 导入 api 模块，里面包含了所有的路由器
from app.common.exceptions import (
    BusinessException,
    business_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import UPLOAD_DIR
from app.config import settings
from app.services import ai_service
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
import asyncio
from app.services import reservation_service
from contextlib import asynccontextmanager

Base.metadata.create_all(
    bind=engine
)  # 根据 Base 中收集到的所有模型元数据，在 engine 对应的数据库中创建尚不存在的表


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(
        reservation_service.run_expire_scan()
    )  # 启动项目开启异步的扫描任务
    try:
        if settings.AI_ENABLED:
            settings.AI_CHECKPOINT_DB.parent.mkdir(parents=True, exist_ok=True)
            async with AsyncSqliteSaver.from_conn_string(
                str(settings.AI_CHECKPOINT_DB)
            ) as checkpointer:
                await checkpointer.setup()
                app.state.ai_graph = ai_service.compile_graph(checkpointer)
                yield
        else:
            app.state.ai_graph = None
            yield
    finally:
        task.cancel()  # 关闭项目同时取消异步任务
        try:
            await task
        except asyncio.CancelledError:
            pass
        app.state.ai_graph = None


app = FastAPI(lifespan=lifespan)  # 创建 FastAPI 应用实例，后续路由都注册到这个 app 上

# 配置 CORS 中间件，允许前端跨域请求
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许的前端源，不要直接写 ["*"]
    allow_credentials=True,  # ✅ 关键：允许前端携带 Authorization token
    allow_methods=["*"],  # 允许所有请求方法 GET POST PUT DELETE OPTIONS
    allow_headers=["*"],  # 允许所有请求头（包含Authorization）
)

app.include_router(
    api
)  # 将 api 路由器注册到 app 上，所有 /api 开头的请求都会交给 api 处理

# 注册全局异常处理器
app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
# 注册全局异常处理器，捕获所有未被捕获的异常，最后注册默认异常处理器
app.add_exception_handler(Exception, global_exception_handler)

# 挂载静态资源：/uploads/xxx.jpg → uploads/xxx.jpg
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")  # 用装饰器注册一个 GET 请求路由，访问路径是根路径 /
def root():  # 定义处理根路径请求的函数，函数名可以自定义
    return {
        "message": "FastAPI正在运行中！"
    }  # 返回字典，FastAPI 会自动把它序列化为 JSON 响应


# uvicorn app.main:app --reload 终端命令启动服务器
