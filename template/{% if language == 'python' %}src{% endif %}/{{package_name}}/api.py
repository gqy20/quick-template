"""FastAPI 应用示例 - 展示标准 API 开发规范。

本模块提供一个规范的 FastAPI 应用示例，包括：
- 统一的响应格式
- RESTful API 设计
- 请求/响应模型验证
- 完整的错误处理
- 日志记录
- API 文档
"""

{% if add_api -%}
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from {{package_name }}.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)


# ==================== 生命周期管理 ====================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    # 启动时执行
    logger.info("FastAPI 应用启动")
    yield
    # 关闭时执行
    logger.info("FastAPI 应用关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="{{project_name }} API",
    description="{{description }}",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan,
)


# ==================== 响应模型 ====================


class ResponseCode(int, Enum):
    """API 响应状态码枚举。"""

    SUCCESS = 0  # 成功
    INVALID_PARAMS = 400  # 参数错误
    NOT_FOUND = 404  # 资源不存在
    SERVER_ERROR = 500  # 服务器错误


class ApiResponse(BaseModel):
    """统一的 API 响应格式。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": 0,
                "data": {"id": 1, "name": "示例"},
                "message": "成功",
            }
        }
    )

    code: int = Field(default=ResponseCode.SUCCESS, description="状态码，0 表示成功")
    data: Any | None = Field(default=None, description="响应数据")
    message: str = Field(default="成功", description="响应消息")


# ==================== 请求/响应模型 ====================


class UserCreate(BaseModel):
    """创建用户请求模型。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"name": "张三", "email": "zhangsan@example.com", "age": 25}
        }
    )

    name: str = Field(..., min_length=1, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱地址")
    age: int | None = Field(None, ge=0, le=150, description="年龄")


class UserResponse(BaseModel):
    """用户响应模型。"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "name": "张三",
                "email": "zhangsan@example.com",
                "age": 25,
                "created_at": "2024-01-01T12:00:00",
            }
        }
    )

    id: int = Field(..., description="用户 ID")
    name: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱地址")
    age: int | None = Field(None, description="年龄")
    created_at: datetime = Field(..., description="创建时间")


class UserUpdate(BaseModel):
    """更新用户请求模型。"""

    model_config = ConfigDict(
        json_schema_extra={"example": {"name": "李四", "age": 30}}
    )

    name: str | None = Field(None, min_length=1, max_length=50, description="用户名")
    email: str | None = Field(None, description="邮箱地址")
    age: int | None = Field(None, ge=0, le=150, description="年龄")


# ==================== 全局异常处理 ====================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """处理 HTTP 异常。"""
    logger.error(f"HTTP 异常: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "data": None,
            "message": exc.detail,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理一般异常。"""
    logger.error(f"服务器错误: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": ResponseCode.SERVER_ERROR,
            "data": None,
            "message": "服务器内部错误",
        },
    )


