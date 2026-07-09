"""Auto-inject the overlay CSS/JS before </body> on HTML responses.

DEBUG-only. Skips streaming responses and non-HTML content types. Idempotent.
"""

from __future__ import annotations

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

_INJECT = (
    '<link rel="stylesheet" href="/static/djust_designer/overlay.css">'
    '<script src="/static/djust_designer/overlay.js" defer></script>'
)


class DjustDesignerMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if not getattr(settings, "DEBUG", False):
            return response
        if getattr(response, "streaming", False):
            return response
        ct = response.get("Content-Type", "") or ""
        if "text/html" not in ct:
            return response
        content = response.content.decode(response.charset)
        if "djust_designer/overlay.js" in content:
            return response
        if "</body>" not in content:
            return response
        content = content.replace("</body>", _INJECT + "</body>", 1)
        response.content = content.encode(response.charset)
        if response.has_header("Content-Length"):
            response["Content-Length"] = str(len(response.content))
        return response
