from django.db import models
from accounts.models import Account
from profiles.models import UserProfile
# Create your models here.

EXAM_TYPE_CHOICES = (
    ('TA','Take Away'),
    ('QA','Question and Answer'),
)

class Answer(models.Model):
    answer = models.TextField()

    def __str__(self):
        return self.answer
    
class Question(models.Model):
    question = models.TextField()
    answers = models.ManyToManyField(Answer, blank=True)
    correct_answer = models.ForeignKey(Answer, on_delete=models.CASCADE,related_name="correct_answer")

    def __str__(self):
        return self.question
 
    # Answers
    # Correct Answer
    # Can only have a total of four answers including the correct answer

class InstructionFile(models.Model):
    instruction_file = models.FileField(blank=True, null=True)

    def __str__(self):
        return self.id

class Exam(models.Model):
    title = models.CharField(blank=True,null=True, max_length=200)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    # The top scorer is the one who gets to buy the account
    total_number_of_student_slots = models.IntegerField(default=0)
    exam_type = models.CharField(choices=EXAM_TYPE_CHOICES,blank=True, max_length=2)
    questions = models.ManyToManyField(Question, blank=True)

    # if type == QA:
    no_of_questions = models.IntegerField(default=0)
    # it will be updated to true once the examiner finishes uploading the questions
    completed = models.BooleanField(default=False)

    # if type == TA:
    instructions = models.TextField(blank=True,null=True)
    instruction_files = models.ManyToManyField(InstructionFile, blank=True)
    

    def __str__(self):
        return self.title

class AnswerFile(models.Model):
    answer_file = models.FileField(blank=True, null=True)

    def __str__(self):
        return self.id
    

class Attempt(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    score = models.FloatField()
    passed = models.BooleanField(default=False)

    # if the exam.type == QA : the timer is 30mins
    timer = models.IntegerField(default=1000)
    answers = models.ManyToManyField(Answer, blank=True)
    # Completed questions
    completed_questions = models.ManyToManyField(Question, blank=True)

    # if exam.type == TA:
    answer_files = models.ManyToManyField(AnswerFile, blank=True)


    def __str__(self):
        return self.passed
    
    

