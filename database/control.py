from database import models
from database.database import get_db

# СТВОРЕННЯ
def addStudent(username: str, name: str):
    student = models.Student(username=username, name=name)

    db = get_db()
    db.add(student)
    db.commit()
    db.refresh(student)

    return student


def addTeacher(username: str, name: str):
    teacher = models.Teacher(username=username, name=name)

    db = get_db()
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return teacher


def addCourse(name: str):
    course = models.Course(name=name)
    
    db = get_db()
    db.add(course)
    db.commit()
    db.refresh(course)

    return course


def addGroup(day: str, time: int, room: int, course_id: int, teacher_id: int):
    group = models.Group(day=day, time=time, room=room, course_id=course_id, teacher_id=teacher_id)

    db = get_db()
    db.add(group)
    db.commit()
    db.refresh(group)

    return group


# ОТРИМАННЯ
def getStudent(username: str):
    db = get_db()

    return db.query(models.Student).filter(models.Student.username == username).first()


def getCourse(name: str):
    db = get_db()

    return db.query(models.Course).filter(models.Course.name == name).first()


def getGroup(day: str, time: int, room: int, course_id: int):
    db = get_db()

    return db.query(models.Group).filter(
        models.Group.course_id == course_id, 
        models.Group.day == day, 
        models.Group.time == time,
        models.Group.room == room
    ).first()


def getTeacher(username: str):
    db = get_db()

    return db.query(models.Teacher).filter(models.Teacher.username == username).first()


def getTeacherGroups(teacher_id: int):
    db = get_db()

    return db.query(models.Group).filter(models.Group.teacher_id == teacher_id).all()


def getStudentGroups(student_username: str):
    db = get_db()

    return db.query(models.Group).select_from(models.Student).join(models.Student.groups).filter(models.Student.username == student_username).all()


# ОНОВЛЕННЯ
def setTeacherAdminStatus(username: str, isAdmin: bool = False):
    db = get_db()
    teacher = db.query(models.Teacher).filter(models.Teacher.username == username).first()

    teacher.isAdmin = isAdmin
    db.add(teacher)
    db.commit()


def joinStudentToGroup(student_id: int, group_id: int):
    db = get_db()

    group_student_relationship = models.GroupStudent(student_id=student_id, group_id=group_id)

    db.add(group_student_relationship)
    db.commit()


# ВИДАЛЕННЯ
def deleteStudent(student_username: str):
    db = get_db()

    student = 

    db.delete()

def leaveStudentFromGroup(student_id: int, group_id: int):
    db = get_db()

    group_student_relationship = db.query(models.GroupStudent).filter(
        models.GroupStudent.student_id == student_id, models.GroupStudent.group_id == group_id
    )

    db.delete(group_student_relationship)
    db.commit()