from django.shortcuts import render

# `school` is available in every template via schools.context_processors.school


def school_home(request):
    return render(request, "public/themes/default/base.html")


def school_about(request):
    return render(request, 'public/themes/default/about.html')


def school_admissions(request):
    return render(request, 'public/themes/default/admissions.html')


def school_news(request):
    return render(request, 'public/themes/default/news.html')


def school_news_detail(request, slug):
    return render(request, 'public/themes/default/news_detail.html', {'slug': slug})


def school_contact(request):
    return render(request, 'public/themes/default/contact.html')
