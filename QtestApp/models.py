from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone



class Test(models.Model):
    TEST_CATEGORIES = [
        ('chapter', 'Chapter Tests'),
        ('life_in_uk', 'Life in the UK Tests'),
        ('practice', 'Practice Tests'),
    ]
    category = models.CharField(max_length=20, choices=TEST_CATEGORIES, default='chapter')
    is_featured = models.BooleanField(default=False,null=True, blank=True)
    series_number = models.IntegerField(default=0, help_text="Test number in the series")
    title = models.CharField(max_length=200,null=True, blank=True)
    description = models.TextField(blank=True)
    chapter = models.IntegerField(default=True,null=True, blank=True)
    slug = models.SlugField(unique=True,null=True, blank=True)
    time_limit_minutes = models.IntegerField(default=45)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    order = models.IntegerField(default=0,null=True, blank=True)  # For ordering tests
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
       if self.category == 'life_in_uk':
            return f"Life in the UK Test {self.series_number}"
       elif self.category == 'chapter':
            return f"Chapter {self.chapter} - {self.title}"
       else:
            return self.title
    
    @property
    def question_count(self):
        return self.questions.count()

class Exam(models.Model):
    title = models.CharField(max_length=200,blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    time_limit_minutes = models.IntegerField(default=45,blank=True, null=True)
    total_questions = models.IntegerField(default=24,blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    order = models.IntegerField(default=0,blank=True, null=True)  # For ordering exams
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return self.title


class Question(models.Model):
    QUESTION_TYPES = [
        ('single', 'Single Choice'),
        ('multiple', 'Multiple Choice'),
    ]
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions',blank=True, null=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions',null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    explanation = models.TextField(blank=True, help_text="Explanation for the correct answer")
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES, default='single',null=True, blank=True)
    order = models.IntegerField(default=0,null=True, blank=True)  # For ordering questions within a test
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.text[:100]}..."  # Show first 100 characters

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers',blank=True, null=True)
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0,blank=True, null=True)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.text[:50]}... ({'✓' if self.is_correct else '✗'})"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices',null=True, blank=True)
    text = models.CharField(max_length=300,null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0,null=True, blank=True)  # For ordering choices
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        question_id = self.question.id if self.question else "?"
        text = self.text or "No choice text"
        return f"Q{question_id}: {text[:50]}"

class TestSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='sessions', null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0, null=True, blank=True)  # This should be the percentage score
    total_questions = models.IntegerField(default=24, null=True, blank=True)  # Only keep one field
    correct_answers = models.IntegerField(default=0, null=True, blank=True)
    time_taken = models.CharField(max_length=10, blank=True, null=True)
    passed = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    time_spent_seconds = models.IntegerField(default=0, null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Session {self.session_id} - {self.test.title}"
    
    @property
    def percentage_score(self):
        if self.total_questions > 0:
            return (self.correct_answers / self.total_questions) * 100
        return 0
    
    @property
    def is_passed(self):
        return self.percentage_score >= 75

class UserAnswer(models.Model):
    session = models.ForeignKey(TestSession, on_delete=models.CASCADE, related_name='user_answers',null=True, blank=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE,null=True, blank=True)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)
    selected_choices = models.ManyToManyField(Choice)
    is_correct = models.BooleanField(default=False)
    is_marked_for_review = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    
    class Meta:
        ordering = ['answered_at']
        unique_together = ['session', 'question']  # One answer per question per session
    
    def __str__(self):
        return f"Answer for Q{self.question.id} in {self.session.session_id}"

class TestProgress(models.Model):
    session = models.OneToOneField(TestSession, on_delete=models.CASCADE, related_name='progress',null=True, blank=True)
    current_question_index = models.IntegerField(default=0,null=True, blank=True)
    marked_questions = models.JSONField(default=list,null=True, blank=True)  # Store question IDs marked for review
    answered_questions = models.JSONField(default=list,null=True, blank=True)  # Store question IDs that are answered
    
    def __str__(self):
        return f"Progress for {self.session.session_id}"
    
    def get_current_question(self):
        questions = list(self.session.test.questions.all())
        if self.current_question_index < len(questions):
            return questions[self.current_question_index]
        return None
    
    def mark_question_for_review(self, question_id):
        if question_id not in self.marked_questions:
            self.marked_questions.append(question_id)
            self.save()
    
    def unmark_question_for_review(self, question_id):
        if question_id in self.marked_questions:
            self.marked_questions.remove(question_id)
            self.save()
    
    def is_question_marked_for_review(self, question_id):
        return question_id in self.marked_questions


class Location(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField()
    lat = models.FloatField()
    lng = models.FloatField()

    has_toilet = models.BooleanField(default=False,blank=True, null=True)
    has_wheelchair = models.BooleanField(default=False,blank=True, null=True)
    has_dog = models.BooleanField(default=False,blank=True, null=True)

    def __str__(self):
        return self.name

from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField()
    agree_to_terms = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Message from {self.name} on {self.submitted_at.strftime('%Y-%m-%d')}"