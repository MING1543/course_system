
"""
选课系统自动化测试 —— 完整测试套件
包含：正向测试、异常测试、边界测试、参数化测试
共 40+ 个测试用例，覆盖核心业务逻辑。

运行方式: pytest -v
"""

import pytest
from models import Course, Student
from services import CourseService


# ================================================================
# 第一部分：数据模型层测试（测试 Course 和 Student 类本身）
# ================================================================

class TestCourseModel:
    """课程模型的单元测试"""

    def test_create_valid_course(self):
        """正向：创建合法的课程对象"""
        course = Course("CS101", "数据结构", "张教授", 3.5, 50)
        assert course.course_id == "CS101"
        assert course.name == "数据结构"
        assert course.credits == 3.5
        assert course.capacity == 50
        assert course.enrolled_count == 0
        assert course.available_seats == 50
        assert not course.is_full

    def test_course_id_empty(self):
        """异常：课程编号为空"""
        with pytest.raises(ValueError, match="课程编号不能为空"):
            Course("", "数据结构", "张教授", 3.0, 50)

    def test_course_name_empty(self):
        """异常：课程名称为空"""
        with pytest.raises(ValueError, match="课程名称不能为空"):
            Course("CS101", "", "张教授", 3.0, 50)

    def test_course_credits_zero(self):
        """边界：学分为 0"""
        with pytest.raises(ValueError, match="学分必须在"):
            Course("CS101", "数据结构", "张教授", 0, 50)

    def test_course_credits_negative(self):
        """边界：学分为负数"""
        with pytest.raises(ValueError, match="学分必须在"):
            Course("CS101", "数据结构", "张教授", -1, 50)

    def test_course_credits_too_high(self):
        """边界：学分超过上限 10"""
        with pytest.raises(ValueError, match="学分必须在"):
            Course("CS101", "数据结构", "张教授", 11, 50)

    def test_course_capacity_negative(self):
        """边界：容量为负数"""
        with pytest.raises(ValueError, match="课程容量不能为负数"):
            Course("CS101", "数据结构", "张教授", 3.0, -1)

    def test_course_capacity_zero(self):
        """边界：容量为 0（允许创建，但立即满员）"""
        course = Course("CS101", "数据结构", "张教授", 3.0, 0)
        assert course.is_full
        assert course.available_seats == 0

    def test_course_is_full(self):
        """正向：课程满员判断"""
        course = Course("CS101", "数据结构", "张教授", 3.0, 2, enrolled_count=2)
        assert course.is_full
        assert course.available_seats == 0

    def test_course_add_student(self):
        """正向：选课人数 +1"""
        course = Course("CS101", "数据结构", "张教授", 3.0, 30)
        course.add_student()
        assert course.enrolled_count == 1
        assert course.available_seats == 29

    def test_course_add_student_full(self):
        """异常：课程已满再加人"""
        course = Course("CS101", "数据结构", "张教授", 3.0, 1, enrolled_count=1)
        with pytest.raises(ValueError, match="已满"):
            course.add_student()

    def test_course_remove_student(self):
        """正向：退课人数 -1"""
        course = Course("CS101", "数据结构", "张教授", 3.0, 30, enrolled_count=5)
        course.remove_student()
        assert course.enrolled_count == 4

    def test_course_remove_student_zero(self):
        """异常：无人选课时退课"""
        course = Course("CS101", "数据结构", "张教授", 3.0, 30, enrolled_count=0)
        with pytest.raises(ValueError, match="当前无人选课"):
            course.remove_student()


