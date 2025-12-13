from django.contrib import admin
from .models import Test, Question, Choice, TestSession, UserAnswer, TestProgress, Location, ContactMessage, Exam, Answer

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    min_num = 2

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ['title', 'total_questions', 'time_limit_minutes', 'is_published']
    inlines = [QuestionInline]

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['title', 'question_count', 'time_limit_minutes', 'is_active', 'order', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'test', 'question_type', 'order', 'created_at']
    list_filter = ['test', 'question_type', 'created_at']
    search_fields = ['text']
    inlines = [ChoiceInline]
    ordering = ['test', 'order']

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['text', 'question', 'is_correct', 'order']
    list_filter = ['is_correct', 'question__test']
    search_fields = ['text', 'question__text']
    list_editable = ['is_correct', 'order']

@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'test', 'user', 'score', 'total_questions', 'is_completed', 'started_at']
    list_filter = ['is_completed', 'test', 'started_at']
    readonly_fields = ['session_id', 'started_at']
    search_fields = ['session_id', 'user__username']

# This is the FIRST UserAnswer registration
@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ['session', 'question', 'is_correct', 'is_marked_for_review', 'answered_at']
    list_filter = ['is_correct', 'is_marked_for_review', 'answered_at']
    search_fields = ['session__session_id', 'question__text']

@admin.register(TestProgress)
class TestProgressAdmin(admin.ModelAdmin):
    list_display = ['session', 'current_question_index']
    readonly_fields = ['session']

# Remove or comment out the Answer model if you're not using it
# Or if you have both Answer and Choice models, keep only one
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['text', 'question', 'is_correct', 'order']

# Remove these commented lines as they're causing confusion
# @admin.register(TestAttempt)
# class TestAttemptAdmin(admin.ModelAdmin):
#     list_display = ['user', 'exam', 'start_time', 'is_completed', 'score']

# COMMENT OUT OR REMOVE THIS DUPLICATE - this is the problem
# @admin.register(UserAnswer)
# class UserAnswerAdmin(admin.ModelAdmin):
#     list_display = ['attempt', 'question', 'selected_answer', 'is_correct', 'is_reviewed']

admin.site.register(Location)
admin.site.register(ContactMessage)