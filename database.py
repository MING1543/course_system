
"""
数据库层 —— 使用 SQLite 实现数据持久化
将数据存入本地数据库文件，程序关闭后数据不会丢失。
"""

import sqlite3
import json
import os
from typing import List, Optional
from models import Course, Student


class Database:
    """SQLite 数据库管理类"""

    def __init__(self, db_path: str = "course_system.db"):
        self.db_path = db_path
        self._init_tables()

    def _get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 让结果可以用列名访问
        return conn

    def _init_tables(self):
        """初始化数据库表结构"""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                course_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                teacher TEXT NOT NULL,
                credits REAL NOT NULL,
                capacity INTEGER NOT NULL,
                enrolled_count INTEGER DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                major TEXT DEFAULT '',
                max_credits REAL DEFAULT 30.0,
                enrolled_courses TEXT DEFAULT '[]',
                grades TEXT DEFAULT '{}'
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                enroll_time TEXT NOT NULL,
                score REAL,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id),
                UNIQUE(student_id, course_id)
            )
        """)

        conn.commit()
        conn.close()

    # ========== 课程操作 ==========

    def add_course(self, course: Course) -> bool:
        """添加课程到数据库"""
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO courses (course_id, name, teacher, credits, capacity, enrolled_count) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (course.course_id, course.name, course.teacher,
                 course.credits, course.capacity, course.enrolled_count)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # 课程编号已存在
        finally:
            conn.close()

    def get_course(self, course_id: str) -> Optional[Course]:
        """根据课程ID查询课程"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM courses WHERE course_id = ?", (course_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return Course(
            course_id=row["course_id"],
            name=row["name"],
            teacher=row["teacher"],
            credits=row["credits"],
            capacity=row["capacity"],
            enrolled_count=row["enrolled_count"],
        )

    def get_all_courses(self) -> List[Course]:
        """查询所有课程"""
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM courses ORDER BY course_id").fetchall()
        conn.close()
        return [
            Course(
                course_id=r["course_id"], name=r["name"], teacher=r["teacher"],
                credits=r["credits"], capacity=r["capacity"],
                enrolled_count=r["enrolled_count"],
            )
            for r in rows
        ]

    def update_course(self, course: Course) -> bool:
        """更新课程信息"""
        conn = self._get_conn()
        cursor = conn.execute(
            "UPDATE courses SET name=?, teacher=?, credits=?, capacity=?, enrolled_count=? "
            "WHERE course_id=?",
            (course.name, course.teacher, course.credits,
             course.capacity, course.enrolled_count, course.course_id)
        )
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    def delete_course(self, course_id: str) -> bool:
        """删除课程"""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM courses WHERE course_id = ?", (course_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def search_courses(self, keyword: str) -> List[Course]:
        """按关键词搜索课程（搜索课程名、教师名、课程编号）"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM courses WHERE course_id LIKE ? OR name LIKE ? OR teacher LIKE ?",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%")
        ).fetchall()
        conn.close()
        return [
            Course(
                course_id=r["course_id"], name=r["name"], teacher=r["teacher"],
                credits=r["credits"], capacity=r["capacity"],
                enrolled_count=r["enrolled_count"],
            )
            for r in rows
        ]

    # ========== 学生操作 ==========

    def add_student(self, student: Student) -> bool:
        """添加学生"""
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO students (student_id, name, major, max_credits, enrolled_courses, grades) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (student.student_id, student.name, student.major,
                 student.max_credits, json.dumps(student.enrolled_courses),
                 json.dumps(student.grades))
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def get_student(self, student_id: str) -> Optional[Student]:
        """查询学生"""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return Student(
            student_id=row["student_id"],
            name=row["name"],
            major=row["major"],
            max_credits=row["max_credits"],
            enrolled_courses=json.loads(row["enrolled_courses"]),
            grades=json.loads(row["grades"]),
        )

    def get_all_students(self) -> List[Student]:
        """查询所有学生"""
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM students ORDER BY student_id").fetchall()
        conn.close()
        return [
            Student(
                student_id=r["student_id"], name=r["name"], major=r["major"],
                max_credits=r["max_credits"],
                enrolled_courses=json.loads(r["enrolled_courses"]),
                grades=json.loads(r["grades"]),
            )
            for r in rows
        ]

    def update_student(self, student: Student) -> bool:
        """更新学生信息"""
        conn = self._get_conn()
        cursor = conn.execute(
            "UPDATE students SET name=?, major=?, max_credits=?, "
            "enrolled_courses=?, grades=? WHERE student_id=?",
            (student.name, student.major, student.max_credits,
             json.dumps(student.enrolled_courses),
             json.dumps(student.grades), student.student_id)
        )
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    # ========== 选课记录操作 ==========

    def add_enrollment(self, student_id: str, course_id: str, enroll_time: str) -> bool:
        """记录选课"""
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT INTO enrollments (student_id, course_id, enroll_time) VALUES (?, ?, ?)",
                (student_id, course_id, enroll_time)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def remove_enrollment(self, student_id: str, course_id: str) -> bool:
        """删除选课记录"""
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM enrollments WHERE student_id = ? AND course_id = ?",
            (student_id, course_id)
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    def get_enrollments_by_student(self, student_id: str) -> List[dict]:
        """查询某学生的所有选课记录"""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT e.course_id, c.name as course_name, c.teacher, c.credits,
                      e.enroll_time, e.score
               FROM enrollments e
               JOIN courses c ON e.course_id = c.course_id
               WHERE e.student_id = ?
               ORDER BY e.enroll_time""",
            (student_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_score(self, student_id: str, course_id: str, score: float) -> bool:
        """录入/更新成绩"""
        conn = self._get_conn()
        cursor = conn.execute(
            "UPDATE enrollments SET score = ? WHERE student_id = ? AND course_id = ?",
            (score, student_id, course_id)
        )
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    def get_statistics(self) -> dict:
        """获取系统统计数据"""
        conn = self._get_conn()
        course_count = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        student_count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        enrollment_count = conn.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0]
        conn.close()
        return {
            "course_count": course_count,
            "student_count": student_count,
            "enrollment_count": enrollment_count,
        }

    def close(self):
        """关闭数据库（如有连接池时调用）"""
        pass