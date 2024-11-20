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
    # Implement roadmap listing logic
    pass

@login_required
def roadmap_view(request, assessment_id):
    # Implement roadmap view logic
    pass

@login_required
def roadmap_print(request, assessment_id):
    # Implement roadmap print logic
    pass

@login_required
def roadmap_share(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)
    roadmap = get_object_or_404(Roadmap, assessment=assessment)
    
    if request.method == 'POST':
        # Email sharing
        if 'email' in request.POST:
            recipient_email = request.POST.get('email')
            message = request.POST.get('message', '')
            
            # Create a shareable link
            share = RoadmapShare.objects.create(
                roadmap=roadmap,
                created_by=request.user,
                shared_with_email=recipient_email,
                expires_at=timezone.now() + timedelta(days=7)
            )
            
            share_url = request.build_absolute_uri(
                reverse('roadmap:shared', args=[share.share_token])
            )
            
            # Prepare email content
            context = {
                'roadmap': roadmap,
                'message': message,
                'share_url': share_url,
                'expires_at': share.expires_at,
            }
            
            html_message = render_to_string('roadmap/email/share.html', context)
            plain_message = strip_tags(html_message)
            
            try:
                send_mail(
                    subject='Business Roadmap Shared with You',
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[recipient_email],
                    html_message=html_message
                )
                messages.success(request, f'Roadmap has been shared with {recipient_email}')
                return redirect('roadmap:view', assessment_id=assessment_id)
            except Exception as e:
                messages.error(request, 'Failed to send email. Please try again later.')
        
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
    """View for accessing a shared roadmap"""
    share = get_object_or_404(RoadmapShare, share_token=share_token)
    
    if share.is_expired:
        messages.error(request, 'This shared link has expired.')
        return redirect('home')
    
    # Update access count and last accessed
    share.access_count += 1
    share.last_accessed = timezone.now()
    share.save()
    
    return render(request, 'roadmap/shared.html', {
        'roadmap': share.roadmap,
        'share': share,
    })