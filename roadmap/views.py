from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import uuid

from assessment.models import Assessment
from .models import Roadmap, RoadmapShare
from django.contrib.auth.models import User

@login_required
def roadmap_list(request):
    """
    Display list of roadmaps for the logged-in user
    """
    user_assessments = Assessment.objects.filter(user=request.user).order_by('-created_at')
    
    # Check if user has any assessments
    if not user_assessments.exists():
        messages.info(request, "To get started, let's create your first business assessment. This will help us generate a personalized roadmap for your business growth.")
        return render(request, 'roadmap/roadmap_list.html', {
            'roadmaps': [],
            'title': 'Your Business Roadmaps',
            'show_start_assessment': True
        })
    
    roadmaps = []
    for assessment in user_assessments:
        roadmap, _ = Roadmap.objects.get_or_create(
            assessment=assessment
        )
        roadmaps.append(roadmap)
    
    return render(request, 'roadmap/roadmap_list.html', {
        'roadmaps': roadmaps,
        'title': 'Your Business Roadmaps',
        'show_start_assessment': False
    })

@login_required
def roadmap_view(request, assessment_id):
    """
    Display individual roadmap based on assessment
    """
    assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)
    roadmap, created = Roadmap.objects.get_or_create(assessment=assessment)
    
    # Handle regenerate request
    if request.method == 'POST' and 'regenerate' in request.POST:
        roadmap.status = 'pending'
        roadmap.save()
        created = True  # Force regeneration
    
    if created or roadmap.status == 'pending':
        try:
            roadmap.status = 'generating'
            roadmap.save()
            
            roadmap_data = generate_ai_roadmap(assessment)
            roadmap.recommendations = roadmap_data
            roadmap.status = 'generated'
            roadmap.generated_at = timezone.now()
            roadmap.error_message = None
            roadmap.save()
            
            messages.success(request, "Your business roadmap has been generated successfully!")
        except Exception as e:
            roadmap.status = 'failed'
            roadmap.error_message = str(e)
            roadmap.save()
            messages.error(request, 'We encountered an issue while generating your roadmap. Please try again later.')
            return redirect('roadmap:list')
    
    return render(request, 'roadmap/roadmap_view.html', {
        'roadmap': roadmap,
        'assessment': assessment,
        'title': f'Business Roadmap - {assessment.business_name}'
    })

@login_required
def roadmap_print(request, assessment_id):
    """
    Generate printable version of roadmap
    """
    assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)
    roadmap = get_object_or_404(Roadmap, assessment=assessment)
    
    if not roadmap.is_ready:
        messages.error(request, "Please wait for your roadmap to be generated before printing.")
        return redirect('roadmap:view', assessment_id=assessment_id)
    
    return render(request, 'roadmap/roadmap_print.html', {
        'roadmap': roadmap,
        'assessment': assessment,
        'title': f'Business Roadmap - {assessment.business_name} (Print Version)'
    })

@login_required
def roadmap_share(request, assessment_id):
    """
    Share roadmap via email or generate shareable link
    """
    assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)
    roadmap = get_object_or_404(Roadmap, assessment=assessment)
    
    if not roadmap.is_ready:
        messages.error(request, "Please wait for your roadmap to be generated before sharing.")
        return redirect('roadmap:view', assessment_id=assessment_id)
    
    if request.method == 'POST':
        # Email sharing
        if 'email' in request.POST:
            recipient_email = request.POST.get('email')
            message = request.POST.get('message', '')
            
            share = RoadmapShare.objects.create(
                roadmap=roadmap,
                created_by=request.user,
                shared_with_email=recipient_email,
                expires_at=timezone.now() + timedelta(days=7)
            )
            
            share_url = request.build_absolute_uri(
                reverse('roadmap:shared', args=[share.share_token])
            )
            
            context = {
                'roadmap': roadmap,
                'message': message,
                'share_url': share_url,
                'expires_at': share.expires_at,
                'sender_name': request.user.get_full_name() or request.user.email,
            }
            
            html_message = render_to_string('roadmap/email/share.html', context)
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(
                    subject=f'Business Roadmap Shared by {context["sender_name"]}',
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient_email],
                    html_message=html_message
                )
                messages.success(request, f'Your roadmap has been shared with {recipient_email}')
                return redirect('roadmap:view', assessment_id=assessment_id)
            except Exception as e:
                messages.error(request, 'We encountered an issue sending the email. Please try again later.')
        
        # Link generation
        elif 'generate_link' in request.POST:
            share = RoadmapShare.objects.create(
                roadmap=roadmap,
                created_by=request.user,
                expires_at=timezone.now() + timedelta(days=7)
            )
            
            share_url = request.build_absolute_uri(
                reverse('roadmap:shared', args=[share.share_token])
            )
            
            return render(request, 'roadmap/share.html', {
                'assessment': assessment,
                'roadmap': roadmap,
                'share_url': share_url,
                'expires_at': share.expires_at,
            })
    
    return render(request, 'roadmap/share.html', {
        'assessment': assessment,
        'roadmap': roadmap,
    })

def shared_roadmap(request, share_token):
    """
    View for accessing a shared roadmap
    """
    share = get_object_or_404(RoadmapShare, share_token=share_token)
    
    if share.is_expired:
        messages.error(request, 'This shared link has expired. Please request a new link from the sender.')
        return redirect('home')
    
    if not share.roadmap.is_ready:
        messages.error(request, 'This roadmap is still being generated. Please try again later.')
        return redirect('home')
    
    share.access_count += 1
    share.last_accessed = timezone.now()
    share.save()
    
    return render(request, 'roadmap/shared.html', {
        'roadmap': share.roadmap,
        'share': share,
    })

def generate_ai_roadmap(assessment):
    """
    Generate AI-based roadmap using assessment data
    This is a placeholder function - implement your ML logic here
    """
    roadmap_data = {
        'summary': f"Strategic Roadmap for {assessment.business_name}",
        'sections': [
            {
                'title': 'Current State Analysis',
                'content': 'Based on your assessment...',
                'recommendations': []
            },
            {
                'title': 'Short-term Goals (0-6 months)',
                'content': 'Priority actions...',
                'recommendations': []
            },
            {
                'title': 'Medium-term Strategy (6-18 months)',
                'content': 'Strategic initiatives...',
                'recommendations': []
            },
            {
                'title': 'Long-term Vision (18+ months)',
                'content': 'Future state...',
                'recommendations': []
            }
        ],
        'key_metrics': [],
        'implementation_timeline': []
    }
    
    return roadmap_data