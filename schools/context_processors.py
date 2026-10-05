from django.utils.functional import SimpleLazyObject

from .services import get_school


def school(request):
    """Make `school` available in every template, e.g. {{ school.name }}.

    SimpleLazyObject means the database is only hit if a template actually uses it.
    """
    return {'school': SimpleLazyObject(get_school)}
