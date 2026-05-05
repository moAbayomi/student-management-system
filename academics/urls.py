from django.urls import path
from .views import create_class_arm, manage_arms, load_arms, delete_arm_htmx, manage_subjects, load_sub

app_name = 'acad'

urlpatterns = [
    path('manage-arms/', manage_arms, name='manage-arms'),
    path('manage-subs/', manage_subjects, name='manage-subs'),
    path('load-arms/<int:level_id>/', load_arms, name='load-arms'),
    path('load-sub/<str:category>/', load_sub, name='load-sub'),
    path('create-arm/', create_class_arm, name='create-class-arm'),
    path('delete-arm/<int:arm_id>/', delete_arm_htmx, name='delete-arm'),
]