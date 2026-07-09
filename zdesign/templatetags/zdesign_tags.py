"""Optional manual injection: `{% load zdesign_tags %}{% zdesign_scripts %}`.

The middleware already auto-injects; this tag exists for users who want
explicit placement (e.g. above a strict CSP-guarded </body>).
"""

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def zdesign_scripts() -> str:
    if not getattr(settings, "DEBUG", False):
        return ""
    return mark_safe(
        '<link rel="stylesheet" href="/static/zdesign/overlay.css">'
        '<script src="/static/zdesign/overlay.js" defer></script>'
    )
