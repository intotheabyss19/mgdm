# academics/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.conf import settings
from django.utils import timezone

from .models import Department, Student, Teacher, Test, Result, Course, Subject, Marksheet
from .forms import ResultForm
from .grading import calculate_grade

import pandas as pd
import os

from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.colors import grey
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF

THEORY_TEST_TYPES = ['Internal', 'Midterm1', 'Midterm2', 'Endterm']
LAB_TEST_TYPES = ['LabInternal', 'Labfinal']

EXAM_TYPE_MAX_MARKS = {
    'Internal': 20,
    'Midterm1': 15,
    'Midterm2': 15,
    'Endterm': 50,
    'LabInternal': 60,
    'Labfinal': 40,
}


def home(request):
    return render(request, 'academics/home.html')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard') 
        else:
            return render(request, 'academics/login.html', {'form': form, 'error': 'Invalid username or password.'})
    
    form = AuthenticationForm()
    return render(request, 'academics/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')

def dashboard_view(request):
    if request.user.is_staff:
        return render(request, 'academics/admin_dashboard.html')
 
    elif hasattr(request.user, 'teacher'):
        teacher = request.user.teacher
        tests = Test.objects.filter(teacher=teacher).order_by('-test_date')
        context = {
            'tests': tests
        }
        return render(request, 'academics/teacher_dashboard.html', context)

    elif hasattr(request.user, 'student'):
        return redirect('select_semester')


def upload_marks_view(request, test_id):
    if not hasattr(request, 'user') or not hasattr(request.user, 'teacher'):
        return redirect('dashboard')

    try:
        test = Test.objects.get(id=test_id, teacher=request.user.teacher)
    except Test.DoesNotExist:
        return redirect('dashboard')

    updated_students = []
    not_found_students = []
    invalid_mark_students = []

    if request.method == 'POST':
        excel_file = request.FILES.get('marks_file')
        if excel_file:
            try:
                df = pd.read_excel(excel_file)
                
                if 'roll_no' not in df.columns or 'obtained_marks' not in df.columns:
                    raise ValueError("Excel file must contain 'roll_no' and 'obtained_marks' columns.")

                for index, row in df.iterrows():
                    roll_no = str(row['roll_no'])
                    obtained_marks = int(row['obtained_marks'])
                    
                    if not (0 <= obtained_marks <= test.max_marks):
                        invalid_mark_students.append({'roll_no': roll_no, 'marks': obtained_marks})

                    try:
                        student = Student.objects.get(roll_no=roll_no)
                        Result.objects.update_or_create(
                            student=student,
                            test=test,
                            defaults={'obtained_marks': obtained_marks}
                        )
                        updated_students.append(student.name)
                    except Student.DoesNotExist:
                        not_found_students.append(roll_no)
                
                context = {
                    'test': test,
                    'success': True,
                    'updated_count': len(updated_students),
                    'not_found_count': len(not_found_students),
                    'not_found_students': not_found_students,
                    'invalid_mark_count': len(invalid_mark_students),
                    'invalid_mark_students': invalid_mark_students,
                }
                return render(request, 'academics/upload_marks.html', context)

            except Exception as e:
                context = {'test': test, 'error': f"An error occurred: {e}"}
                return render(request, 'academics/upload_marks.html', context)

    context = {'test': test}
    return render(request, 'academics/upload_marks.html', context)


def edit_mark_view(request, result_id):
    if not (request.user.is_staff or hasattr(request.user, 'teacher')):
        return redirect('dashboard')

    try:
        if request.user.is_staff:
            result = Result.objects.get(id=result_id)
        else:
            result = Result.objects.get(id=result_id, test__teacher=request.user.teacher)
    except Result.DoesNotExist:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ResultForm(request.POST, instance=result)
        if form.is_valid():
            form.save()
            return redirect('view_marks', test_id=result.test.id)
    else:
        form = ResultForm(instance=result)

    context = {
        'form': form,
        'result': result
    }
    return render(request, 'academics/edit_mark.html', context)


