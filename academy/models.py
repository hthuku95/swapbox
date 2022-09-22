from django.db import models

# Create your models here.

class Series(models.Model):
    title = models.CharField( max_length=255)
    description = models.TextField()
    thumnail= models.ImageField()
    cover_image = models.ImageField()
    views = models.IntegerField()

    def __str__(self):
        return self.title
    
class Lesson(models.Model):
    title = models.CharField( max_length=255)
    description = models.TextField()
    thumbnail= models.ImageField()
    series = models.ForeignKey(Series, on_delete=models.CASCADE)
    views = models.IntegerField()

    def __str__(self):
        return self.title

