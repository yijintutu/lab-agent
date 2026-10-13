from fastapi import APIRouter, Depends
from app.common.response import Response
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.user import (
    UserResponse,
    UserUpdateRequest,
    PasswordUpdateRequest,
    UserCreateRequest,
)
from app.services import user_service
from app.database import get_db
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_admin

router = APIRouter(prefix="/user", tags=["用户信息接口"])


@router.get("/me", tags=["用户信息接口"])
def api_get_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return Response.success(data=user_service.get_user_info(current_user))


@router.put("/me")
def api_update_user_info(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前登录用户信息"""
    res = user_service.update_user_info(db, current_user, data)
    return Response.success(data=res)


@router.put("/me/password")
def api_update_user_password(
    data: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前登录用户密码"""
    res = user_service.update_user_password(db, current_user, data)
    return Response.success(data=res)


@router.get("/list")
def get_user_list(
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.get_user_page_list(db, page, page_size, keywords)
    return Response.success(data=res)


@router.post("")
def create_user(
    data: UserCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.create_user(db, data)
    return Response.success(data=res)


@router.put("/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.update_user(db, user_id, data)
    return Response.success(data=res)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    res = user_service.delete_user(db, user_id, current_user)
    return Response.success()


# http://127.0.0.1:8000/api/auth/login   POST 登录接口地址
# http://127.0.0.1:8000/api/user/me   GET 获取当前登录用户信息接口地址
# http://127.0.0.1:8000/api/user/me   PUT 更新当前登录用户信息接口地址
# http://127.0.0.1:8000/api/user/me/password   PUT 更新当前登录用户密码接口地址
# http://127.0.0.1:8000/api/user/me/avatar   PUT 上传当前登录用户头像接口地址
