from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import HttpResponse, JsonResponse
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import LoginView, SiteContentView
import os

# ── ONE-TIME DB FLUSH (remove after use) ─────────────────────────────────────
_FLUSH_SECRET = 'tutlee-flush-2026-xK9m'

def flush_db(request):
    """Delete all user data. Hit once then this endpoint will be removed."""
    if request.GET.get('secret') != _FLUSH_SECRET:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    try:
        from django.contrib.auth import get_user_model
        from sessions_app.models import Session
        from kyt.models import KYTApplication
        from payments.models import Transaction, Payout
        from assessments.models import Assessment
        from study_rings.models import StudyRing
        from reports.models import Report
        User = get_user_model()
        counts = {
            'sessions': Session.objects.all().delete()[0],
            'kyt': KYTApplication.objects.all().delete()[0],
            'transactions': Transaction.objects.all().delete()[0],
            'payouts': Payout.objects.all().delete()[0],
            'assessments': Assessment.objects.all().delete()[0],
            'rings': StudyRing.objects.all().delete()[0],
            'reports': Report.objects.all().delete()[0],
            'users': User.objects.all().delete()[0],
        }
        return JsonResponse({'status': 'flushed', 'deleted': counts})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


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
                resp['Ca