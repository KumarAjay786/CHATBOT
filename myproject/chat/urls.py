from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.chat_home, name='home'),
    path('new/', views.new_conversation, name='new_conversation'),
    path('conversation/<int:conversation_id>/',
         views.conversation_detail, name='conversation_detail'),
    path('send/', views.send_message, name='send_message'),
    path('delete/<int:conversation_id>/',
         views.delete_conversation, name='delete_conversation'),
    path('update-title/<int:conversation_id>/',
         views.update_title, name='update_title'),
]
