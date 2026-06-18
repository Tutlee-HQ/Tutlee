from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import LoginView, SiteContentView
import os


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



@csrf_exempt
def dev_flush(request):
    """Drop ALL public tables so the next deploy runs migrations from scratch.
    Protected by FLUSH_SECRET env var. Visit with ?key=<FLUSH_SECRET>&drop=1 to drop tables."""
    import os
    secret = os.environ.get('FLUSH_SECRET', '')
    if not secret or request.GET.get('key') != secret:
        return JsonResponse({'error': 'forbidden'}, status=403)
    from django.db import connection
    with connection.cursor() as cur:
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        tables = [r[0] for r in cur.fetchall()]
        if tables:
            if request.GET.get('drop') == '1':
                # Drop tables entirely so next migrate creates them fresh
                cur.execute('DROP TABLE IF EXISTS ' + ', '.join(f'"{t}"' for t in tables) + ' CASCADE')
                return JsonResponse({'status': 'dropped', 'tables': tables})
            else:
                # Default: truncate (keep schema, clear data)
                cur.execute('TRUNCATE TABLE ' + ', '.join(f'"{t}"' for t in tables) + ' RESTART IDENTITY CASCADE')
                return JsonResponse({'status': 'truncated', 'tables': tables})
    return JsonResponse({'status': 'nothing_to_do', 'tables': []})

urlpatterns = [
    path('api/health/', health, name='health'),
    path('api/dev/flush/', dev_flush, name='dev-flush'),
    path('django-admin/', admin.site.urls),

    path('api.js', serve_js_file('api.js'), name='api-js'),

    path('', TemplateView.as_view(template_name='index.html'), name='app'),
    path('admin-panel/', TemplateView.as_view(template_name='admin.html'), name='admin-panel'),

    path('api/auth/login/',   LoginView.as_view(),        name='token_obtain'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/accounts/',    include('accounts.urls')),
    pa