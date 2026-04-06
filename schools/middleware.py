from django.shortcuts import get_object_or_404
from django.urls import resolve
from .models import School

class SchoolMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # first part of the URL path (e.g., 'osogbo-grammar')
        path_parts = request.path.strip('/').split('/')
        school_slug = path_parts[0] if path_parts else None

        if school_slug:
            try:
                # We attach the actual School OBJECT to the request
                request.school = School.objects.get(slug=school_slug)
            except School.DoesNotExist:
                # Fallback: If the slug isn't a school, maybe it's a global page
                request.school = None
        else:
            request.school = None

        # 3. Pass the request (with the school attached) to the View
        response = self.get_response(request)
        return response