class TestStudentModel:
    """学生模型的单元测试"""

    def test_create_valid_student(self):
        """正向：创建合法的学生对象"""
        student = Student("2023001", "张三", "计算机科学")
        assert student.student_id == "2023001"
        assert student.name == "张三"
        assert student.max_credits == 30.0
        assert student.enrolled_courses == []
        assert student.grades == {}

    def test_student_id_empty(self):
        """异常：学号为空"""
        with pytest.raises(ValueError, match="学号不能为空"):
            Student("", "张三")

    def test_student_name_empty(self):
        """异常：姓名为空"""
        with pytest.raises(ValueError, match="学生姓名不能为空"):
            Student("2023001", "")

    def test_student_max_credits_invalid(self):
        """边界：学分上限为 0"""
        with pytest.raises(ValueError, match="最大学分限制必须大于0"):
            Student("2023001", "张三", max_credits=0)

    def test_can_enroll_normal(self):
        """正向：正常选课检查"""
        student = Student("S001", "张三", max_credits=30)
        course = Course("CS101", "数据结构", "张教授", 3.0, 50)
        can, reason = student.can_enroll(course, current_total_credits=10.0)
        assert can is True

    def test_can_enroll_already_enrolled(self):
        """异常：重复选同一门课"""
        student = Student("S001", "张三", enrolled_courses=["CS101"])
        course = Course("CS101", "数据结构", "张教授", 3.0, 50)
        can, reason = student.can_enroll(course, current_total_credits=4.0)
        assert can is False
        assert "已经选过" in reason

    def test_can_enroll_course_full(self):
        """异常：课程已满"""
        student = Student("S001", "张三")
        course = Course("CS101", "数据结构", "张教授", 3.0, 1, enrolled_count=1)
        can, reason = student.can_enroll(course, current_total_credits=0)
        assert can is False
        assert "已满" in reason

    def test_can_enroll_credits_exceed(self):
        """边界：选课导致学分超限"""
        student = Student("S001", "张三", max_credits=10)
        course = Course("CS101", "数据结构", "张教授", 4.0, 50)
        can, reason = student.can_enroll(course, current_total_credits=8.0)
        assert can is False
        assert "学分超限" in reason

    def test_can_enroll_credits_exact_limit(self):
        """边界：选课刚好达到学分上限（应该允许）"""
        student = Student("S001", "张三", max_credits=10)
        course = Course("CS101", "数据结构", "张教授", 3.0, 50)
        can, reason = student.can_enroll(course, current_total_credits=7.0)
        assert can is True  # 7 + 3 = 10，刚好等于上限


# ================================================================
# 第二部分：业务逻辑层测试（测试 CourseService）
# ================================================================

class TestCourseServiceCourseManagement:
    """课程管理的业务测试"""

    def test_create_course_success(self, svc):
        """正向：成功创建课程"""
        course = svc.create_course("CS101", "数据结构", "张教授", 3.5, 50)
        assert course.course_id == "CS101"
        assert course.name == "数据结构"

    def test_create_duplicate_course(self, svc):
        """异常：创建重复编号的课程"""
        svc.create_course("CS101", "数据结构", "张教授", 3.5, 50)
        with pytest.raises(ValueError, match="已存在"):
            svc.create_course("CS101", "数据结构2", "李教授", 3.0, 40)

    def test_get_course_success(self, populated_service):
        """正向：查询已存在的课程"""
        svc = populated_service
        course = svc.get_course("CS101")
        assert course.name == "程序设计基础"

    def test_get_course_not_found(self, svc):
        """异常：查询不存在的课程"""
        with pytest.raises(ValueError, match="不存在"):
            svc.get_course("NOTEXIST")

    def test_list_courses(self, populated_service):
        """正向：列出所有课程"""
        svc = populated_service
        courses = svc.list_courses()
        assert len(courses) == 3

    def test_search_courses_found(self, populated_service):
        """正向：搜索能匹配到结果"""
        svc = populated_service
        results = svc.search_courses("张")
        assert len(results) >= 1
        assert any(c.teacher == "张教授" for c in results)

    def test_search_courses_not_found(self, populated_service):
        """正向：搜索无结果（不报错，返回空列表）"""
        svc = populated_service
        results = svc.search_courses("不存在的关键字xyz")
        assert results == []

    def test_search_courses_empty_keyword(self, populated_service):
        """异常：搜索关键词为空"""
        svc = populated_service
        with pytest.raises(ValueError, match="搜索关键词不能为空"):
            svc.search_courses("")

    def test_delete_course_success(self, populated_service):
        """正向：删除无人选的课程"""
        svc = populated_service
        result = svc.delete_course("MA101")
        assert result is True
        # 确认已删除
        courses = svc.list_courses()
        assert len(courses) == 2

    def test_delete_course_with_enrollments(self, populated_service):
        """异常：删除有人选的课程"""
        svc = populated_service
        # 先让一个学生选课
        svc.enroll("S001", "CS101")
        # 尝试删除该课程
        with pytest.raises(ValueError, match="已有.*人选课"):
            svc.delete_course("CS101")

    def test_delete_course_not_exist(self, svc):
        """异常：删除不存在的课程"""
        with pytest.raises(ValueError, match="不存在"):
            svc.delete_course("NOTEXIST")


