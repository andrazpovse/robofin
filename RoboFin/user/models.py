from django.db import models
from django.contrib.auth.models import User
from portfolio.models import Portfolio

class UserInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    starting_capital = models.DecimalField(max_digits=20, decimal_places=2)

    risk_score = models.IntegerField(blank=True, null=True)
    monthly_investment = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return "{username}".format(username=self.user.get_username())