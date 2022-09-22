from django.contrib import admin
from .models import Exam, Attempt, Answer, Question, InstructionFile, AnswerFile
# Register your models here.

admin.site.register(Question)
admin.site.register(Exam)
admin.site.register(Attempt)
admin.site.register(Answer)
admin.site.register(AnswerFile)
admin.site.register(InstructionFile)