from django.urls import path
from . import views

app_name = 'assessment'

urlpatterns = [
    path('', views.assessment_list, name='list'),
    path('start/', views.start_assessment, name='start'),
    path('<int:assessment_id>/question/<int:question_number>/', views.question_view, name='question'),
    path('<int:assessment_id>/complete/', views.assessment_complete, name='complete'),
    path('<int:assessment_id>/download-pdf/', views.download_pdf, name='download_pdf'),
]