class TestCourseServiceStudentManagement:
    """学生管理的业务测试"""

    def test_create_student_success(self, svc):
        """正向：成功创建学生"""
        student = svc.create_student("S001", "张三", "计算机")
        assert student.student_id == "S001"
        assert student.name == "张三"

    def test_create_duplicate_student(self, svc):
        """异常：创建重复学号的学生"""
        svc.create_student("S001", "张三", "计算机")
        with pytest.raises(ValueError, match="已存在"):
            svc.create_student("S001", "张三2", "软件")

    def test_get_student_success(self, populated_service):
        """正向：查询已存在的学生"""
        svc = populated_service
        student = svc.get_student("S001")
        assert student.name == "张三"

    def test_get_student_not_found(self, svc):
        """异常：查询不存在的学生"""
        with pytest.raises(ValueError, match="不存在"):
            svc.get_student("NOTEXIST")


class TestEnrollment:
    """选课/退课的核心业务测试 —— 面试最常问的部分"""

    def test_enroll_success(self, populated_service):
        """正向：成功选课"""
        svc = populated_service
        result = svc.enroll("S001", "CS101")
        assert result["success"] is True
        assert "选课成功" in result["message"]

        # 验证课程已选人数 +1
        course = svc.get_course("CS101")
        assert course.enrolled_count == 1

        # 验证学生的已选课程列表更新
        student = svc.get_student("S001")
        assert "CS101" in student.enrolled_courses

    def test_enroll_student_not_exist(self, populated_service):
        """异常：不存在的学生选课"""
        svc = populated_service
        result = svc.enroll("NOTEXIST", "CS101")
        assert result["success"] is False
        assert "不存在" in result["message"]

    def test_enroll_course_not_exist(self, populated_service):
        """异常：选不存在的课程"""
        svc = populated_service
        result = svc.enroll("S001", "NOTEXIST")
        assert result["success"] is False
        assert "不存在" in result["message"]

    def test_enroll_duplicate(self, populated_service):
        """异常：重复选同一门课"""
        svc = populated_service
        svc.enroll("S001", "CS101")
        result = svc.enroll("S001", "CS101")
        assert result["success"] is False
        assert "已经选过" in result["message"]

    def test_enroll_course_full(self, populated_service):
        """边界：课程满员后选课"""
        svc = populated_service
        # CS201 容量为 2，让两个人选满
        svc.enroll("S001", "CS201")
        svc.enroll("S002", "CS201")
        # 第三个人选课应该失败
        result = svc.enroll("S003", "CS201")
        assert result["success"] is False
        assert "已满" in result["message"]

    def test_enroll_credits_exceed(self, populated_service):
        """边界：选课导致学分超限"""
        svc = populated_service
        # 将 S001 的学分上限设为 5
        student = svc.get_student("S001")
        student.max_credits = 5.0
        svc.db.update_student(student)
        # MA101 是 5 学分，选完后达到上限
        svc.enroll("S001", "MA101")
        # 再选 CS101（4学分）应该失败
        result = svc.enroll("S001", "CS101")
        assert result["success"] is False
        assert "学分超限" in result["message"]

    def test_drop_success(self, populated_service):
        """正向：成功退课"""
        svc = populated_service
        svc.enroll("S001", "CS101")
        result = svc.drop("S001", "CS101")
        assert result["success"] is True
        assert "退课成功" in result["message"]

        # 验证课程人数恢复
        course = svc.get_course("CS101")
        assert course.enrolled_count == 0

        # 验证学生已选列表更新
        student = svc.get_student("S001")
        assert "CS101" not in student.enrolled_courses

    def test_drop_not_enrolled(self, populated_service):
        """异常：退没选的课"""
        svc = populated_service
        result = svc.drop("S001", "CS101")
        assert result["success"] is False
        assert "没有选修" in result["message"]

    def test_drop_student_not_exist(self, populated_service):
        """异常：不存在的学生退课"""
        svc = populated_service
        result = svc.drop("NOTEXIST", "CS101")
        assert result["success"] is False

    def test_drop_course_not_exist(self, populated_service):
        """异常：退不存在的课程"""
        svc = populated_service
        result = svc.drop("S001", "NOTEXIST")
        assert result["success"] is False

    def test_enroll_then_drop_then_reenroll(self, populated_service):
        """正向：选课 → 退课 → 重新选课（验证数据一致性）"""
        svc = populated_service
        # 选课
        r1 = svc.enroll("S001", "CS101")
        assert r1["success"] is True
        # 退课
        r2 = svc.drop("S001", "CS101")
        assert r2["success"] is True
        # 重新选课
        r3 = svc.enroll("S001", "CS101")
        assert r3["success"] is True
        # 验证最终状态
        course = svc.get_course("CS101")
        assert course.enrolled_count == 1


