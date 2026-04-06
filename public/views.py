import os
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from schools.models import School

def school_home(request):
        
    return render(request, "public/themes/default/base.html")

def _ctx(school_slug):
    """Base context every view needs."""
    return {'school_slug': school_slug}


def school_about(request, school_slug):
    return render(request, 'public/themes/default/about.html', _ctx(school_slug))


def school_admissions(request, school_slug):
    return render(request, 'public/themes/default/admissions.html', _ctx(school_slug))


def school_news(request, school_slug):
    return render(request, 'public/themes/default/news.html', _ctx(school_slug))


def school_news_detail(request, school_slug, slug):
    ctx = _ctx(school_slug)
    ctx['slug'] = slug
    return render(request, 'public/themes/default/news_detail.html', ctx)


def school_contact(request, school_slug):
    return render(request, 'public/themes/default/contact.html', _ctx(school_slug))
