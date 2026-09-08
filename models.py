
"""
数据模型层 —— 定义课程和学生的数据结构
这是整个系统的地基，所有业务逻辑都建立在这些数据类之上。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Course:
    """课程模型"""
    course_id: str           # 课程编号，如 "CS101"
    name: str                # 课程名称，如 "数据结构"
    teacher: str             # 授课教师
    credits: float           # 学分（0.5 ~ 10）
    capacity: int            # 最大选课人数
    enrolled_count: int = 0  # 当前已选人数

    def __post_init__(self):
        """数据校验 —— 创建对象时自动执行"""
        if not self.course_id or not self.course_id.strip():
            raise ValueError("课程编号不能为空")
        if not self.name or not self.name.strip():
            raise ValueError("课程名称不能为空")
        if not self.teacher or not self.teacher.strip():
            raise ValueError("授课教师不能为空")
        if self.credits <= 0 or self.credits > 10:
            raise ValueError(f"学分必须在 0.5~10 之间，当前值: {self.credits}")
        if self.capacity < 0:
            raise ValueError(f"课程容量不能为负数，当前值: {self.capacity}")
        if self.enrolled_count < 0:
            raise ValueError(f"已选人数不能为负数，当前值: {self.enrolled_count}")
        if self.enrolled_count > self.capacity:
            raise ValueError(
                f"已选人数({self.enrolled_count})不能超过课程容量({self.capacity})"
            )

    @property
    def is_full(self) -> bool:
        """课程是否已满"""
        return self.enrolled_count >= self.capacity

    @property
    def available_seats(self) -> int:
        """剩余名额"""
        return max(0, self.capacity - self.enrolled_count)

    def add_student(self):
        """选课成功时调用：已选人数 +1"""
        if self.is_full:
            raise ValueError(f"课程 {self.name}({self.course_id}) 已满，无法选课")
        self.enrolled_count += 1

    def remove_student(self):
        """退课成功时调用：已选人数 -1"""
        if self.enrolled_count <= 0:
            raise ValueError(f"课程 {self.name} 当前无人选课，无法退课")
        self.enrolled_count -= 1

    def to_dict(self) -> dict:
        """转为字典（方便存入数据库）"""
        return {
            "course_id": self.course_id,
            "name": self.name,
            "teacher": self.teacher,
            "credits": self.credits,
            "capacity": self.capacity,
            "enrolled_count": self.enrolled_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Course":
        """从字典创建课程对象"""
        return cls(
            course_id=data["course_id"],
            name=data["name"],
            teacher=data["teacher"],
            credits=float(data["credits"]),
            capacity=int(data["capacity"]),
            enrolled_count=int(data.get("enrolled_count", 0)),
        )


@dataclass
class Student:
    """学生模型"""
    student_id: str              # 学号，如 "2023001"
    name: str                    # 姓名
    major: str = ""              # 专业
    max_credits: float = 30.0    # 每学期最大学分限制
    enrolled_courses: list = field(default_factory=list)  # 已选课程ID列表
    grades: dict = field(default_factory=dict)            # {course_id: score}

    def __post_init__(self):
        """数据校验"""
        if not self.student_id or not self.student_id.strip():
            raise ValueError("学号不能为空")
        if not self.name or not self.name.strip():
            raise ValueError("学生姓名不能为空")
        if self.max_credits <= 0:
            raise ValueError(f"最大学分限制必须大于0，当前值: {self.max_credits}")

    def can_enroll(self, course: Course, current_total_credits: float) -> tuple:
        """
        检查学生是否可以选某门课
        返回: (是否可以选, 原因说明)
        """
        if course.course_id in self.enrolled_courses:
            return False, f"你已经选过 {course.name}，不能重复选课"
        if course.is_full:
            return False, f"课程 {course.name} 已满（{course.enrolled_count}/{course.capacity}）"
        if current_total_credits + course.credits > self.max_credits:
            return False, (
                f"学分超限：当前已选 {current_total_credits} 学分，"
                f"本课程 {course.credits} 学分，"
                f"上限 {self.max_credits} 学分"
            )
        return True, "可以选课"

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "name": self.name,
            "major": self.major,
            "max_credits": self.max_credits,
            "enrolled_courses": self.enrolled_courses,
            "grades": self.grades,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Student":
        return cls(
            student_id=data["student_id"],
            name=data["name"],
            major=data.get("major", ""),
            max_credits=float(data.get("max_credits", 30)),
            enrolled_courses=data.get("enrolled_courses", []),
            grades=data.get("grades", {}),
        )


@dataclass
class EnrollmentRecord:
    """选课记录模型"""
    student_id: str
    course_id: str
    enroll_time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    score: Optional[float] = None  # 成绩，None 表示尚未出成绩

    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "course_id": self.course_id,
            "enroll_time": self.enroll_time,
            "score": self.score,
        }