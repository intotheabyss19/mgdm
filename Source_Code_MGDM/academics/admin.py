# academics/admin.py

from django.contrib import admin
from .models import (
    Department,
    Course,
    Subject,
    Student,
    Teacher,
    Test,
    Result,
    Marksheet
)

admin.site.register(Department)
admin.site.register(Course)
admin.site.register(Subject)
admin.site.register(Student)
admin.site.register(Teacher)
admin.site.register(Test)
admin.site.register(Result)
admin.site.register(Marksheet)
