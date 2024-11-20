# roadmap/urls.py
from django.urls import path
from . import views

app_name = 'roadmap'

urlpatterns = [
    path('', views.roadmap_list, name='list'),
    path('<int:assessment_id>/', views.roadmap_view, name='view'),
    path('<int:assessment_id>/print/', views.roadmap_print, name='print'),
    path('<int:assessment_id>/share/', views.roadmap_share, name='share'),
    path('shared/<uuid:share_token>/', views.shared_roadmap, name='shared'),
]