from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, index=True, primary_key=True)
    username = Column(String(50), unique=True)
    name = Column(String(60))

    groups = relationship("Group", secondary="group_students", back_populates="students")

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, index=True, primary_key=True)
    username = Column(String(50), unique=True)
    name = Column(String(60))
    isAdmin = Column(Boolean, default=False)

    groups = relationship("Group", back_populates="teacher")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, index=True, primary_key=True)
    name = Column(String(20), unique=True)
    
    groups = relationship("Group", back_populates="course")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, index=True, primary_key=True)
    day = Column(String(2))
    time = Column(Integer)
    room = Column(Integer)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete='CASCADE'))
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete='CASCADE'))

    teacher = relationship("Teacher", back_populates="groups")
    course = relationship("Course", back_populates="groups")
    students = relationship("Student", secondary="group_students", back_populates="groups")


class GroupStudent(Base):
    __tablename__ = "group_students"

    id = Column(Integer, index=True, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete='CASCADE'))
    student_id = Column(Integer, ForeignKey("students.id", ondelete='CASCADE'))
    balance = Column(Float, default=0)