class TestGradeManagement:
    """成绩管理的业务测试"""

    def test_set_score_success(self, populated_service):
        """正向：成功录入成绩"""
        svc = populated_service
        svc.enroll("S001", "CS101")
        result = svc.set_score("S001", "CS101", 85.5)
        assert result["success"] is True

        # 验证成绩已记录
        student = svc.get_student("S001")
        assert student.grades["CS101"] == 85.5

    def test_set_score_invalid_high(self, populated_service):
        """边界：成绩超过 100"""
        svc = populated_service
        svc.enroll("S001", "CS101")
        result = svc.set_score("S001", "CS101", 101)
        assert result["success"] is False
        assert "0~100" in result["message"]

    def test_set_score_invalid_negative(self, populated_service):
        """边界：成绩为负数"""
        svc = populated_service
        svc.enroll("S001", "CS101")
        result = svc.set_score("S001", "CS101", -5)
        assert result["success"] is False

    def test_set_score_boundary_0(self, populated_service):
        """边界：成绩为 0（应该允许）"""
        svc = populated_service
        svc.enroll("S001", "CS101")
        result = svc.set_score("S001", "CS101", 0)
        assert result["success"] is True

    def test_set_score_boundary_100(self, populated_service):
        """边界：成绩为 100（应该允许）"""
        svc = populated_service
        svc.enroll("S001", "CS101")
        result = svc.set_score("S001", "CS101", 100)
        assert result["success"] is True

    def test_set_score_not_enrolled(self, populated_service):
        """异常：给未选课的学生录入成绩"""
        svc = populated_service
        result = svc.set_score("S001", "CS101", 80)
        assert result["success"] is False
        assert "未选修" in result["message"]

    def test_student_report(self, populated_service):
        """正向：生成成绩单"""
        svc = populated_service
        svc.enroll("S001", "CS101")
        svc.enroll("S001", "MA101")
        svc.set_score("S001", "CS101", 90)
        svc.set_score("S001", "MA101", 80)

        report = svc.get_student_report("S001")
        assert report["student_name"] == "张三"
        assert report["total_credits"] == 9.0  # 4.0 + 5.0
        assert report["earned_credits"] == 9.0  # 两门都及格
        assert len(report["courses"]) == 2


