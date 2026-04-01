# academics/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('upload-marks/<int:test_id>/', views.upload_marks_view, name='upload_marks'),
    path('view-marks/<int:test_id>/', views.view_marks_view, name='view_marks'),
    path('edit-mark/<int:result_id>/', views.edit_mark_view, name='edit_mark'),
    path('management/bulk-student-upload/', views.bulk_student_upload_view, name='bulk_student_upload'),
    path('marksheet/semester/<int:semester>/', views.view_marksheet, name='view_marksheet'),
    path('marksheet/semester/<int:semester>/download/', views.download_marksheet_pdf, name='download_marksheet_pdf'),
    path('change-password/', views.change_password_view, name='change_password'),
    path('management/bulk-subject-upload/', views.bulk_subject_upload_view, name='bulk_subject_upload'),
    path('management/bulk-teacher-upload/', views.bulk_teacher_upload_view, name='bulk_teacher_upload'),
    path('select-semester/', views.select_semester_view, name='select_semester'),
    path('management/publish-marksheets/', views.publish_marksheets_view, name='publish_marksheets'),
    path('management/review-marks/<str:roll_no>/<int:semester>/', views.review_student_marks_view, name='review_student_marks'),
]
