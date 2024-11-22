from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from .models import Category, Question, Assessment, Response
from roadmap.models import Roadmap, RecommendationTemplate
import json
from django.db.models import Count

@login_required
def assessment_list(request):
    """
    Display list of user's assessments and option to start a new one
    """
    assessments = Assessment.objects.filter(user=request.user).order_by('-created_at')
    incomplete_exists = assessments.filter(completion_date__isnull=True).exists()
    
    context = {
        'assessments': assessments,
        'incomplete_exists': incomplete_exists,
        'completed_count': assessments.filter(completion_date__isnull=False).count(),
    }
    return render(request, 'assessment/assessment_list.html', context)

@login_required
def start_assessment(request):
    """
    Start a new assessment or continue an incomplete one
    """
    # Check for any incomplete assessments
    incomplete_assessment = Assessment.objects.filter(
        user=request.user,
        completion_date__isnull=True
    ).first()
    
    if incomplete_assessment:
        messages.warning(request, 'You have an incomplete assessment. Continuing from where you left off.')
        # Get the last answered question's number
        last_response = Response.objects.filter(assessment=incomplete_assessment).order_by('-created_at').first()
        if last_response:
            next_question_number = last_response.question.order + 1
        else:
            next_question_number = 1
        return redirect('assessment:question', 
                      assessment_id=incomplete_assessment.id,
                      question_number=next_question_number)

    # Create new assessment
    try:
        with transaction.atomic():
            assessment = Assessment.objects.create(user=request.user)
            return redirect('assessment:question', 
                          assessment_id=assessment.id,
                          question_number=1)
    except Exception as e:
        messages.error(request, 'Unable to start assessment. Please try again.')
        return redirect('assessment:list')

@login_required
def question_view(request, assessment_id, question_number):
    """
    Display and handle responses for assessment questions
    """
    assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)
    
    if assessment.completion_date:
        messages.warning(request, 'This assessment has already been completed.')
        return redirect('roadmap:view', assessment_id=assessment_id)

    # Get current question
    try:
        question = Question.objects.select_related('category').get(order=question_number)
    except Question.DoesNotExist:
        if question_number > 1:
            # If we've gone past the last question, complete the assessment
            return complete_assessment(request, assessment)
        raise Http404("Question not found")

    # Calculate progress
    total_questions = Question.objects.count()
    progress = (question_number / total_questions) * 100

    if request.method == 'POST':
        try:
            answer = request.POST.get(f'question_{question.id}')
            if not answer:
                raise ValidationError('Please provide an answer to continue.')

            # Save response
            Response.objects.update_or_create(
                assessment=assessment,
                question=question,
                defaults={'answer': answer}
            )

            messages.success(request, 'Response saved successfully!')
            return redirect('assessment:question', 
                          assessment_id=assessment_id,
                          question_number=question_number + 1)

        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, 'An error occurred. Please try again.')

    # Get previous response if it exists
    previous_response = Response.objects.filter(
        assessment=assessment,
        question=question
    ).first()

    context = {
        'assessment': assessment,
        'question': question,
        'progress': progress,
        'question_number': question_number,
        'total_questions': total_questions,
        'previous_response': previous_response.answer if previous_response else None,
        'is_last_question': question_number == total_questions,
    }
    return render(request, 'assessment/question.html', context)

@login_required
def assessment_complete(request, assessment_id):
    """
    Mark assessment as complete and generate roadmap
    """
    assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)
    
    if not assessment.completion_date:
        assessment.completion_date = timezone.now()
        assessment.scores = calculate_scores(assessment)
        assessment.save()
        
        # Generate roadmap
        roadmap = generate_roadmap(assessment)
        if roadmap:
            messages.success(request, 'Assessment completed successfully! View your personalized roadmap below.')
        else:
            messages.warning(request, 'Assessment completed, but there was an issue generating your roadmap. Our team has been notified.')
    
    return redirect('roadmap:view', assessment_id=assessment_id)

@login_required
def download_pdf(request, assessment_id):
    """
    Generate and download PDF report of assessment results
    """
    assessment = get_object_or_404(Assessment, id=assessment_id, user=request.user)
    
    # Ensure assessment is complete
    if not assessment.completion_date:
        messages.error(request, 'Assessment must be completed before downloading results.')
        return redirect('assessment:question', assessment_id=assessment_id, question_number=1)

    try:
        # Generate PDF logic here (implementation details omitted for brevity)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="assessment_{assessment_id}_report.pdf"'
        # Add PDF generation code here
        return response
    except Exception as e:
        messages.error(request, 'Unable to generate PDF report. Please try again later.')
        return redirect('assessment:list')