
"""
pytest 测试夹具（Fixture）
定义所有测试共用的"准备数据"，每个测试函数自动获取干净的数据库和测试数据。
"""

import pytest
import os
import tempfile
from database import Database
from services import CourseService


@pytest.fixture
def temp_db():
    """
    创建一个临时数据库文件，测试结束后自动删除。
    这保证了每个测试之间互不影响（隔离性）。
    """
    # 在系统临时目录创建数据库文件
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    db = Database(db_path)
    yield db  # yield 之前的代码是"setup"，之后是"teardown"

    # 测试结束后清理
    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def svc(temp_db):
    """基于临时数据库创建 CourseService 实例"""
    return CourseService(temp_db)


@pytest.fixture
def sample_courses():
    """预定义的测试课程数据"""
    return [
        {"course_id": "CS101", "name": "程序设计基础", "teacher": "张教授",
         "credits": 4.0, "capacity": 3},
        {"course_id": "CS201", "name": "数据结构", "teacher": "李教授",
         "credits": 3.5, "capacity": 2},
        {"course_id": "MA101", "name": "高等数学", "teacher": "陈教授",
         "credits": 5.0, "capacity": 50},
    ]


@pytest.fixture
def sample_students():
    """预定义的测试学生数据"""
    return [
        {"student_id": "S001", "name": "张三", "major": "计算机科学与技术"},
        {"student_id": "S002", "name": "李四", "major": "软件工程"},
        {"student_id": "S003", "name": "王五", "major": "信息安全"},
    ]


@pytest.fixture
def populated_service(svc, sample_courses, sample_students):
    """
    预填充了课程和学生数据的服务实例。
    很多测试都需要这个"已填充好数据"的状态。
    """
    # 添加课程
    for c in sample_courses:
        svc.create_course(**c)
    # 添加学生
    for s in sample_students:
        svc.create_student(**s)
    return svc