# ================================================================
# 第三部分：参数化测试（一组数据跑同一套逻辑）
# ================================================================

class TestParameterized:
    """参数化测试 —— 面试加分项"""

    @pytest.mark.parametrize("score,expected_level", [
        (95, "优秀"),
        (90, "优秀"),
        (85, "良好"),
        (80, "良好"),
        (75, "中等"),
        (70, "中等"),
        (65, "及格"),
        (60, "及格"),
        (59, "不及格"),
        (0, "不及格"),
        (None, "未评分"),
    ])
    def test_score_to_level(self, score, expected_level):
        """参数化：分数转等级的所有边界"""
        result = CourseService._score_to_level(score)
        assert result == expected_level

    @pytest.mark.parametrize("keyword,expected_min_count", [
        ("CS", 2),       # CS101 和 CS201 都包含 "CS"
        ("张", 1),       # 张教授
        ("数学", 1),     # 高等数学
        ("不存在的xyz", 0),
    ])
    def test_search_various_keywords(self, populated_service, keyword, expected_min_count):
        """参数化：不同搜索关键词的结果"""
        svc = populated_service
        results = svc.search_courses(keyword)
        assert len(results) >= expected_min_count

    @pytest.mark.parametrize("credits,should_pass", [
        (0.5, True),
        (1.0, True),
        (5.0, True),
        (10.0, True),
        (0, False),
        (-1, False),
        (10.1, False),
        (100, False),
    ])
    def test_course_credits_boundary(self, svc, credits, should_pass):
        """参数化：学分的各种边界值"""
        if should_pass:
            course = svc.create_course("TEST01", "测试课", "老师", credits, 30)
            assert course.credits == credits
        else:
            with pytest.raises(ValueError):
                svc.create_course("TEST01", "测试课", "老师", credits, 30)


# ================================================================
# 第四部分：集成测试（多步骤业务流程）
# ================================================================

class TestIntegration:
    """端到端的业务流程测试"""

    def test_full_enrollment_workflow(self, populated_service):
        """完整流程：创建 → 选课 → 录成绩 → 查看成绩单 → 退课"""
        svc = populated_service

        # Step 1: 选课
        r = svc.enroll("S001", "CS101")
        assert r["success"] is True

        # Step 2: 录入成绩
        r = svc.set_score("S001", "CS101", 88)
        assert r["success"] is True

        # Step 3: 查看成绩单
        report = svc.get_student_report("S001")
        assert len(report["courses"]) == 1
        assert report["courses"][0]["score"] == 88
        assert report["gpa"] > 0

        # Step 4: 退课（退课后成绩也应清除）
        r = svc.drop("S001", "CS101")
        assert r["success"] is True

        # Step 5: 验证退课后状态
        student = svc.get_student("S001")
        assert "CS101" not in student.enrolled_courses
        assert "CS101" not in student.grades

        course = svc.get_course("CS101")
        assert course.enrolled_count == 0

    def test_multiple_students_same_course(self, populated_service):
        """多个学生选同一门课"""
        svc = populated_service
        # CS101 容量为 3
        r1 = svc.enroll("S001", "CS101")
        r2 = svc.enroll("S002", "CS101")
        r3 = svc.enroll("S003", "CS101")
        assert all(r["success"] for r in [r1, r2, r3])

        course = svc.get_course("CS101")
        assert course.enrolled_count == 3
        assert course.is_full

    def test_system_stats_after_operations(self, populated_service):
        """操作后系统统计数据正确"""
        svc = populated_service
        svc.enroll("S001", "CS101")
        svc.enroll("S002", "CS101")

        stats = svc.get_system_stats()
        assert stats["课程总数"] == 3
        assert stats["学生总数"] == 3
        assert stats["选课记录总数"] == 2