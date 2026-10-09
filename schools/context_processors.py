from django.utils.functional import SimpleLazyObject

from .services import get_school, get_current_term


def school(request):
    """Make `school` available in every template, e.g. {{ school.name }}.

    SimpleLazyObject means the database is only hit if a template actually uses it.
    """
    return {'school': SimpleLazyObject(get_school)}

def current_term(request):
    return {'current_term': SimpleLazyObject(get_current_term)}