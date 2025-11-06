from database import models
from database.database import get_db, engine
from sqlalchemy import text

import random
import string

# ІНСТРУМЕНТИ
def executeSqlQuery(query: str):
    with engine.begin() as conn:
        return conn.execution_options(autocommit=True).execute(text(query)).all()
    
def evaluateSqlAlchemyQuery(query: str):
    db = get_db()
    return eval(query, locals={"db": db}, globals={"models": models})

def executeSqlAlchemyQuery(query: str):
    db = get_db()
    return exec(query, locals={"db": db}, globals={"models": models})

# СТВОРЕННЯ
def addStudent(username: str):
    student = models.Student(username=username)

    db = get_db()
    db.add(student)
    db.commit()
    db.refresh(student)

    return student


def addTeacher(username: str):
    teacher = models.Teacher(username=username)

    db = get_db()
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return teacher


def addCourseCategory(name: str):
    course_category = models.CourseCategory(name=name)

    db = get_db()
    db.add(course_category)
    db.commit()
    db.refresh(course_category)

    return course_category

def addCourse(name: str, course_category_id: int):
    course = models.Course(name=name, course_category_id=course_category_id)
    
    db = get_db()
    db.add(course)
    db.commit()
    db.refresh(course)

    return course


def addGroup(day: str, time: int, room: int, course_id: int, teacher_id: int):
    db = get_db()
    group = models.Group(day=day, time=time, room=room, course_id=course_id, teacher_id=teacher_id)
    
    db.add(group)
    db.commit()
    db.refresh(group)

    random.seed(group.id)
    db = get_db()
    group = db.query(models.Group).where(models.Group.id == group.id).first()
    group.code = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
    db.add(group)
    db.commit()
    db.refresh(group)

    return group


def addGroupStudent(student_name: str, student_login: str, group_id: int):
    db = get_db()

    group_student = models.GroupStudent(student_name=student_name, student_login=student_login, group_id=group_id)

    db.add(group_student)
    db.commit()
    db.refresh(group_student)

    return group_student


# ОТРИМАННЯ
def getStudent(username: str):
    db = get_db()

    return db.query(models.Student).where(models.Student.username == username).first()


def getStudentById(student_id: int):
    db = get_db()

    return db.query(models.Student).where(models.Student.id == student_id).first()


def getTeacher(username: str):
    db = get_db()

    return db.query(models.Teacher).where(models.Teacher.username == username).first()


def getCourseCategory(name: str):
    db = get_db()

    return db.query(models.CourseCategory).where(models.CourseCategory.name == name).first()


def getAllCourseCategories():
    db = get_db()

    return db.query(models.CourseCategory).all()


def getCourse(name: str):
    db = get_db()

    return db.query(models.Course).where(models.Course.name == name).first()


def getGroup(day: str, time: int, room: int, course_id: int):
    db = get_db()

    return db.query(models.Group).where(
        models.Group.course_id == course_id, 
        models.Group.day == day, 
        models.Group.time == time,
        models.Group.room == room
    ).first()

def getGroupById(group_id: int):
    db = get_db()

    return db.query(models.Group).where(models.Group.id == group_id).first()


def getCoursesByCategory(course_category_id: int):
    db = get_db()

    return db.query(models.Course).where(models.Course.course_category_id == course_category_id).all()


def getTeacherGroups(teacher_id: int):
    db = get_db()

    return db.query(models.Group).where(models.Group.teacher_id == teacher_id).all()


def getStudentGroupsById(student_id: int):
    db = get_db()

    return db.query(models.Group).join(models.GroupStudent).where(models.GroupStudent.student_id == student_id).all()


def getStudentBalances(student_id: int):
    db = get_db()

    student_groups = db.query(models.GroupStudent).where(models.GroupStudent.student_id == student_id).all()

    student_balances = [
        (group_student.group, group_student.balance)

        for group_student in student_groups
    ]

    return student_balances


def getGroupByCode(group_code: str):
    db = get_db()

    group = db.query(models.Group).where(models.Group.code == group_code).first()

    return group

