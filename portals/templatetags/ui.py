"""Small template helpers for the shared UI.

    {% load ui %}
    {% icon "users" %}                       -> an 18px Lucide icon
    {% icon "users" "w-4 h-4" %}             -> with your own size classes
    {% nav_link "portal:manage-students" "Students" "users" also="portal:student-detail" %}
"""
from django import template
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

# Lucide icon paths (https://lucide.dev), stroke-based so they inherit text colour.
ICONS = {
    "dashboard": '<rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "teacher": '<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z"/><path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>',
    "calendar": '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>',
    "layers": '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
    "attendance": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "grades": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "clipboard": '<rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
    "megaphone": '<path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/>',
    "card": '<rect width="20" height="14" x="2" y="5" rx="2"/><path d="M2 10h20"/>',
    "settings": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    "logout": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
    "chevron-left": '<path d="m15 18-6-6 6-6"/>',
    "chevron-right": '<path d="m9 18 6-6-6-6"/>',
    "panel-right": '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M15 3v18"/>',
    "pencil": '<path d="M21.17 6.81a1 1 0 0 0-3.99-3.99L3.84 16.17a2 2 0 0 0-.5.83l-1.32 4.35a.5.5 0 0 0 .62.62l4.35-1.32a2 2 0 0 0 .83-.5z"/>',
    "building": '<rect width="16" height="20" x="4" y="2" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M12 6h.01"/><path d="M12 10h.01"/><path d="M12 14h.01"/><path d="M16 10h.01"/><path d="M16 14h.01"/><path d="M8 10h.01"/><path d="M8 14h.01"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
}


@register.simple_tag
def icon(name, classes="w-[18px] h-[18px] shrink-0"):
    paths = ICONS.get(name, "")
    return format_html(
        '<svg class="{}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>',
        classes, mark_safe(paths),
    )


@register.inclusion_tag("portals/partials/nav_link.html", takes_context=True)
def nav_link(context, url_name, label, icon_name, badge=None, also="", soon=False):
    """A sidebar link that highlights itself when you're on its page.

    `also` is a comma-separated list of other URL names that should
    highlight this link too (e.g. a detail page under a list page).
    """
    request = context.get("request")
    match = getattr(request, "resolver_match", None)
    current = f"{match.namespace}:{match.url_name}" if match and match.namespace else getattr(match, "url_name", "")
    names = {url_name, *(n.strip() for n in also.split(",") if n.strip())}
    return {
        "href": "#" if soon else reverse(url_name),
        "label": label,
        "icon_name": icon_name,
        "badge": badge,
        "soon": soon,
        "active": not soon and current in names,
    }


@register.filter
def ui(field):
    """Render a form field with the shared style for its widget type: {{ form.name|ui }}"""
    widget = field.field.widget
    kind = widget.__class__.__name__
    input_type = getattr(widget, "input_type", None)
    if kind == "CheckboxInput":
        css = "checkbox checkbox-sm checkbox-primary"
    elif kind in ("ClearableFileInput", "FileInput"):
        css = "file-input file-input-sm w-full"
    elif input_type == "color":
        css = "h-9 w-16 rounded-md border border-border cursor-pointer"
    else:
        css = "ui-input"
    existing = widget.attrs.get("class", "")
    return field.as_widget(attrs={"class": f"{existing} {css}".strip()})
