from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path(r'',views.exam_guidance_view,name="exam-guidance"),
    path(r'instructions/<slug>/',views.exam_type_instructions_view,name="exam-instructions"),
    path(r'exam/quiz/<int:id>/',views.quiz_exam_details_view,name="quiz-details"),
    path(r'exam/takeaway/<int:id>/',views.take_away_exam_details_view,name="takeaway-details"),
    path(r'exam/quiz_view/<int:id>/',views.quiz_view,name="quiz-view"),
    path(r'exam/takeaway_view/<int:id>/',views.takeaway_view,name="takeaway-view"),
]