def getGroupStudentByLogin(student_login: str, group_id):
    db = get_db()

    group_student = db.query(models.GroupStudent).where(models.GroupStudent.student_login == student_login, models.GroupStudent.group_id == group_id).first()

    return group_student

def getGroupStudent(student_id: int, group_id: int):
    db = get_db()

    return db.query(models.GroupStudent).where(models.GroupStudent.student_id == student_id, models.GroupStudent.group_id).first()


def getStudentQuizCompletetion(student_id: int, group_id: int):
    db = get_db()

    group_student_pair = db.query(models.GroupStudent).where(models.GroupStudent.student_id == student_id, models.GroupStudent.group_id == group_id).first()

    return group_student_pair.has_answered


def getGroupStudentById(group_student_id: int):
    db = get_db()

    group_student = db.query(models.GroupStudent).where(models.GroupStudent.id == group_student_id).first()

    return group_student


def getGroupStudents(group_id: int):
    db = get_db()

    group_students = db.query(models.GroupStudent).where(models.GroupStudent.group_id == group_id).all()

    return group_students

# ОНОВЛЕННЯ
def setTeacherAdminStatus(username: str, isAdmin: bool = False):
    db = get_db()
    teacher = db.query(models.Teacher).where(models.Teacher.username == username).first()

    teacher.isAdmin = isAdmin
    db.add(teacher)
    db.commit()


def setGroupStudentBalance(group_student_id: int, balance: float):
    db = get_db()

    group_student_pair = db.query(models.GroupStudent).where(
        models.GroupStudent.id == group_student_id
    ).first()

    if group_student_pair:

        group_student_pair.balance = balance

        db.add(group_student_pair)
        db.commit()

def setStudentQuizCompletion(student_id: int, group_id: int):
    db = get_db()

    group_student_pair = db.query(models.GroupStudent).where(models.GroupStudent.student_id == student_id, models.GroupStudent.group_id == group_id).first()
    group_student_pair.has_answered = True

    db.add(group_student_pair)
    db.commit()

def resetStudentsQuizCompletion():
    db = get_db()

    group_student_pairs = db.query(models.GroupStudent).all()
    for pair in group_student_pairs:
        pair.has_answered = False
        db.add(pair)

    db.commit()
    

def loginGroupStudent(student_login: str, student_id: int, group_id: int):
    db = get_db()

    group_student = db.query(models.GroupStudent).where(models.GroupStudent.group_id == group_id, models.GroupStudent.student_login == student_login).first()
    group_student.student_id = student_id

    db.add(group_student)
    db.commit()

def deloginGroupStudent(student_id: int, group_id: int):
    db = get_db()

    group_student = db.query(models.GroupStudent).where(
        models.GroupStudent.student_id == student_id,
        models.GroupStudent.group_id == group_id
    ).first()
    group_student.student_id = None

    db.add(group_student)
    db.commit()

# ВИДАЛЕННЯ
def deleteStudent(student_username: str):
    db = get_db()

    student = db.query(models.Student).where(models.Student.username == student_username).first()

    db.delete(student)
    db.commit()


def deleteTeacher(teacher_username: str):
    db = get_db()

    teacher = db.query(models.Teacher).where(models.Teacher.username == teacher_username).first()

    db.delete(teacher)
    db.commit()


def deleteCourse(course_name: str):
    db = get_db()

    course = db.query(models.Course).where(models.Course.name == course_name).first()

    db.delete(course)
    db.commit()


def deleteGroup(group_id: int):
    db = get_db()

    group = db.query(models.Group).where(models.Group.id == group_id).first()

    db.delete(group)
    db.commit()

def deleteGroupStudent(group_student_id: int):
    db = get_db()

    group_student_relationship = db.query(models.GroupStudent).where(models.GroupStudent.id == group_student_id).first()

    db.delete(group_student_relationship)
    db.commit()

def kickGroupStudent(group_student_id: int, group_id: int):
    db = get_db()

    group_student = db.query(models.GroupStudent).where(models.GroupStudent.group_student_id == group_student_id, models.GroupStudent.group_id == group_id).first()

    db.delete(group_student)
    db.commit()