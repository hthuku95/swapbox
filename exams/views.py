from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Exam,Attempt,AnswerFile,InstructionFile,Question
from accounts.models import Account
from profiles.models import UserProfile
# Create your views here.

# Removed the exam guidance/ More instructions view

@login_required()
def exam_type_instructions_view(request,slug):
    return render(request, "exams/exam_type_instructions_page.html")

# you cant go back to the previous question
@login_required()
def quiz_exam_details_view(request,id):
    return render(request, "exams/quiz_exam_details_page.html")

@login_required()
def take_away_exam_details_view(request,id):
    return render(request,"exams/take_away_exam_details_page.html")

# Only viewed from seller mode
@login_required()
def quiz_view(request,id):
    return render(request, "exams/quiz.html")

# Only viewed from seller mode
@login_required()
def takeaway_view(request,id):
    return render(request, "exams/takeaway.html")