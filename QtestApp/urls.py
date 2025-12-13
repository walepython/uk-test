

from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('tests/', views.test_home, name='test'),
    path("tests/", views.tests_by_chapter, name="tests_by_chapter"),
    path('test/<int:test_id>/', views.take_test, name='take_test'),
    path('faqs/', views.faqview, name='faqs'),
    # path('test/<slug:slug>/', views.take_test, name='take_test'),
    path('save-answer/', views.save_answer, name='save_answer'),
    path('test_content/', views.test_content, name='test_content'),
    path('about/', views.about_us, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('tests-by-chapter/', views.tests_by_chapter, name='tests_by_chapter'),
    path('life-in-uk-tests/', views.life_in_uk_tests, name='life_in_uk_tests'),
    path('test/<int:test_id>/results/', views.test_results, name='test_results'),
    path('save-test-score/', views.save_test_score, name='save_test_score'),
    path('study-materials/', views.study_materials, name='study_materials'),

    path('chapters/1/', views.chapter1_view, name='chapter1'),
    # Add other chapters similarly
    path('chapters/2/', views.chapter2_view, name='chapter2'),
    path('chapters/3/', views.chapter3_view, name='chapter3'),
    path('chapters/4/', views.chapter4_view, name='chapter4'),
    path('chapters/5/', views.chapter5_view, name='chapter5'),

    # Exam URLs
    path('exams/', views.exam_list, name='exam_list'),
    path('exam/<int:exam_id>/', views.take_exam, name='take_exam'),
    path('exam/<int:exam_id>/question/<int:question_number>/', views.exam_question, name='exam_question'),
    # path('exam/<int:exam_id>/results/<int:attempt_id>/', views.exam_results, name='exam_results'),
    path('save-answer/', views.save_answer, name='save_answer'),


]
