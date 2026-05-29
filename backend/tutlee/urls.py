from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import LoginView
import os


def serve_js_file(filename):
    """Serve a JS file from the repo root (one level above backend/)."""
    def view(request):
        filepath = os.path.join(str(settings.BASE_DIR.parent), filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            resp = HttpResponse(content, content_type='application/javascript')
            resp['Cache-Control'] = 'public, max-age=300'
            return resp
        except FileNotFoundError:
            return HttpResponse(
                f'console.error("Could not load {filename}");',
                content_type='application/javascript',
                status=404,
            )
    return view


urlpatterns = [
    # Django admin
    path('django-admin/', admin.site.urls),

    # Serve JS files that HTML pages depend on
    path('api.js',    serve_js_file('api.js'),    name='api-js'),

    # Serve HTML files
    path('', TemplateView.as_view(template_name='index.html'), name='app'),
    path('admin-panel/', TemplateView.as_view(template_name='admin.html'), name='admin-panel'),

    # Auth
    path('api/auth/login/',   LoginView.as_view(),       name='token_obtain'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # App APIs
    path('api/accounts/',     include('accounts.urls')),
    path('api/sessions/',     include('sessions_app.urls')),
    path('api/assessments/',  include('assessments.urls')),
    path('api/kyt/',          include('kyt.urls')),
    path('api/rings/',        include('study_rings.urls')),
    path('api/reports/',      include('reports.urls')),
    path('api/payments/',     include('payments.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
