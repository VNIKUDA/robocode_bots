from database.database import setupDatabase, resetDatabase
from database import models, control

# resetDatabase()
setupDatabase()

control.addCourse("Arduino Junior")
control.addCourse("Intro Coding")
control.addCourse("Unity Beginner")
control.addCourse("Unity 2D")

student = control.addStudent("AleksGoncharuk", "Гончарук Олександр")
teacher = control.addTeacher("AleksGoncharuk", "Гончарук Олександр")

group1 = control.addGroup("ПТ", 18, 1, 1, 1)
control.joinStudentToGroup(student.id, group1.id)

student1 = control.addStudent("AleksGoncharuk1", "Гончарук Олександр")
group2 = control.addGroup("ЧТ", 18, 1, 1, 1)
control.joinStudentToGroup(student1.id, group2.id)
# control.joinStudentToGroup(student.id, group.id)

print([(group.course, group.day) for group in control.getStudentGroups(student1.username)])
print([(group.course, group.day) for group in control.getTeacherGroups(teacher.id)])