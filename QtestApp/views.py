import uuid
import requests
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
import json
from .forms import ContactForm
from .models import Choice, Test, Question, TestSession, UserAnswer, TestProgress, Location, ContactMessage,Exam,Answer


# Update your test_home view
def test_home(request):
    test = Test.objects.all()
    return render(request, "test_list.html",context={"tests":test})

def life_in_uk_tests(request):
    """View for Life in the UK test series"""
    tests = Test.objects.filter(
        title__icontains='Life in the UK',  # Filter by title containing "Life in the UK"
        is_active=True
    ).order_by('series_number')
    
    context = {
        'tests': tests,
        'title': 'Life in the UK Tests',
    }
    return render(request, 'life_in_the_uk.html', context)

def tests_by_chapter(request):
    chapter_filter = request.GET.get('chapter')
    
    # Get all active tests
    tests = Test.objects.filter(is_active=True).order_by('chapter', 'order', 'created_at')
    
    # Filter by chapter if selected
    if chapter_filter:
        tests = tests.filter(chapter=chapter_filter)
    
    # Get distinct chapters for the filter dropdown
    chapters = Test.objects.filter(is_active=True).values_list('chapter', flat=True).distinct().order_by('chapter')
    
    context = {
        'tests': tests,
        'chapters': chapters,
        'selected_chapter': chapter_filter,
    }
    return render(request, 'tests_by_chapter.html', context)

def take_test(request, test_id):
    test = get_object_or_404(Test, id=test_id, is_active=True)
    questions = test.questions.all()[:24]  # Ensure only 24 questions
    
    # Create or get test session
    session_id = request.session.get('test_session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        request.session['test_session_id'] = session_id
        
        # Create new session
        session = TestSession.objects.create(
            user=request.user if request.user.is_authenticated else None,
            test=test,
            session_id=session_id,
            total_questions=questions.count()
        )
        
        # Create progress tracker
        TestProgress.objects.create(session=session)
    else:
        try:
            session = TestSession.objects.get(session_id=session_id, test=test)
        except TestSession.DoesNotExist:
            session_id = str(uuid.uuid4())
            request.session['test_session_id'] = session_id
            session = TestSession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                test=test,
                session_id=session_id,
                total_questions=questions.count()
            )
            TestProgress.objects.create(session=session)
    
    return render(request, 'test.html', {
        'test': test,
        'questions': questions,
        'session': session
    })


@require_POST
# @login_required
def save_answer(request):
    try:
        data = json.loads(request.body)
        session_id = request.session.get('test_session_id')

        if not session_id:
            return JsonResponse({'error': 'No active test session'}, status=400)

        session = TestSession.objects.get(session_id=session_id)
        question = Question.objects.get(id=data['question_id'])

        choice_ids = data.get('choice_ids', [])

        if not choice_ids:
            return JsonResponse({'error': 'No choices selected'}, status=400)

        # Get selected choices (MULTIPLE SUPPORT)
        selected_choices = Choice.objects.filter(id__in=choice_ids)

        if not selected_choices.exists():
            return JsonResponse({'error': 'Invalid choices'}, status=400)

        user_answer, created = UserAnswer.objects.get_or_create(
            session=session,
            question=question
        )

        # Clear previous answers
        user_answer.selected_choices.clear()
        user_answer.selected_choices.add(*selected_choices)

        # Correct answers
        correct_choices = question.choices.filter(is_correct=True)

        # Check correctness
        if question.question_type == 'single':
            user_answer.is_correct = (
                selected_choices.count() == 1 and
                correct_choices.count() == 1 and
                selected_choices.first() in correct_choices
            )
        else:  # multiple
            user_answer.is_correct = set(selected_choices) == set(correct_choices)

        user_answer.save()

        return JsonResponse({
            'status': 'saved',
            'is_correct': user_answer.is_correct,
            'correct_choice_ids': list(correct_choices.values_list('id', flat=True)),
            'correct_answers': [c.text for c in correct_choices],
            'explanation': question.explanation or ""
        })

    except TestSession.DoesNotExist:
        return JsonResponse({'error': 'Test session not found'}, status=400)
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def test_results(request, test_id):
    test = get_object_or_404(Test, id=test_id)

    # Ensure session exists
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    # Get test session for this user/session
    test_session = get_object_or_404(TestSession, session_id=session_key, test=test)

     # Get the progress
    progress = getattr(test_session, 'progress', None)

    context = {
        "test": test,
        "total_questions": test_session.total_questions,
        'progress': progress,
        "correct_answers": test_session.correct_answers,
        "percentage_score": test_session.percentage_score,
        "time_taken": test_session.time_taken,
        "passed": test_session.passed,
    }
    

    return render(request, "test_result.html", context)

