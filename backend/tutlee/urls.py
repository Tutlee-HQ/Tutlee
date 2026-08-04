from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve
from django.views.generic import TemplateView
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import LoginView, SiteContentView
import os

def serve_img_cached(request, path, document_root=None, **kwargs):
    response = serve(request, path, document_root=document_root, **kwargs)
    response['Cache-Control'] = 'public, max-age=604800'  # cache images for 7 days
    return response


def serve_js_file(filename):
    """Serve a JS file — checks multiple locations so it works locally and on Render."""
    def view(request):
        search_paths = [
            os.path.join(str(settings.BASE_DIR), 'static', 'js', filename),
            os.path.join(str(settings.BASE_DIR), 'static', filename),
            os.path.join(str(settings.BASE_DIR.parent), filename),
            os.path.join(str(settings.BASE_DIR), filename),
        ]
        for filepath in search_paths:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                resp = HttpResponse(content, content_type='application/javascript')
                resp['Cache-Control'] = 'public, max-age=60'
                return resp
        return HttpResponse(
            f'console.error("Could not load {filename}");',
            content_type='application/javascript',
            status=404,
        )
    return view


@csrf_exempt
def health(request):
    # Also wake the database — Render free tier DB sleeps independently of Gunicorn
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception:
        pass  # best-effort; server is still up even if DB ping fails
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('api/health/', health, name='health'),
    path('django-admin/', admin.site.urls),

    path('api.js', serve_js_file('api.js'), name='api-js'),

    path('', TemplateView.as_view(template_name='index.html'), name='app'),
    path('admin-panel/', TemplateView.as_view(template_name='admin.html'), name='admin-panel'),
  
    re_path(r'^img/(?P<path>.*)$', serve_img_cached, {'document_root': os.path.join(str(settings.BASE_DIR.parent), 'img')}),
    path('api/auth/login/',   LoginView.as_view(),        name='token_obtain'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/accounts/',    include('accounts.urls')),
    path('api/sessions/',    include('sessions_app.urls')),
    path('api/assessments/', include('assessments.urls')),
    path('api/kyt/',         include('kyt.urls')),
    path('api/rings/',       include('study_rings.urls')),
    path('api/reports/',     include('reports.urls')),
    path('api/payments/',    include('payments.urls')),
    path('about.html',    TemplateView.as_view(template_name='about.html'),    name='about'),
    path('blog.html',     TemplateView.as_view(template_name='blog.html'),     name='blog'),
    path('careers.html',  TemplateView.as_view(template_name='careers.html'),  name='careers'),
    path('help.html',     TemplateView.as_view(template_name='help.html'),     name='help'),
    path('privacy.html',  TemplateView.as_view(template_name='privacy.html'),  name='privacy'),
    path('partners.html',    TemplateView.as_view(template_name='partners.html'),    name='partners'),
    path('press.html',    TemplateView.as_view(template_name='press.html'),    name='press'),
    path('contact.html',    TemplateView.as_view(template_name='contact.html'),    name='contact'),
    path('research.html', TemplateView.as_view(template_name='research.html'), name='research'),
    path('safety.html',   TemplateView.as_view(template_name='safety.html'),   name='safety'),
    path('terms.html',    TemplateView.as_view(template_name='terms.html'),    name='terms'),
    path('api/content/<str:key>/', SiteContentView.as_view(), name='site-content'),
    path('api/content/',          SiteContentView.as_view(), name='site-content-default'),
    # Serve uploaded media files unconditionally (bypasses DEBUG-only static() helper)
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
