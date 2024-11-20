from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from assessment.models import Assessment
from .services import BusinessAnalyzer
from django.core.cache import cache
import json

@login_required
@require_http_methods(["GET"])
def dashboard(request):
    """User dashboard view"""
    assessments = Assessment.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'assessments': assessments,
        'completed_count': assessments.filter(status='completed').count(),
        'in_progress_count': assessments.filter(status='in_progress').count(),
    }
    return render(request, 'core/dashboard.html', context)

@login_required
@require_http_methods(["POST"])
def analyze_assessment(request, assessment_id):
    """API endpoint to analyze an assessment"""
    try:
        assessment = Assessment.objects.get(id=assessment_id, user=request.user)
        
        # Check cache first
        cache_key = f'analysis_{assessment_id}'
        analysis = cache.get(cache_key)
        
        if not analysis:
            analyzer = BusinessAnalyzer()
            analysis = analyzer.analyze_assessment(assessment)
            # Cache for 1 hour
            cache.set(cache_key, analysis, 3600)
        
        return JsonResponse({
            'status': 'success',
            'data': analysis
        })
    except Assessment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Assessment not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)