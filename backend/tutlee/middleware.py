import asyncio
from django.http import HttpResponse

_CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Headers": (
        "Accept, Accept-Encoding, Authorization, Content-Type, "
        "DNT, Origin, User-Agent, X-CSRFToken, X-Requested-With"
    ),
    "Access-Control-Allow-Methods": "DELETE, GET, OPTIONS, PATCH, POST, PUT",
    "Access-Control-Max-Age":       "86400",
}

try:
    from asgiref.sync import markcoroutinefunction as _mark
except ImportError:
    def _mark(f): pass


def _add(response, path):
    if path.startswith("/api/"):
        for k, v in _CORS_HEADERS.items():
            response[k] = v
    return response


class ForceCORSMiddleware:
    """Position-0 middleware: short-circuit OPTIONS + stamp CORS on all /api/ responses."""
    async_capable = True

    def __init__(self, get_response):
        self.get_response = get_response
        if asyncio.iscoroutinefunction(self.get_response):
            _mark(self)

    def __call__(self, request):
        if asyncio.iscoroutinefunction(self.get_response):
            return self._async(request)
        if request.method == "OPTIONS" and request.path.startswith("/api/"):
            return _add(HttpResponse(status=200), request.path)
        return _add(self.get_response(request), request.path)

    async def _async(self, request):
        if request.method == "OPTIONS" and request.path.startswith("/api/"):
            return _add(HttpResponse(status=200), request.path)
        return _add(await self.get_response(request), request.path)
