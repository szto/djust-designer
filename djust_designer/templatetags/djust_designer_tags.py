"""Optional manual injection: `{% load djust_designer_tags %}{% djust_designer_scripts %}`.

The middleware already auto-injects; this tag exists for users who want
explicit placement (e.g. above a strict CSP-guarded </body>).
"""

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def djust_designer_scripts() -> str:
    if not getattr(settings, "DEBUG", False):
        return ""
    return mark_safe(
        '<link rel="stylesheet" href="/static/djust_designer/overlay.css">'
        '<script src="/static/djust_designer/overlay.js" defer></script>'
    )
