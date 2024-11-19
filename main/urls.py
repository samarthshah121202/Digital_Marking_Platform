from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create_assignment/', views.create_assignment, name='create_assignment'),
    path('assignments/<int:assignment_id>', views.assignment_detail, name='assignment_detail'),
    path('assignments/<int:assignment_id>/markscheme/<int:submission_id>/', views.view_markscheme, name='view_markscheme'),
    path('assignments/<int:assignment_id>/marks/', views.view_marks, name='view_marks'),
    path('delete_assignment/<int:assignment_id>/', views.delete_assignment, name='delete_assignment'),
    path('save-marks/', views.save_marks, name='save_marks'),
] 