def save_test_score(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)

        test_id = data.get("test_id")
        score = int(data.get("score", 0))  # Percentage score
        correct = int(data.get("correct", 0))
        wrong = int(data.get("wrong", 0))
        total = int(data.get("total", 0))
        time_taken = data.get("time_taken", "00:00")

        if not test_id:
            return JsonResponse({"error": "Missing test_id"}, status=400)

        # Get Test
        test = get_object_or_404(Test, id=test_id)

        # Ensure session key exists
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        # Create or update TestSession
        test_session, created = TestSession.objects.get_or_create(
            session_id=session_key,
            test=test,
            defaults={
                "user": request.user if request.user.is_authenticated else None,
                "total_questions": total,
                "score": score,  # Store percentage
                "correct_answers": correct,
                "time_taken": time_taken,
                "passed": score >= 75,  # 75% passing threshold
                "is_completed": True,
                "completed_at": timezone.now()
            }
        )

        # If session already exists, update it
        if not created:
            test_session.score = score
            test_session.correct_answers = correct
            test_session.total_questions = total
            test_session.time_taken = time_taken
            test_session.passed = score >= 75
            test_session.is_completed = True
            test_session.completed_at = timezone.now()
            test_session.save()

        # Return redirect URL
        return JsonResponse({
            "redirect_url": reverse("test_results", args=[test.id])
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
def home(request):
    test = Test.objects.filter(chapter=1).first()

    return render(request, "home.html", {
        "test_id": test.id if test else None
    })

def about_us(request):
    return render(request, 'about.html')

# def contact_us(request):
#     return render(request, 'contact_us.html')


def faqview(request):
    return render(request, 'faq.html')

def study_materials(request):
    return render(request, 'study_materials.html')

def chapter1_view(request):
    
    test = Test.objects.filter(chapter=1).first()

    return render(request, "chapter1.html", {
        "test_id": test.id if test else None
    })


def chapter2_view(request):
    """View for displaying Chapter 2 content"""
    test = Test.objects.filter(chapter=1).first()

    return render(request, "chapter2.html", {
        "test_id": test.id if test else None
    })

def chapter3_view(request):
    """View for displaying Chapter 2 content"""
    test = Test.objects.filter(chapter=1).first()

    return render(request, "chapter3.html", {
        "test_id": test.id if test else None
    })

def chapter4_view(request):
    """View for displaying Chapter 2 content"""
    test = Test.objects.filter(chapter=1).first()

    return render(request, "chapter4.html", {
        "test_id": test.id if test else None
    })

def chapter5_view(request):
    """View for displaying Chapter 2 content"""
    test = Test.objects.filter(chapter=1).first()

    return render(request, "chapter5.html", {
        "test_id": test.id if test else None
    })
def test_content(request):
    return render(request, 'test_content.html')

def test_content(request):
    locations = Location.objects.all()

    toilet_icon = "<i class='fas fa-door-open' style='font-size:32px'></i>"
    wheelchair_icon = "<i class='fas fa-wheelchair' style='font-size:32px'></i>"
    dog_icon = "<i class='fas fa-dog' style='font-size:32px'></i>"

    return render(request, "test_content.html", {
        "locations": locations,
        "toilet_icon": toilet_icon,
        "wheelchair_icon": wheelchair_icon,
        "dog_icon": dog_icon,
    })


def contact_view(request):
    success = False
    error = None

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")
        terms = request.POST.get("terms")
        token = request.POST.get("g-recaptcha-response")

        # Verify reCAPTCHA
        recaptcha_url = "https://www.google.com/recaptcha/api/siteverify"
        recaptcha_data = {
            "secret": settings.RECAPTCHA_SECRET_KEY,
            "response": token
        }
        recaptcha_result = requests.post(recaptcha_url, data=recaptcha_data).json()

        if not recaptcha_result.get("success"):
            error = "reCAPTCHA failed. Please try again."

        elif not all([name, email, subject, message]):
            error = "Please fill in all required fields."

        else:
            # Save to database
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message
            )

            success = True

    return render(request, "contact.html", {
        "success": success,
        "error": error,
        "recaptcha_site_key": settings.RECAPTCHA_PUBLIC_KEY
    })

def exam_list(request):
    """List all available exams"""
    exams = Exam.objects.filter(is_published=True)
    return render(request, 'exams_list.html', {'exams': exams})

def take_exam(request, exam_id):
    """Start or continue an exam"""
    exam = get_object_or_404(Exam, id=exam_id, is_published=True)
    
    # Get or create test attempt
    if request.user.is_authenticated:
        attempt, created = TestAttempt.objects.get_or_create(
            user=request.user,
            exam=exam,
            is_completed=False
        )
    else:
        # For anonymous users, use session
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        attempt, created = TestAttempt.objects.get_or_create(
            session_id=session_id,
            exam=exam,
            is_completed=False
        )
    
    # Get all questions for this exam
    questions = exam.questions.all().prefetch_related('answers')
    
    # Create UserAnswer objects for new questions if this is a new attempt
    if created:
        for question in questions:
            UserAnswer.objects.create(
                attempt=attempt,
                question=question
            )
    
    # Get current question (first unanswered or first question)
    current_question = questions.first()
    
    # Try to find first unanswered question
    unanswered = UserAnswer.objects.filter(
        attempt=attempt,
        selected_answer__isnull=True
    ).first()
    
    if unanswered:
        current_question = unanswered.question
    
    context = {
        'exam': exam,
        'attempt': attempt,
        'current_question': current_question,
        'total_questions': exam.total_questions,
        'time_limit': exam.time_limit_minutes * 60,  # Convert to seconds
    }
    
    return render(request, 'take_exam.html', context)

def exam_question(request, exam_id, question_number):
    """Get specific question"""
    exam = get_object_or_404(Exam, id=exam_id)
    attempt = get_object_or_404(TestAttempt, id=request.GET.get('attempt_id'))
    
    try:
        question = exam.questions.get(order=question_number)
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found'}, status=404)
    
    # Get user's answer for this question
    try:
        user_answer = UserAnswer.objects.get(attempt=attempt, question=question)
        selected_answer_id = user_answer.selected_answer.id if user_answer.selected_answer else None
        is_reviewed = user_answer.is_reviewed
    except UserAnswer.DoesNotExist:
        selected_answer_id = None
        is_reviewed = False
    
    # Prepare question data
    question_data = {
        'id': question.id,
        'text': question.text,
        'order': question.order,
        'answers': [
            {
                'id': answer.id,
                'text': answer.text,
                'is_correct': answer.is_correct
            }
            for answer in question.answers.all()
        ],
        'selected_answer': selected_answer_id,
        'is_reviewed': is_reviewed,
        'total_questions': exam.questions.count()
    }
    
    return JsonResponse(question_data)