def bulk_student_upload_view(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    if request.method == 'POST':
        excel_file = request.FILES.get('student_file')
        course_id = request.POST.get('course')
        current_semester_raw = request.POST.get('current_semester')
        
        try:
            course = Course.objects.get(id=course_id)

            if not current_semester_raw:
                raise ValueError("Please select the current semester for these students.")
            try:
                current_semester = int(current_semester_raw)
            except (TypeError, ValueError):
                raise ValueError("Current semester must be a valid integer.")
            df = pd.read_excel(excel_file)
            
            required_columns = ['roll_no', 'name', 'email']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(f"File must contain all required columns: {', '.join(required_columns)}")

            created_students = []
            errors = []

            for index, row in df.iterrows():
                roll_no = str(row['roll_no'])
                email = str(row['email'])
                
                if Student.objects.filter(roll_no=roll_no).exists() or User.objects.filter(username=roll_no).exists():
                    errors.append(f"Student with roll number {roll_no} or email {email} already exists.")
                    continue
                
                try:
                    password = str(row['password']) if 'password' in df.columns and pd.notna(row['password']) else roll_no
                    
                    user = User.objects.create_user(username=roll_no, password=password, email=email)
                    
                    Student.objects.create(
                        user=user,
                        roll_no=roll_no,
                        name=str(row['name']),
                        email=email,
                        programme=course.course_name,
                        course=course,
                        current_semester=current_semester,
                    )
                    created_students.append(str(row['name']))
                except Exception as e:
                    errors.append(f"Error creating student {row['name']} ({roll_no}): {e}")

            context = { 'courses': Course.objects.all(), 'success': True, 'created_count': len(created_students), 'error_count': len(errors), 'errors': errors }
            return render(request, 'academics/admin_student_upload.html', context)

        except Exception as e:
            context = {'courses': Course.objects.all(), 'upload_error': f"An error occurred: {e}"}
            return render(request, 'academics/admin_student_upload.html', context)

    context = {'courses': Course.objects.all()}
    return render(request, 'academics/admin_student_upload.html', context)


def bulk_subject_upload_view(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    if request.method == 'POST':
        subject_file = request.FILES.get('subject_file')
        course_id = request.POST.get('course')

        try:
            course = Course.objects.get(id=course_id)
            created_subjects = []
            errors = []

            if not subject_file:
                raise ValueError("Please upload a subject Excel file.")

            df = pd.read_excel(subject_file)

            required_columns = ['sub_code', 'sub_name', 'credits', 'teacher_username']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(
                    "File must contain all required columns: "
                    + ", ".join(required_columns)
                )

            for index, row in df.iterrows():
                try:
                    sub_code = str(row['sub_code']).strip()
                    sub_name = str(row['sub_name']).strip()
                    credits = int(row['credits'])
                    teacher_username_raw = str(row['teacher_username']).strip()

                    if Subject.objects.filter(sub_code=sub_code).exists():
                        errors.append(
                            f"Subject with code {sub_code} already exists. Skipped."
                        )
                        continue

                    teacher = None
                    if teacher_username_raw:
                        if '@' in teacher_username_raw:
                            base_username = teacher_username_raw.split('@', 1)[0]
                        else:
                            base_username = teacher_username_raw

                        try:
                            teacher = Teacher.objects.get(user__username=base_username)
                        except Teacher.DoesNotExist:
                            try:
                                teacher = Teacher.objects.get(email=teacher_username_raw)
                            except Teacher.DoesNotExist:
                                errors.append(
                                    f"No teacher found with username/email {teacher_username_raw} "
                                    f"for subject {sub_code} - {sub_name}. Subject created without teacher."
                                )

                    subject = Subject.objects.create(
                        sub_code=sub_code,
                        sub_name=sub_name,
                        credits=credits,
                        course=course,
                        teacher=teacher,
                    )
                    created_subjects.append(sub_name)

                    is_lab = False
                    try:
                        if len(sub_code) > 4 and sub_code[4] == '2':
                            is_lab = True
                    except Exception:
                        is_lab = False

                    exam_types = LAB_TEST_TYPES if is_lab else THEORY_TEST_TYPES
                    if teacher:
                        for exam_type in exam_types:
                            max_marks = EXAM_TYPE_MAX_MARKS.get(exam_type, 100)
                            Test.objects.get_or_create(
                                subject=subject,
                                teacher=teacher,
                                exam_type=exam_type,
                                defaults={
                                    'max_marks': max_marks,
                                    'test_date': timezone.now().date(),
                                },
                            )
                except Exception as e:
                    errors.append(
                        f"Error processing row {index + 2} "
                        f"({row.get('sub_code', '')}): {e}"
                    )
  
            context = {
                'courses': Course.objects.all(),
                'success': True,
                'created_count': len(created_subjects),
                'error_count': len(errors),
                'errors': errors,
            }
            return render(request, 'academics/admin_subject_upload.html', context)
        except Course.DoesNotExist:
            context = {'courses': Course.objects.all(), 'upload_error': 'The selected course was not found.'}
            return render(request, 'academics/admin_subject_upload.html', context)
        except Exception as e:
            context = {
                'courses': Course.objects.all(),
                'upload_error': f"An error occurred: {e}",
            }
            return render(request, 'academics/admin_subject_upload.html', context)


    context = {'courses': Course.objects.all()}
    return render(request, 'academics/admin_subject_upload.html', context)


def bulk_teacher_upload_view(request):
    """
    Staff-only view to bulk register teachers from an Excel/ODS file.
    Expected columns: name, email, username, phone, department
    - username defaults to the part before '@' in the email if blank.
    - department must match an existing Department.dept_name.
    """
    if not request.user.is_staff:
        return redirect('dashboard')

    if request.method == 'POST':
        teacher_file = request.FILES.get('teacher_file')

        try:
            if not teacher_file:
                raise ValueError("Please upload a teacher Excel file.")

            df = pd.read_excel(teacher_file)

            required_columns = ['name', 'email', 'username', 'phone', 'department']
            if not all(col in df.columns for col in required_columns):
                raise ValueError(
                    "File must contain all required columns: "
                    + ", ".join(required_columns)
                )

            created_teachers = []
            errors = []

            for index, row in df.iterrows():
                try:
                    name = str(row['name']).strip()
                    email = str(row['email']).strip()
                    username_raw = str(row['username']).strip()
                    phone = str(row['phone']).strip() if not pd.isna(row['phone']) else ''
                    department_name = str(row['department']).strip()

                    if not username_raw:
                        username_raw = email.split('@', 1)[0] if '@' in email else email

                    if User.objects.filter(username=username_raw).exists():
                        errors.append(f"User with username {username_raw} already exists. Skipped.")
                        continue
                    if User.objects.filter(email=email).exists():
                        errors.append(f"User with email {email} already exists. Skipped.")
                        continue

                    try:
                        department = Department.objects.get(dept_name=department_name)
                    except Department.DoesNotExist:
                        errors.append(
                            f"Department '{department_name}' not found for teacher {name} ({email})."
                        )
                        continue

                    user = User.objects.create_user(
                        username=username_raw,
                        password=username_raw,
                        email=email,
                    )

                    Teacher.objects.create(
                        user=user,
                        name=name,
                        email=email,
                        phone=phone,
                        department=department,
                    )
                    created_teachers.append(name)
                except Exception as e:
                    errors.append(
                        f"Error processing row {index + 2} "
                        f"({row.get('email', '')}): {e}"
                    )

            context = {
                'success': True,
                'created_count': len(created_teachers),
                'error_count': len(errors),
                'errors': errors,
            }
            return render(request, 'academics/admin_teacher_upload.html', context)
        except Exception as e:
            context = {
                'upload_error': f"An error occurred: {e}",
            }
            return render(request, 'academics/admin_teacher_upload.html', context)

    return render(request, 'academics/admin_teacher_upload.html')


def _compute_marksheet_data(student, semester):
    """
    Shared helper to compute marksheet information (subjects, grades, SGPA, CGPA, status)
    for a given student and semester.
    """
    student_current_sem = getattr(student, 'current_semester', None) or semester
    max_sem_for_aggregate = min(semester, student_current_sem)

    all_course_subjects = Subject.objects.filter(course=student.course)

    current_subjects = [s for s in all_course_subjects if s.semester == semester]

    marksheet_data = []
    total_credits_sem = 0
    total_grade_points_sem = 0
    has_failed = False
    all_marks_uploaded = True

    for subject in current_subjects:
        results = Result.objects.filter(student=student, test__subject=subject)

        if not results.exists():
            all_marks_uploaded = False

        total_obtained = sum(r.obtained_marks for r in results)
        total_max = sum(r.test.max_marks for r in results)
        percentage = (total_obtained / total_max) * 100 if total_max > 0 else 0
        letter_grade, grade_point = calculate_grade(percentage)

        if letter_grade == 'FF':
            has_failed = True

        marksheet_data.append({'subject': subject, 'letter_grade': letter_grade})
        total_credits_sem += subject.credits
        total_grade_points_sem += grade_point * subject.credits

    sgpa = (total_grade_points_sem / total_credits_sem) if total_credits_sem > 0 else 0

    all_past_subjects = [
        s
        for s in all_course_subjects
        if s.semester is not None and s.semester <= max_sem_for_aggregate
    ]
    total_credits_all = 0
    total_grade_points_all = 0

    for subject in all_past_subjects:
        results = Result.objects.filter(student=student, test__subject=subject)
        total_obtained = sum(r.obtained_marks for r in results)
        total_max = sum(r.test.max_marks for r in results)
        percentage = (total_obtained / total_max) * 100 if total_max > 0 else 0
        _, grade_point = calculate_grade(percentage)
        total_credits_all += subject.credits
        total_grade_points_all += grade_point * subject.credits

    cgpa = (total_grade_points_all / total_credits_all) if total_credits_all > 0 else 0

    if has_failed:
        status = "FAIL"
    elif not all_marks_uploaded:
        status = "INCOMPLETE"
    else:
        status = "PASS"

    return {
        'marksheet_data': marksheet_data,
        'sgpa': sgpa,
        'cgpa': cgpa,
        'status': status,
        'all_marks_uploaded': all_marks_uploaded,
        'has_failed': has_failed,
    }


def view_marksheet(request, semester):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    try:
        marksheet_status = Marksheet.objects.get(student=request.user.student, semester=semester)
        if not marksheet_status.is_published:
            return redirect('select_semester')
    except Marksheet.DoesNotExist:
        return redirect('select_semester')

    student = request.user.student

    marksheet_context = _compute_marksheet_data(student, semester)

    context = {
        'student': student,
        'semester': semester,
        'marksheet_data': marksheet_context['marksheet_data'],
        'sgpa': f"{marksheet_context['sgpa']:.2f}"
        if marksheet_context['status'] == "PASS"
        else "N/A",
        'cgpa': f"{marksheet_context['cgpa']:.2f}"
        if marksheet_context['status'] == "PASS"
        else "N/A",
        'status': marksheet_context['status'],
    }
    return render(request, 'academics/marksheet_template.html', context)


def view_marks_view(request, test_id):
    if not hasattr(request, 'user') or not hasattr(request.user, 'teacher'):
        return redirect('dashboard')

    try:
        test = Test.objects.get(id=test_id, teacher=request.user.teacher)
        results = Result.objects.filter(test=test).order_by('student__roll_no')
    except Test.DoesNotExist:
        return redirect('dashboard')

    context = {
        'test': test,
        'results': results,
    }
    return render(request, 'academics/view_marks.html', context)


def download_marksheet_pdf(request, semester):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    try:
        marksheet_status = Marksheet.objects.get(
            student=request.user.student, semester=semester
        )
        if not marksheet_status.is_published:
            return redirect('select_semester')
    except Marksheet.DoesNotExist:
        return redirect('select_semester')

    student = request.user.student
    marksheet_context = _compute_marksheet_data(student, semester)
    marksheet_data = marksheet_context['marksheet_data']
    sgpa_value = marksheet_context['sgpa']
    cgpa_value = marksheet_context['cgpa']
    status = marksheet_context['status']

    display_sgpa = f"{sgpa_value:.2f}" if status == "PASS" else "N/A"
    display_cgpa = f"{cgpa_value:.2f}" if status == "PASS" else "N/A"

    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'
    ] = f'attachment; filename="Marksheet_Sem{semester}_{student.roll_no}.pdf"'
    p = canvas.Canvas(response, pagesize=landscape(letter))
    width, height = landscape(letter)

    p.saveState()
    p.setFont('Helvetica', 12)
    p.setFillColor(grey, alpha=0.08)
    p.rotate(45)
    watermark_text = f"NIT Sikkim - {student.roll_no}"
    for x in range(-10, 20):
        for y in range(-10, 20):
            p.drawString(x * 5 * inch, y * 2 * inch, watermark_text)
    p.restoreState()

    logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'images/logo.png')
    try:
        p.drawImage(logo_path, x=inch, y=height - 1.5*inch, width=inch, height=inch)
    except:
        pass

    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2.0, height - inch, "National Institute of Technology Sikkim")
    p.setFont("Helvetica", 12)
    p.drawCentredString(width / 2.0, height - 1.2 * inch, "PROVISIONAL GRADE CARD")

    info_data = [
        ['Name:', student.name, 'Enroll No.:', student.roll_no],
        ['Department:', student.course.department.dept_name, 'Programme:', student.programme],
        ['Semester:', str(semester), '', ''],
    ]
    info_table = Table(
        info_data,
        colWidths=[1.2 * inch, 3.0 * inch, 1.2 * inch, 2.1 * inch],
    )
    info_table.setStyle(
        TableStyle(
            [
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    iw, ih = info_table.wrap(width - 2 * inch, height)
    info_y = height - 2.2 * inch - ih
    info_table.drawOn(p, inch, info_y)

    grades_header = [
        ['Subject Name', 'Subject Code', 'Course Credit', 'Obtained Grade']
    ]
    grades_data = [
        [
            item['subject'].sub_name,
            item['subject'].sub_code,
            item['subject'].credits,
            item['letter_grade'],
        ]
        for item in marksheet_data
    ]
    grades_table_data = grades_header + grades_data
    grades_table = Table(
        grades_table_data,
        colWidths=[3.5 * inch, 1.5 * inch, 1.25 * inch, 1.25 * inch],
    )
    grades_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]
        )
    )
    gw, gh = grades_table.wrap(width - 2 * inch, height)
    grades_y = info_y - 0.6 * inch - gh
    grades_table.drawOn(p, inch, grades_y)

    y_pos = grades_y - 0.4 * inch
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(
        width - inch,
        y_pos,
        f"SGPA: {display_sgpa}   CGPA: {display_cgpa}   Status: {status}",
    )

    qr_data = (
        f"Name:{student.name},Roll:{student.roll_no},"
        f"Sem:{semester},SGPA:{display_sgpa},CGPA:{display_cgpa},Status:{status}"
    )
    qr_code = QrCodeWidget(qr_data)
    bounds = qr_code.getBounds()
    qr_width = bounds[2] - bounds[0]
    d = Drawing(
        1.2 * inch,
        1.2 * inch,
        transform=[1.2 * inch / qr_width, 0, 0, 1.2 * inch / qr_width, 0, 0],
    )
    d.add(qr_code)
    renderPDF.draw(d, p, inch, inch)

    p.showPage()
    p.save()
    return response


