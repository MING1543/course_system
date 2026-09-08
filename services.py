
"""
业务逻辑层 —— 选课系统的核心业务规则
所有"能不能选""能不能退""成绩怎么算"的逻辑都在这里。
这是测试的重点对象。
"""

from datetime import datetime
from typing import Optional, List, Tuple
from models import Course, Student
from database import Database


class CourseService:
    """选课系统业务逻辑"""

    def __init__(self, db: Database):
        self.db = db

    # ========== 课程管理 ==========

    def create_course(self, course_id: str, name: str, teacher: str,
                      credits: float, capacity: int) -> Course:
        """
        创建新课程
        返回: 创建好的课程对象
        异常: ValueError（参数不合法或课程已存在）
        """
        # 检查课程是否已存在
        existing = self.db.get_course(course_id)
        if existing:
            raise ValueError(f"课程编号 {course_id} 已存在：{existing.name}")

        course = Course(
            course_id=course_id,
            name=name,
            teacher=teacher,
            credits=credits,
            capacity=capacity,
        )

        if not self.db.add_course(course):
            raise ValueError(f"课程 {course_id} 创建失败（数据库错误）")

        return course

    def get_course(self, course_id: str) -> Course:
        """查询课程，不存在则抛异常"""
        course = self.db.get_course(course_id)
        if not course:
            raise ValueError(f"课程 {course_id} 不存在")
        return course

    def list_courses(self) -> List[Course]:
        """列出所有课程"""
        return self.db.get_all_courses()

    def search_courses(self, keyword: str) -> List[Course]:
        """搜索课程"""
        if not keyword or not keyword.strip():
            raise ValueError("搜索关键词不能为空")
        return self.db.search_courses(keyword.strip())

    def delete_course(self, course_id: str) -> bool:
        """删除课程（如果有学生选了这门课，不允许删除）"""
        course = self.db.get_course(course_id)
        if not course:
            raise ValueError(f"课程 {course_id} 不存在")
        if course.enrolled_count > 0:
            raise ValueError(
                f"课程 {course.name} 已有 {course.enrolled_count} 人选课，不能删除"
            )
        return self.db.delete_course(course_id)

    # ========== 学生管理 ==========

    def create_student(self, student_id: str, name: str,
                       major: str = "", max_credits: float = 30.0) -> Student:
        """创建新学生"""
        existing = self.db.get_student(student_id)
        if existing:
            raise ValueError(f"学号 {student_id} 已存在：{existing.name}")

        student = Student(
            student_id=student_id,
            name=name,
            major=major,
            max_credits=max_credits,
        )

        if not self.db.add_student(student):
            raise ValueError(f"学生 {student_id} 创建失败")

        return student

    def get_student(self, student_id: str) -> Student:
        """查询学生"""
        student = self.db.get_student(student_id)
        if not student:
            raise ValueError(f"学生 {student_id} 不存在")
        return student

    def list_students(self) -> List[Student]:
        return self.db.get_all_students()

    # ========== 选课/退课（核心业务） ==========

    def enroll(self, student_id: str, course_id: str) -> dict:
        """
        学生选课
        返回: {"success": True, "message": "..."} 或 {"success": False, "message": "..."}
        """
        # 1. 验证学生存在
        student = self.db.get_student(student_id)
        if not student:
            return {"success": False, "message": f"学生 {student_id} 不存在"}

        # 2. 验证课程存在
        course = self.db.get_course(course_id)
        if not course:
            return {"success": False, "message": f"课程 {course_id} 不存在"}

        # 3. 计算学生当前已选学分
        current_credits = self._get_student_total_credits(student)

        # 4. 检查是否可以选课（调用 Student 模型的方法）
        can_enroll, reason = student.can_enroll(course, current_credits)
        if not can_enroll:
            return {"success": False, "message": reason}

        # 5. 执行选课：更新课程已选人数
        course.add_student()
        self.db.update_course(course)

        # 6. 更新学生的已选课程列表
        student.enrolled_courses.append(course_id)
        self.db.update_student(student)

        # 7. 记录选课记录
        enroll_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.add_enrollment(student_id, course_id, enroll_time)

        return {
            "success": True,
            "message": f"{student.name} 选课成功：{course.name}（{course.credits}学分）",
        }

    def drop(self, student_id: str, course_id: str) -> dict:
        """
        学生退课
        """
        # 1. 验证学生存在
        student = self.db.get_student(student_id)
        if not student:
            return {"success": False, "message": f"学生 {student_id} 不存在"}

        # 2. 验证课程存在
        course = self.db.get_course(course_id)
        if not course:
            return {"success": False, "message": f"课程 {course_id} 不存在"}

        # 3. 检查学生是否选了这门课
        if course_id not in student.enrolled_courses:
            return {
                "success": False,
                "message": f"{student.name} 没有选修 {course.name}，无法退课",
            }

        # 4. 执行退课：更新课程已选人数
        course.remove_student()
        self.db.update_course(course)

        # 5. 更新学生的已选课程列表
        student.enrolled_courses.remove(course_id)
        # 如果已有成绩，也一并删除
        if course_id in student.grades:
            del student.grades[course_id]
        self.db.update_student(student)

        # 6. 删除选课记录
        self.db.remove_enrollment(student_id, course_id)

        return {
            "success": True,
            "message": f"{student.name} 退课成功：{course.name}",
        }

    # ========== 成绩管理 ==========

    def set_score(self, student_id: str, course_id: str, score: float) -> dict:
        """录入成绩"""
        # 验证分数范围
        if score < 0 or score > 100:
            return {"success": False, "message": f"成绩必须在 0~100 之间，当前值: {score}"}

        # 验证学生选了这门课
        student = self.db.get_student(student_id)
        if not student:
            return {"success": False, "message": f"学生 {student_id} 不存在"}
        if course_id not in student.enrolled_courses:
            return {"success": False, "message": f"学生未选修课程 {course_id}，不能录入成绩"}

        # 更新成绩
        student.grades[course_id] = score
        self.db.update_student(student)
        self.db.update_score(student_id, course_id, score)

        return {
            "success": True,
            "message": f"成绩录入成功：{student.name} - {course_id} = {score}分",
        }

    def get_student_report(self, student_id: str) -> dict:
        """获取学生成绩单"""
        student = self.db.get_student(student_id)
        if not student:
            raise ValueError(f"学生 {student_id} 不存在")

        enrollments = self.db.get_enrollments_by_student(student_id)
        total_credits = 0.0
        earned_credits = 0.0
        weighted_sum = 0.0

        courses_detail = []
        for e in enrollments:
            detail = {
                "course_id": e["course_id"],
                "course_name": e["course_name"],
                "teacher": e["teacher"],
                "credits": e["credits"],
                "score": e["score"],
                "grade_level": self._score_to_level(e["score"]),
            }
            courses_detail.append(detail)
            total_credits += e["credits"]
            if e["score"] is not None and e["score"] >= 60:
                earned_credits += e["credits"]
                weighted_sum += e["score"] * e["credits"]

        gpa = (weighted_sum / earned_credits / 10) if earned_credits > 0 else 0.0

        return {
            "student_id": student.student_id,
            "student_name": student.name,
            "major": student.major,
            "courses": courses_detail,
            "total_credits": total_credits,
            "earned_credits": earned_credits,
            "gpa": round(gpa, 2),
        }

    # ========== 统计信息 ==========

    def get_system_stats(self) -> dict:
        """获取系统概览"""
        stats = self.db.get_statistics()
        return {
            "课程总数": stats["course_count"],
            "学生总数": stats["student_count"],
            "选课记录总数": stats["enrollment_count"],
        }

    # ========== 内部方法 ==========

    def _get_student_total_credits(self, student: Student) -> float:
        """计算学生当前已选课程的总学分"""
        total = 0.0
        for cid in student.enrolled_courses:
            course = self.db.get_course(cid)
            if course:
                total += course.credits
        return total

    @staticmethod
    def _score_to_level(score: Optional[float]) -> str:
        """分数转等级"""
        if score is None:
            return "未评分"
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "中等"
        elif score >= 60:
            return "及格"
        else:
            return "不及格"