# academics/models.py

from django.db import models

# from django.conf import settings
from django.contrib.auth.models import User


class Department(models.Model):
    dept_name = models.CharField(max_length=100, unique=True, null=False)

    def __str__(self):
        return self.dept_name


class Course(models.Model):
    course_name = models.CharField(max_length=100, unique=True, null=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return self.course_name


class Subject(models.Model):
    sub_code = models.CharField(max_length=10, unique=True, null=False)
    sub_name = models.CharField(max_length=100, null=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    credits = models.IntegerField(null=False)
    teacher = models.ForeignKey(
        "Teacher",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subjects",
    )

    @property
    def semester(self):
        """
        Derive semester from the subject code.
        Convention: the 2nd digit of the numeric part represents the semester.
        Example: ME13103 -> numeric part '13103' -> '3' (semester 3)
        """
        digits = "".join(ch for ch in self.sub_code if ch.isdigit())
        if len(digits) >= 2:
            try:
                return int(digits[1])
            except ValueError:
                return None
        return None

    def __str__(self):
        return f"{self.sub_code}: {self.sub_name}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    roll_no = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=100, null=False)
    email = models.EmailField(unique=True, null=False)
    phone = models.CharField(max_length=15, blank=True)
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    programme = models.CharField(max_length=50, default="B.TECH")
    current_semester = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.roll_no} - {self.name}"


class Teacher(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True
    )  # Add this line
    name = models.CharField(max_length=100, null=False)
    email = models.EmailField(unique=True, null=False)
    phone = models.CharField(max_length=15, blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT)

    def __str__(self):
        return self.name


class Test(models.Model):
    EXAM_CHOICES = [
        ("Internal", "Internal"),
        ("Midterm1", "Midterm1"),
        ("Midterm2", "Midterm2"),
        ("Endterm", "Endterm"),
        ("LabInternal", "LabInternal"),
        ("Labfinal", "LabFinal"),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    exam_type = models.CharField(max_length=11, choices=EXAM_CHOICES, null=False)
    max_marks = models.IntegerField(null=False)
    test_date = models.DateField(null=False)

    def __str__(self):
        return f"{self.subject} - {self.exam_type}"


class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    obtained_marks = models.IntegerField(null=False)

    class Meta:
        unique_together = (
            "student",
            "test",
        )  # a student can only have one result per test

    def __str__(self):
        return f"Result for {self.student} in {self.test}"


class Marksheet(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    semester = models.IntegerField(null=False)
    is_published = models.BooleanField(default=False)
    # file_path = models.CharField(max_length=255, blank=True, null=True)
    # generated_by = models.CharField(max_length=100)
    generated_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        # a student can only have one marksheet object per semester
        unique_together = ("student", "semester")

    def __str__(self):
        return f"Marksheet for {self.student} - Sem {self.semester} - Published: {self.is_published}"
