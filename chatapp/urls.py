from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('home', views.home, name='home'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('react-dashboard', views.react_dashboard, name='react_dashboard'),

    # New Group Events Dashboard (UI + APIs)
    path('group-events', views.group_events_page, name='group_events_page'),
    path('api/group_events/analytics/', views.group_events_analytics, name='group_events_analytics'),
    path('api/group_events/logs/', views.group_events_logs, name='group_events_logs'),

    path('groups/', views.get_groups, name='get_groups'),
    path('upload/', views.upload_file, name='upload_file'),
    path('delete_file/', views.delete_file, name='delete_file'),
    path('get_uploaded_files/', views.get_uploaded_files, name='get_uploaded_files'),
    path('summarize/', views.summarize, name='summarize'),
    path('ask/', views.ask_question, name='ask_question'),
    path('group_events/', views.group_events, name='group_events'),
    path('event_details/', views.event_details, name='event_details'),
    path('sentiment/', views.sentiment, name='sentiment'),
    path('activity_analysis/', views.activity_analysis, name='activity_analysis'),
    path('export_data/', views.export_data, name='export_data'),
    
    
]