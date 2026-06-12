from django.http import HttpResponse


_CORS_HEADERS = {
    "Access-Control-Allow-Origin":  "*",
    "Access-Control-Allow-Headers": "Accept, Accept-Encoding, Authorization, Content-Type, DNT, Origin, User-Agent, X-CSRFToken, X-Requested-With",
    "Access-Control-Allow-Methods": "DELETE, GET, OPTIONS, PATCH, POST, PUT",
    "Access-Control-Max-Age":       "86400",
}


class ForceCORSMiddleware:
    """Guarantee CORS headers on every API response — belt-and-suspenders."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Short-circuit OPTIONS preflights immediately — no view needed
        if request.method == "OPTIONS" and request.path.startswith("/api/"):
            response = HttpResponse(status=200)
            for k, v in _CORS_HEADERS.items():
                response[k] = v
            return response

        response = self.get_response(request)

        # Add CORS headers to every API response
        if request.path.startswith("/api/"):
            for k, v in _CORS_HEADERS.items():
                response[k] = v

        return response