# ==================== 中间件 ====================


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求。"""
    logger.info(f"请求: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"响应: {response.status_code}")
    return response


# ==================== API 端点 ====================


@app.get(
    "/",
    response_model=ApiResponse,
    summary="根路径",
    description="API 根路径，返回欢迎信息",
)
async def root():
    """根路径端点。"""
    return ApiResponse(data={"message": "欢迎使用 {{project_name }} API"})


@app.get(
    "/api/v1/health",
    response_model=ApiResponse,
    summary="健康检查",
    description="检查 API 服务是否正常运行",
    tags=["系统"],
)
async def health_check():
    """健康检查端点。"""
    logger.info("执行健康检查")
    return ApiResponse(
        data={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.get(
    "/api/v1/users/{user_id}",
    response_model=ApiResponse,
    summary="获取用户",
    description="根据用户 ID 获取用户信息",
    tags=["用户管理"],
)
async def get_user(user_id: int):
    """获取单个用户信息。

    Args:
        user_id: 用户 ID

    Returns:
        包含用户信息的响应

    Raises:
        HTTPException: 用户不存在时抛出 404 错误
    """
    logger.info(f"获取用户信息: user_id={user_id}")

    # 模拟数据库查询
    if user_id <= 0:
        logger.warning(f"无效的用户 ID: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="无效的用户 ID"
        )

    if user_id > 100:
        logger.warning(f"用户不存在: user_id={user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    user = UserResponse(
        id=user_id,
        name=f"用户{user_id}",
        email=f"user{user_id}@example.com",
        age=20 + user_id,
        created_at=datetime.now(),
    )

    logger.info(f"成功获取用户: {user.name}")
    return ApiResponse(data=user.model_dump())


@app.post(
    "/api/v1/users",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建用户",
    description="创建新用户",
    tags=["用户管理"],
)
async def create_user(user: UserCreate):
    """创建新用户。

    Args:
        user: 用户创建请求数据

    Returns:
        包含新创建用户信息的响应
    """
    logger.info(f"创建用户: name={user.name}, email={user.email}")

    # 模拟创建用户
    new_user = UserResponse(
        id=1,
        name=user.name,
        email=user.email,
        age=user.age,
        created_at=datetime.now(),
    )

    logger.info(f"成功创建用户: id={new_user.id}, name={new_user.name}")
    return ApiResponse(data=new_user.model_dump(), message="用户创建成功")


@app.put(
    "/api/v1/users/{user_id}",
    response_model=ApiResponse,
    summary="更新用户",
    description="更新用户信息",
    tags=["用户管理"],
)
async def update_user(user_id: int, user: UserUpdate):
    """更新用户信息。

    Args:
        user_id: 用户 ID
        user: 用户更新请求数据

    Returns:
        包含更新后用户信息的响应

    Raises:
        HTTPException: 用户不存在时抛出 404 错误
    """
    logger.info(f"更新用户: user_id={user_id}")

    # 模拟检查用户是否存在
    if user_id > 100:
        logger.warning(f"用户不存在: user_id={user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 模拟更新用户
    updated_user = UserResponse(
        id=user_id,
        name=user.name or f"用户{user_id}",
        email=user.email or f"user{user_id}@example.com",
        age=user.age or 25,
        created_at=datetime.now(),
    )

    logger.info(f"成功更新用户: id={updated_user.id}, name={updated_user.name}")
    return ApiResponse(data=updated_user.model_dump(), message="用户更新成功")


@app.delete(
    "/api/v1/users/{user_id}",
    response_model=ApiResponse,
    summary="删除用户",
    description="删除指定用户",
    tags=["用户管理"],
)
async def delete_user(user_id: int):
    """删除用户。

    Args:
        user_id: 用户 ID

    Returns:
        删除成功的响应

    Raises:
        HTTPException: 用户不存在时抛出 404 错误
    """
    logger.info(f"删除用户: user_id={user_id}")

    # 模拟检查用户是否存在
    if user_id > 100:
        logger.warning(f"用户不存在: user_id={user_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 模拟删除用户
    logger.info(f"成功删除用户: user_id={user_id}")
    return ApiResponse(message="用户删除成功")


@app.get(
    "/api/v1/users",
    response_model=ApiResponse,
    summary="获取用户列表",
    description="获取所有用户列表（支持分页）",
    tags=["用户管理"],
)
async def list_users(skip: int = 0, limit: int = 10):
    """获取用户列表。

    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数

    Returns:
        包含用户列表的响应
    """
    logger.info(f"获取用户列表: skip={skip}, limit={limit}")

    # 模拟分页查询
    users = [
        UserResponse(
            id=i,
            name=f"用户{i}",
            email=f"user{i}@example.com",
            age=20 + i,
            created_at=datetime.now(),
        )
        for i in range(skip + 1, skip + limit + 1)
    ]

    logger.info(f"成功获取 {len(users)} 个用户")
    return ApiResponse(
        data={
            "total": 100,
            "skip": skip,
            "limit": limit,
            "users": [user.model_dump() for user in users],
        }
    )


# ==================== 主函数 ====================


def main():
    """运行 FastAPI 应用。

    使用 uvicorn 启动服务器。
    """
    import uvicorn

    logger.info("启动 FastAPI 服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


if __name__ == "__main__":
    main()
{% endif -%}
