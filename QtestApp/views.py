import uuid
import requests
from django.http import HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
import json
import random
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View
from .forms import ContactForm
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Choice, Test, Question, TestSession, UserAnswer, TestProgress, Location, ContactMessage,Exam,Answer


# Update your test_home view
def test_home(request):
    test = Test.objects.all()
    return render(request, "test_list.html",context={"tests":test})

def life_in_uk_tests(request):
    """View for Life in the UK test series"""
    tests = Test.objects.filter(
        title__icontains='Life in UK',  # Filter by title containing "Life in the UK"
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
        
        # Get all possible parameters
        attempt_id = data.get('attempt_id')
        question_id = data.get('question_id')
        answer_id = data.get('answer_id')
        choice_ids = data.get('choice_ids', [])
        is_reviewed = data.get('is_reviewed')
        
        print(f"DEBUG - Received data: {data}")
        
        # Validate required fields
        if not question_id:
            return JsonResponse({'error': 'Question ID is required'}, status=400)
        
        # Handle review flag
        if is_reviewed is not None:
            # Try to get attempt from attempt_id first, then from session
            if attempt_id:
                attempt = TestSession.objects.get(id=attempt_id)
            else:
                session_id = request.session.get('test_session_id')
                if not session_id:
                    return JsonResponse({'error': 'No active session for tests'}, status=400)
                attempt = TestSession.objects.get(session_id=session_id)
            
            question = Question.objects.get(id=question_id)
            
            user_answer, created = UserAnswer.objects.get_or_create(
                session=attempt,
                question=question
            )
            user_answer.is_marked_for_review = is_reviewed
            user_answer.save()
            
            return JsonResponse({
                'success': True,
                'is_marked_for_review': user_answer.is_marked_for_review
            })
        
        # Handle answer selection - try both exam and test scenarios
        attempt = None
        
        # Try to get attempt from attempt_id first (for exams)
        if attempt_id:
            attempt = TestSession.objects.get(id=attempt_id)
        # If no attempt_id, try to get from session (for tests)
        else:
            session_id = request.session.get('test_session_id')
            if session_id:
                attempt = TestSession.objects.get(session_id=session_id)
        
        if not attempt:
            return JsonResponse({'error': 'No active test session or exam attempt'}, status=400)
        
        question = Question.objects.get(id=question_id)
        
        # Get correct choices for this question
        correct_choices = question.choices.filter(is_correct=True)
        correct_choice_ids = list(correct_choices.values_list('id', flat=True))
        
        user_answer, created = UserAnswer.objects.get_or_create(
            session=attempt,
            question=question
        )
        
        is_correct = False
        selected_choice_ids = []
        
        # SINGLE CHOICE QUESTIONS
        if question.question_type == 'single' and answer_id:
            selected_choice = Choice.objects.get(id=answer_id)
            user_answer.selected_choice = selected_choice
            user_answer.selected_choices.clear()
            
            is_correct = selected_choice.is_correct
            selected_choice_ids = [selected_choice.id]
        
        # MULTIPLE CHOICE QUESTIONS
        elif question.question_type == 'multiple' and choice_ids:
            selected_choices = Choice.objects.filter(id__in=choice_ids)
            
            user_answer.selected_choice = None
            user_answer.selected_choices.clear()
            user_answer.selected_choices.add(*selected_choices)
            
            selected_choice_ids = list(selected_choices.values_list('id', flat=True))
            
            # Check correctness
            selected_ids_set = set(selected_choice_ids)
            correct_ids_set = set(correct_choice_ids)
            
            is_correct = (selected_ids_set == correct_ids_set and 
                        len(selected_choice_ids) == len(correct_choice_ids))
        
        # Update user answer
        user_answer.is_correct = is_correct
        user_answer.save()
        
        return JsonResponse({
            'success': True,
            'is_correct': user_answer.is_correct,
            'explanation': question.explanation or "",
            'selected_choice_ids': selected_choice_ids,
            'correct_choice_ids': correct_choice_ids,
            'correct_answers_text': [c.text for c in correct_choices]
        })
        
    except TestSession.DoesNotExist:
        return JsonResponse({'error': 'Test session/attempt not found'}, status=400)
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found'}, status=400)
    except Choice.DoesNotExist:
        return JsonResponse({'error': 'Choice not found'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def test_results(request, test_id):
    """Display test results for Test objects"""
    test = get_object_or_404(Test, id=test_id)
    
    print(f"DEBUG: Accessing results for test {test_id}, user: {request.user}")  # Debug
    
    # Get the latest completed session for this user and test
    attempt = TestSession.objects.filter(
        test=test,
        is_completed=True
    ).order_by('-completed_at').first()
    
    # For anonymous users, try to get by session key
    if not attempt and not request.user.is_authenticated:
        session_key = request.session.session_key
        if session_key:
            attempt = TestSession.objects.filter(
                session_id__contains=session_key,  # Partial match for session-based IDs
                test=test,
                is_completed=True
            ).order_by('-completed_at').first()
    
    if not attempt:
        print(f"DEBUG: No TestSession found for test {test_id}")  # Debug
        # Redirect back to test or show error
        return render(request, 'QtestApp/no_results.html', {
            'test': test,
            'error': 'No test results found. Please complete the test first.'
        })
    
    print(f"DEBUG: Found TestSession ID: {attempt.id}")  # Debug
    
    context = {
        'test': test,
        'attempt': attempt,
        'total_questions': attempt.total_questions or test.questions.count(),
        'correct_answers': attempt.correct_answers or 0,
        'percentage_score': attempt.score or 0,
        'time_taken': attempt.time_taken or "00:00",
        'passed': attempt.passed,
    }
    
    return render(request, 'test_result.html', context)

@csrf_exempt
def save_test_score(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        data = json.loads(request.body)
        test_id = data.get("test_id")
        score = int(data.get("score", 0))
        correct = int(data.get("correct", 0))
        total = int(data.get("total", 0))
        time_taken = data.get("time_taken", "00:00")
        
        print(f"DEBUG: Received test_id: {test_id}, score: {score}, correct: {correct}, total: {total}")  # Debug

        if not test_id:
            return JsonResponse({"error": "Missing test_id"}, status=400)

        test = get_object_or_404(Test, id=test_id)
        
        # Get or create user
        user = request.user if request.user.is_authenticated else None
        
        # Generate unique session ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # Create TestSession
        test_session = TestSession.objects.create(
            session_id=session_id,
            test=test,
            user=user,
            total_questions=total,
            score=score,
            correct_answers=correct,
            time_taken=time_taken,
            passed=score >= 75,
            is_completed=True,
            completed_at=timezone.now()
        )
        
        print(f"DEBUG: Created TestSession with ID: {test_session.id}, Session ID: {session_id}")  # Debug

        return JsonResponse({
            "success": True,
            "redirect_url": reverse("test_results", args=[test.id]),
            "session_id": session_id  # Return the session ID for debugging
        })

    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        import traceback
        print(f"Error in save_test_score: {e}")
        print(traceback.format_exc())
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

def privacy(request):
    return render(request, 'privacy.html')

def term_and_condition(request):
    return render(request, 'terms_and_condition.html')

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

@login_required
def take_exam(request, exam_id):
    """Display exam interface"""
    exam = get_object_or_404(Exam, id=exam_id)
    
    # First, check if there's an existing incomplete session
    attempt = TestSession.objects.filter(
        user=request.user,
        exam=exam,
        is_completed=False  # Changed from 'completed' to 'is_completed'
    ).first()
    
    if attempt:
        # Update the existing session
        attempt.started_at = timezone.now()
        attempt.save()
    else:
        # Create a new session with a unique session_id
        try:
            # Generate unique session ID
            import time
            unique_session_id = f"exam_{exam_id}_{request.user.id}_{uuid.uuid4()}"
            
            attempt = TestSession.objects.create(
                user=request.user,
                exam=exam,
                session_id=unique_session_id,
                started_at=timezone.now(),
                is_completed=False
            )
            
        except IntegrityError as e:
            # If there's still a duplicate, try with timestamp
            unique_session_id = f"exam_{exam_id}_{request.user.id}_{uuid.uuid4()}_{int(time.time())}"
            
            attempt = TestSession.objects.create(
                user=request.user,
                exam=exam,
                session_id=unique_session_id,
                started_at=timezone.now(),
                is_completed=False
            )
    
    # Get user's answers to show status
    user_answers = UserAnswer.objects.filter(session=attempt)
    
    # Separate correct, review, and incorrect questions
    correct_questions = []
    review_questions = []
    incorrect_questions = []
    
    for user_answer in user_answers:
        if user_answer.is_marked_for_review:
            review_questions.append(user_answer.question.order)
        else:
            # Check if answer is correct
            correct_choices = set(user_answer.question.choices.filter(is_correct=True).values_list('id', flat=True))
            user_choices = set(user_answer.selected_choices.values_list('id', flat=True))
            
            if user_answer.question.question_type == 'multiple':
                is_correct = correct_choices == user_choices
            else:
                is_correct = len(user_choices) == 1 and list(user_choices)[0] in correct_choices
            
            if is_correct:
                correct_questions.append(user_answer.question.order)
            else:
                incorrect_questions.append(user_answer.question.order)
    
    context = {
        'exam': exam,
        'attempt': attempt,
        'total_questions': exam.questions.count(),
        'time_limit': exam.time_limit_minutes * 60,  # Convert to seconds
        'correct_answers': correct_questions,
        'review_answers': review_questions,
        'incorrect_answers': incorrect_questions,
    }
    
    return render(request, 'take_exam.html', context)

def exam_question(request, exam_id, question_number):
    """Get specific question"""
    exam = get_object_or_404(Exam, id=exam_id)
    attempt = get_object_or_404(TestSession, id=request.GET.get('attempt_id'))
    
    try:
        question = exam.questions.get(order=question_number)
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Question not found'}, status=404)
    
    # Get user's answer for this question
    selected_choice_id = None
    selected_choice_ids = []
    is_reviewed = False
    
    try:
        user_answer = UserAnswer.objects.get(session=attempt, question=question)
        is_reviewed = user_answer.is_marked_for_review
        
        # Get selected answers based on question type
        if question.question_type == 'single':
            # FIXED: Use selected_choices instead of selected_choice
            # Get the first selected choice for single answer questions
            if user_answer.selected_choices.exists():
                selected_choice = user_answer.selected_choices.first()
                selected_choice_id = int(selected_choice.id)
        else:  # multiple choice
            # Get all selected choices from ManyToMany field
            selected_choice_ids = list(user_answer.selected_choices.values_list('id', flat=True))
                
    except UserAnswer.DoesNotExist:
        pass  # Use default values
    
    # Get all choices for this question
    choices = question.choices.all()
    
    # Prepare question data
    question_data = {
        'id': int(question.id),
        'text': str(question.text),
        'order': int(question.order),
        'question_type': str(question.question_type),
        'explanation': str(question.explanation) if question.explanation else "",
        'answers': [
            {
                'id': int(choice.id),
                'text': str(choice.text),
                'is_correct': bool(choice.is_correct)
            }
            for choice in choices
        ],
        'selected_answer': selected_choice_id,  # For single choice
        'selected_answers': selected_choice_ids,  # For multiple choice
        'is_reviewed': bool(is_reviewed),
        'total_questions': int(exam.questions.count())
    }
    
    return JsonResponse(question_data)


def exam_results(request, exam_id, attempt_id):
    """Display exam results"""
    exam = get_object_or_404(Exam, id=exam_id)
    attempt = get_object_or_404(TestSession, id=attempt_id, user=request.user)
    
    # Mark exam as completed if not already
    if not attempt.is_completed:
        attempt.is_completed = True
        attempt.completed_at = timezone.now()
        
        # Calculate results
        user_answers = UserAnswer.objects.filter(session=attempt).select_related('question')
        total_questions = exam.questions.count()
        correct_count = 0
        
        for user_answer in user_answers:
            if hasattr(user_answer, 'is_correct'):
                # Try accessing as field first
                try:
                    if user_answer.is_correct:  # No parentheses for field
                        correct_count += 1
                except:
                    # If it's a method
                    if user_answer.is_correct():  # With parentheses for method
                        correct_count += 1
        
        # Update the attempt
        attempt.correct_answers = correct_count
        attempt.total_questions = total_questions
        
        # Calculate score and passed status
        if total_questions > 0:
            score_percentage = (correct_count / total_questions) * 100
            attempt.score = int(score_percentage)
            attempt.passed = score_percentage >= 75
        
        attempt.save()
    
    # Calculate time taken
    time_taken = "00:00"
    if attempt.started_at and attempt.completed_at:
        duration = attempt.completed_at - attempt.started_at
        minutes = int(duration.total_seconds() // 60)
        seconds = int(duration.total_seconds() % 60)
        time_taken = f"{minutes:02d}:{seconds:02d}"
    
    context = {
        'exam': exam,
        'attempt': attempt,
        'total_questions': attempt.total_questions or 0,
        'correct_answers': attempt.correct_answers or 0,  # Changed from correct_count
        'incorrect_count': (attempt.total_questions or 0) - (attempt.correct_answers or 0),
        'percentage_score': attempt.score or 0,  # Changed from score to percentage_score
        'score': attempt.score or 0,
        'passed': attempt.passed or False,
        'passing_score': 75,
        'time_taken': time_taken,  # Added this
        'user_answers': UserAnswer.objects.filter(session=attempt).select_related('question', 'selected_choices'),
    }
    
    return render(request, 'exam_results.html', context) 


def mark_exam_completed(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        attempt_id = data.get('attempt_id')
        
        try:
            attempt = TestSession.objects.get(id=attempt_id, user=request.user)
            attempt.completed = True
            attempt.end_time = timezone.now()
            attempt.save()
            return JsonResponse({'success': True})
        except TestSession.DoesNotExist:
            return JsonResponse({'error': 'Exam attempt not found'}, status=404)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
    
def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )

        messages.success(request, "Account created successfully")
        return redirect("login")

    return render(request, "register.html")


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect("login")

@login_required(login_url="login")
def dashboard(request):
    return render(request, "dashboard.html")




def admin_only_view(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("You are not allowed here")
    return render(request, "admin.html")


class QuickTestView(TemplateView):
    """View to start a quick test"""
    template_name = 'quick_test_start.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # You can add any initial context here
        return context

class QuickTestQuestionsView(View):
    def get(self, request):
        questions = Question.objects.order_by('?')[:5]
        questions_data = []

        for question in questions:
            choices = question.choices.all()
            correct_count = choices.filter(is_correct=True).count()

            # Auto-detect type if needed
            question_type = (
                'multiple' if correct_count > 1 else 'single'
            )

            question_data = {
                'id': question.id,
                'text': question.text,
                'question_type': question_type,
                'explanation': question.explanation or "",
                'choices': [
                    {
                        'id': c.id,
                        'text': c.text,
                        'is_correct': c.is_correct
                    }
                    for c in choices
                ]
            }

            questions_data.append(question_data)

        return JsonResponse({
            'questions': questions_data,
            'total_questions': len(questions_data)
        })


@method_decorator(csrf_exempt, name='dispatch')
class SubmitQuickTestView(View):
    """View to submit and evaluate quick test answers"""
    
    def post(self, request):
        import json
        data = json.loads(request.body)
        user_answers = data.get('answers', {})
        
        results = []
        total_correct = 0
        total_questions = len(user_answers)
        
        for question_id, answer_data in user_answers.items():
            try:
                question = Question.objects.get(id=int(question_id))
                is_correct = False
                
                if question.question_type == 'multiple':
                    user_choice_ids = [int(cid) for cid in answer_data]

                    correct_choice_ids = list(
                        question.choices.filter(is_correct=True)
                        .values_list('id', flat=True)
                    )

                    is_correct = set(user_choice_ids) == set(correct_choice_ids)

                else:
                    user_choice_id = int(answer_data)

                    correct_choice_id = (
                        question.choices
                        .filter(is_correct=True)
                        .values_list('id', flat=True)
                        .first()
                    )

                    is_correct = user_choice_id == correct_choice_id
               
                if is_correct:
                    total_correct += 1
                
                results.append({
                    'question_id': question.id,
                    'question_text': question.text,
                    'is_correct': is_correct,
                    'explanation': question.explanation
                })
                
            except (Question.DoesNotExist, ValueError):
                continue
        
        score_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        return JsonResponse({
            'results': results,
            'total_correct': total_correct,
            'total_questions': total_questions,
            'score_percentage': round(score_percentage, 2),
            'passed': score_percentage >= 50  # 75% passing threshold
        })
