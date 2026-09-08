
"""
命令行入口 —— 提供交互式菜单，让用户操作选课系统
运行方式: python main.py
"""

import os
import sys
from database import Database
from services import CourseService


def print_banner():
    print()
    print("=" * 50)
    print("        学生选课管理系统 v1.0")
    print("=" * 50)


def print_menu():
    print()
    print("--- 主菜单 ---")
    print("  1. 课程管理")
    print("  2. 学生管理")
    print("  3. 选课操作")
    print("  4. 成绩管理")
    print("  5. 查询统计")
    print("  0. 退出系统")
    print("-" * 30)


def input_float(prompt: str, min_val=None, max_val=None) -> float:
    """安全地读取浮点数输入"""
    while True:
        try:
            val = float(input(prompt))
            if min_val is not None and val < min_val:
                print(f"  输入值不能小于 {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"  输入值不能大于 {max_val}")
                continue
            return val
        except ValueError:
            print("  请输入有效数字")


def input_int(prompt: str, min_val=None) -> int:
    while True:
        try:
            val = int(input(prompt))
            if min_val is not None and val < min_val:
                print(f"  输入值不能小于 {min_val}")
                continue
            return val
        except ValueError:
            print("  请输入有效整数")


def course_management(svc: CourseService):
    """课程管理子菜单"""
    while True:
        print()
        print("== 课程管理 ==")
        print("  1. 添加课程")
        print("  2. 查看所有课程")
        print("  3. 搜索课程")
        print("  4. 删除课程")
        print("  0. 返回主菜单")

        choice = input("请选择: ").strip()

        if choice == "1":
            cid = input("课程编号: ").strip()
            name = input("课程名称: ").strip()
            teacher = input("授课教师: ").strip()
            credits = input_float("学分(0.5~10): ", 0.5, 10)
            capacity = input_int("最大人数: ", 0)
            try:
                course = svc.create_course(cid, name, teacher, credits, capacity)
                print(f"  [成功] 课程 {course.name}({course.course_id}) 已创建")
            except ValueError as e:
                print(f"  [失败] {e}")

        elif choice == "2":
            courses = svc.list_courses()
            if not courses:
                print("  当前没有课程")
            else:
                print(f"  {'编号':<10} {'名称':<16} {'教师':<10} {'学分':>4} {'已选/容量':>10}")
                print("  " + "-" * 54)
                for c in courses:
                    full_mark = " [满]" if c.is_full else ""
                    print(f"  {c.course_id:<10} {c.name:<16} {c.teacher:<10} "
                          f"{c.credits:>4.1f} {c.enrolled_count}/{c.capacity:>4}{full_mark}")

        elif choice == "3":
            keyword = input("搜索关键词: ").strip()
            try:
                results = svc.search_courses(keyword)
                if not results:
                    print(f"  未找到匹配 ''{keyword}'' 的课程")
                else:
                    for c in results:
                        print(f"  {c.course_id} - {c.name} ({c.teacher}) "
                              f"{c.credits}学分 {c.enrolled_count}/{c.capacity}人")
            except ValueError as e:
                print(f"  [失败] {e}")

        elif choice == "4":
            cid = input("要删除的课程编号: ").strip()
            try:
                svc.delete_course(cid)
                print(f"  [成功] 课程 {cid} 已删除")
            except ValueError as e:
                print(f"  [失败] {e}")

        elif choice == "0":
            break


def student_management(svc: CourseService):
    """学生管理子菜单"""
    while True:
        print()
        print("== 学生管理 ==")
        print("  1. 添加学生")
        print("  2. 查看所有学生")
        print("  3. 查看学生详情")
        print("  0. 返回主菜单")

        choice = input("请选择: ").strip()

        if choice == "1":
            sid = input("学号: ").strip()
            name = input("姓名: ").strip()
            major = input("专业(可回车跳过): ").strip()
            try:
                student = svc.create_student(sid, name, major)
                print(f"  [成功] 学生 {student.name}({student.student_id}) 已注册")
            except ValueError as e:
                print(f"  [失败] {e}")

        elif choice == "2":
            students = svc.list_students()
            if not students:
                print("  当前没有学生")
            else:
                print(f"  {'学号':<12} {'姓名':<10} {'专业':<16} {'已选课程数':>8}")
                print("  " + "-" * 50)
                for s in students:
                    print(f"  {s.student_id:<12} {s.name:<10} {s.major:<16} "
                          f"{len(s.enrolled_courses):>6}门")

        elif choice == "3":
            sid = input("学号: ").strip()
            try:
                student = svc.get_student(sid)
                print(f"  学号: {student.student_id}")
                print(f"  姓名: {student.name}")
                print(f"  专业: {student.major}")
                print(f"  学分上限: {student.max_credits}")
                print(f"  已选课程: {student.enrolled_courses}")
                if student.grades:
                    print(f"  成绩: {student.grades}")
            except ValueError as e:
                print(f"  [失败] {e}")

        elif choice == "0":
            break


def enrollment_operations(svc: CourseService):
    """选课/退课子菜单"""
    while True:
        print()
        print("== 选课操作 ==")
        print("  1. 选课")
        print("  2. 退课")
        print("  3. 查看我的课表")
        print("  0. 返回主菜单")

        choice = input("请选择: ").strip()

        if choice == "1":
            sid = input("学号: ").strip()
            cid = input("课程编号: ").strip()
            result = svc.enroll(sid, cid)
            status = "[成功]" if result["success"] else "[失败]"
            print(f"  {status} {result['message']}")

        elif choice == "2":
            sid = input("学号: ").strip()
            cid = input("课程编号: ").strip()
            result = svc.drop(sid, cid)
            status = "[成功]" if result["success"] else "[失败]"
            print(f"  {status} {result['message']}")

        elif choice == "3":
            sid = input("学号: ").strip()
            try:
                student = svc.get_student(sid)
                print(f"  {student.name} 的课表:")
                if not student.enrolled_courses:
                    print("    （暂无选课）")
                else:
                    for cid in student.enrolled_courses:
                        course = svc.get_course(cid)
                        score = student.grades.get(cid, "未评分")
                        print(f"    {course.course_id} - {course.name} "
                              f"({course.teacher}) {course.credits}学分 成绩:{score}")
            except ValueError as e:
                print(f"  [失败] {e}")

        elif choice == "0":
            break


def grade_management(svc: CourseService):
    """成绩管理子菜单"""
    while True:
        print()
        print("== 成绩管理 ==")
        print("  1. 录入成绩")
        print("  2. 查看成绩单")
        print("  0. 返回主菜单")

        choice = input("请选择: ").strip()

        if choice == "1":
            sid = input("学号: ").strip()
            cid = input("课程编号: ").strip()
            score = input_float("成绩(0~100): ", 0, 100)
            result = svc.set_score(sid, cid, score)
            status = "[成功]" if result["success"] else "[失败]"
            print(f"  {status} {result['message']}")

        elif choice == "2":
            sid = input("学号: ").strip()
            try:
                report = svc.get_student_report(sid)
                print(f"  === {report['student_name']} 的成绩单 ===")
                print(f"  专业: {report['major']}")
                print()
                if not report["courses"]:
                    print("    （暂无选课记录）")
                else:
                    print(f"  {'课程':<14} {'教师':<10} {'学分':>4} {'成绩':>6} {'等级':>6}")
                    print("  " + "-" * 46)
                    for c in report["courses"]:
                        score_str = f"{c['score']:.0f}" if c['score'] is not None else "未评"
                        print(f"  {c['course_name']:<14} {c['teacher']:<10} "
                              f"{c['credits']:>4.1f} {score_str:>6} {c['grade_level']:>6}")
                    print()
                    print(f"  总学分: {report['total_credits']:.1f}")
                    print(f"  已获学分: {report['earned_credits']:.1f}")
                    print(f"  GPA: {report['gpa']:.2f}")
            except ValueError as e:
                print(f"  [失败] {e}")

        elif choice == "0":
            break


def query_stats(svc: CourseService):
    """系统统计"""
    stats = svc.get_system_stats()
    print()
    print("== 系统统计 ==")
    for k, v in stats.items():
        print(f"  {k}: {v}")


def load_demo_data(svc: CourseService):
    """加载演示数据"""
    demo_courses = [
        ("CS101", "程序设计基础", "张教授", 4.0, 60),
        ("CS201", "数据结构", "李教授", 3.5, 50),
        ("CS301", "操作系统", "王教授", 3.0, 40),
        ("CS401", "计算机网络", "赵教授", 3.0, 45),
        ("MA101", "高等数学", "陈教授", 5.0, 80),
        ("MA201", "线性代数", "刘教授", 3.0, 70),
        ("EN101", "大学英语", "外教Smith", 2.0, 100),
    ]
    for cid, name, teacher, credits, cap in demo_courses:
        try:
            svc.create_course(cid, name, teacher, credits, cap)
        except ValueError:
            pass  # 已存在则跳过

    demo_students = [
        ("2023001", "张三", "计算机科学与技术"),
        ("2023002", "李四", "计算机科学与技术"),
        ("2023003", "王五", "软件工程"),
    ]
    for sid, name, major in demo_students:
        try:
            svc.create_student(sid, name, major)
        except ValueError:
            pass


def main():
    print_banner()

    # 初始化数据库（使用当前目录下的文件）
    db = Database("course_system.db")
    svc = CourseService(db)

    # 如果是第一次运行，询问是否加载演示数据
    stats = svc.get_system_stats()
    if stats["课程总数"] == 0 and stats["学生总数"] == 0:
        print("  检测到空数据库，是否加载演示数据？(y/n): ", end="")
        if input().strip().lower() == "y":
            load_demo_data(svc)
            print("  [成功] 已加载 7 门课程和 3 名学生的演示数据")

    while True:
        print_menu()
        choice = input("请选择: ").strip()

        if choice == "1":
            course_management(svc)
        elif choice == "2":
            student_management(svc)
        elif choice == "3":
            enrollment_operations(svc)
        elif choice == "4":
            grade_management(svc)
        elif choice == "5":
            query_stats(svc)
        elif choice == "0":
            print("  再见！")
            break
        else:
            print("  无效选项，请重新选择")


if __name__ == "__main__":
    main()