def select_semester_view(request):
    if not hasattr(request.user, 'student'):
        return redirect('dashboard')

    student = request.user.student
    published_marksheets = Marksheet.objects.filter(student=student, is_published=True).order_by('semester')
    semesters = [m.semester for m in published_marksheets]

    return render(request, 'academics/select_semester.html', {'semesters': semesters})


def publish_marksheets_view(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    courses = Course.objects.all()
    selected_course_id = request.GET.get('course')
    selected_semester = request.GET.get('semester')

    students_data = []
    semester_int = None
    if selected_course_id and selected_semester:
        try:
            semester_int = int(selected_semester)
        except (TypeError, ValueError):
            semester_int = None

        if semester_int is not None:
            students = Student.objects.filter(course_id=selected_course_id)
            all_subjects_for_course = Subject.objects.filter(
                course_id=selected_course_id
            )
            subjects_in_sem = [
                s for s in all_subjects_for_course if s.semester == semester_int
            ]

            for student in students:
                all_marks_present = True
                missing_subjects = []
                for subject in subjects_in_sem:
                    if not Result.objects.filter(
                        student=student, test__subject=subject
                    ).exists():
                        all_marks_present = False
                        missing_subjects.append(subject)

                status, _ = Marksheet.objects.get_or_create(
                    student=student, semester=semester_int
                )

                students_data.append(
                    {
                        'student': student,
                        'all_marks_present': all_marks_present,
                        'is_published': status.is_published,
                        'missing_subjects': missing_subjects,
                    }
                )

    if request.method == 'POST':
        student_ids_to_publish = request.POST.getlist('publish')
        action = request.POST.get('action', 'publish')

        if selected_semester:
            try:
                semester_int = int(selected_semester)
            except (TypeError, ValueError):
                semester_int = None
        else:
            semester_int = None

        if semester_int is not None and student_ids_to_publish:
            if action == 'unpublish':
                Marksheet.objects.filter(
                    student_id__in=student_ids_to_publish, semester=semester_int
                ).update(is_published=False)
            else:
                Marksheet.objects.filter(
                    student_id__in=student_ids_to_publish, semester=semester_int
                ).update(is_published=True)
        return redirect(request.get_full_path())

    context = {
        'courses': courses,
        'selected_course_id': selected_course_id,
        'selected_semester': selected_semester,
        'students_data': students_data,
    }
    return render(request, 'academics/publish_marksheets.html', context)

def review_student_marks_view(request, roll_no, semester):
    """
    Staff-only view to inspect a single student's marks for a given semester
    before publishing or troubleshooting issues.
    """
    if not request.user.is_staff:
        return redirect('dashboard')

    try:
        student = Student.objects.get(roll_no=roll_no)
    except Student.DoesNotExist:
        return redirect('publish_marksheets')

    marksheet_context = _compute_marksheet_data(student, semester)

    context = {
        'student': student,
        'semester': semester,
        'marksheet_data': marksheet_context['marksheet_data'],
        'sgpa': f"{marksheet_context['sgpa']:.2f}"
        if marksheet_context['status'] == "PASS"
        else "N/A",
        'cgpa': f"{marksheet_context['cgpa']:.2f}"
        if marksheet_context['status'] == "PASS"
        else "N/A",
        'status': marksheet_context['status'],
    }
    return render(request, 'academics/admin_review_marks.html', context)


def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'academics/change_password.html', {'form': form})
