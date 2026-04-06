from django.urls import path
from .views import *

app_name = 'public'

urlpatterns = [
    path('',            school_home,       name='home'),
    path('about/',      school_about,      name='about'),
    path('admissions/', school_admissions, name='admissions'),
    path('news/',       school_news,       name='news'),
    path('news//', school_news_detail, name='news_detail'),
    path('contact/',    school_contact,    name='contact'),
]