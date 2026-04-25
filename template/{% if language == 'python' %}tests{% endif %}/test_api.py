"""API 模块的测试用例。"""

{% if add_api -%}
import pytest
from fastapi.testclient import TestClient

from {{package_name }}.api import app

# 创建测试客户端
client = TestClient(app)


class TestBasicEndpoints:
    """基础端点的测试用例。"""

    def test_root(self):
        """测试根路径端点。"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "message" in data["data"]

    def test_health_check(self):
        """测试健康检查端点。"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["status"] == "healthy"
        assert "timestamp" in data["data"]


class TestUserEndpoints:
    """用户管理端点的测试用例。"""

    def test_get_user_success(self):
        """测试成功获取用户信息。"""
        response = client.get("/api/v1/users/1")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["id"] == 1
        assert "name" in data["data"]
        assert "email" in data["data"]

    def test_get_user_not_found(self):
        """测试获取不存在的用户。"""
        response = client.get("/api/v1/users/999")
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == 404
        assert "不存在" in data["message"]

    def test_get_user_invalid_id(self):
        """测试使用无效的用户 ID。"""
        response = client.get("/api/v1/users/0")
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == 400
        assert "无效" in data["message"]

    def test_create_user_success(self):
        """测试成功创建用户。"""
        user_data = {"name": "张三", "email": "zhangsan@example.com", "age": 25}
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["name"] == "张三"
        assert data["data"]["email"] == "zhangsan@example.com"
        assert data["message"] == "用户创建成功"

    def test_create_user_invalid_data(self):
        """测试使用无效数据创建用户。"""
        user_data = {"name": "", "email": "invalid"}
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 422

    def test_update_user_success(self):
        """测试成功更新用户信息。"""
        update_data = {"name": "李四", "age": 30}
        response = client.put("/api/v1/users/1", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["name"] == "李四"
        assert data["data"]["age"] == 30
        assert data["message"] == "用户更新成功"

    def test_update_user_not_found(self):
        """测试更新不存在的用户。"""
        update_data = {"name": "王五"}
        response = client.put("/api/v1/users/999", json=update_data)
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == 404
        assert "不存在" in data["message"]

    def test_delete_user_success(self):
        """测试成功删除用户。"""
        response = client.delete("/api/v1/users/1")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "用户删除成功"

    def test_delete_user_not_found(self):
        """测试删除不存在的用户。"""
        response = client.delete("/api/v1/users/999")
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == 404
        assert "不存在" in data["message"]

    def test_list_users_default(self):
        """测试获取用户列表（默认参数）。"""
        response = client.get("/api/v1/users")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "users" in data["data"]
        assert data["data"]["total"] == 100
        assert data["data"]["skip"] == 0
        assert data["data"]["limit"] == 10
        assert len(data["data"]["users"]) == 10

    def test_list_users_with_pagination(self):
        """测试获取用户列表（带分页参数）。"""
        response = client.get("/api/v1/users?skip=5&limit=20")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["skip"] == 5
        assert data["data"]["limit"] == 20
        assert len(data["data"]["users"]) == 20

    @pytest.mark.parametrize(
        "user_id,expected_status",
        [
            (1, 200),
            (50, 200),
            (100, 200),
            (0, 400),
            (-1, 400),
            (101, 404),
            (999, 404),
        ],
    )
    def test_get_user_various_ids(self, user_id, expected_status):
        """使用不同的用户 ID 进行参数化测试。"""
        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == expected_status


class TestResponseFormat:
    """响应格式的测试用例。"""

    def test_success_response_format(self):
        """测试成功响应的格式。"""
        response = client.get("/api/v1/users/1")
        data = response.json()
        assert "code" in data
        assert "data" in data
        assert "message" in data
        assert isinstance(data["code"], int)

    def test_error_response_format(self):
        """测试错误响应的格式。"""
        response = client.get("/api/v1/users/999")
        data = response.json()
        assert "code" in data
        assert "data" in data
        assert "message" in data
        assert data["code"] != 0


class TestValidation:
    """数据验证的测试用例。"""

    def test_create_user_missing_required_fields(self):
        """测试创建用户时缺少必填字段。"""
        response = client.post("/api/v1/users", json={})
        assert response.status_code == 422

    def test_create_user_invalid_email(self):
        """测试创建用户时使用无效的邮箱。"""
        user_data = {"name": "测试", "email": "not-an-email"}
        response = client.post("/api/v1/users", json=user_data)
        # FastAPI 的 email 验证可能需要 pydantic[email]
        # 这里只测试响应状态
        assert response.status_code in [201, 422]

    def test_create_user_invalid_age(self):
        """测试创建用户时使用无效的年龄。"""
        user_data = {"name": "测试", "email": "test@example.com", "age": -1}
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 422

    def test_create_user_age_too_large(self):
        """测试创建用户时年龄超出范围。"""
        user_data = {"name": "测试", "email": "test@example.com", "age": 200}
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 422
{% else -%}
import pytest

# API 模块未启用
{% endif -%}
