from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from database.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, index=True, primary_key=True)
    username = Column(String(50), unique=True)
    name = Column(String(60))
    notify = Column(Boolean, default=0)

    groups = relationship("Group", secondary="group_students", back_populates="students")


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, index=True, primary_key=True)
    username = Column(String(50), unique=True)
    name = Column(String(60))
    isAdmin = Column(Boolean, default=False)

    groups = relationship("Group", cascade="all, delete", back_populates="teacher")


class CourseCategory(Base):
    __tablename__ = "course_categories"

    id = Column(Integer, index=True, primary_key=True)
    name = Column(String, unique=True)

    courses = relationship("Course", back_populates="course_category")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, index=True, primary_key=True)
    name = Column(String(20), unique=True)
    course_category_id = Column(Integer, ForeignKey("course_categories.id"))
    
    course_category = relationship("CourseCategory", cascade="all, delete", back_populates="courses")
    groups = relationship("Group", cascade="all, delete", back_populates="course")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, index=True, primary_key=True)
    day = Column(String(2))
    time = Column(Integer)
    room = Column(Integer)
    course_id = Column(Integer, ForeignKey("courses.id"))
    teacher_id = Column(Integer, ForeignKey("teachers.id"))

    teacher = relationship("Teacher", back_populates="groups")
    course = relationship("Course", back_populates="groups", lazy="joined")
    students = relationship("Student", secondary="group_students", back_populates="groups", lazy="joined")

    __table_args__ = (
        UniqueConstraint("day", "time", "room", name="_group_uc_"),
    )


class GroupStudent(Base):
    __tablename__ = "group_students"

    id = Column(Integer, index=True, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    balance = Column(Float, default=0)
    has_answered = Column(Boolean, default=0)