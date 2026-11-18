"""测试包本身的基本属性。"""

from {{package_name}} import __version__, add, greet


def test_version():
    """测试版本号是否已定义。"""
    assert __version__ == "{{ version_escaped }}"


def test_exports():
    """测试预期的函数是否已导出。"""
    assert callable(greet)
    assert callable(add)
