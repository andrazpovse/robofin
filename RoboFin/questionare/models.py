from django.db import models


class Question(models.Model):
    question_text = models.CharField(max_length=400)
    pub_date = models.DateTimeField('date published')

    def __str__(self):
        return self.question_text

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    choice_points = models.IntegerField(default=0)

    def __str__(self):
        return "Text: {text}\nPoints: {points}" \
            .format(text=self.choice_text, points=self.choice_points)




