from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('groups/', views.get_groups, name='get_groups'),
    path('upload/', views.upload_file, name='upload_file'),
    path('delete_file/', views.delete_file, name='delete_file'),
    path('get_uploaded_files/', views.get_uploaded_files, name='get_uploaded_files'),
    path('summarize/', views.summarize, name='summarize'),
    path('ask/', views.ask_question, name='ask_question'),
    path('group_events/', views.group_events, name='group_events'),
    path('event_details/', views.event_details, name='event_details'),
    path('sentiment/', views.sentiment, name='sentiment'),
    path('topic_analysis/', views.topic_analysis, name='topic_analysis'),
    path('activity_analysis/', views.activity_analysis, name='activity_analysis'),
    path('export_data/', views.export_data, name='export_data'),
]