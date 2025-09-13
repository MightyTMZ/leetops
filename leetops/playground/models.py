from django.db import models
from django.conf import settings


class Rating(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=100)
    # additional analytics/ratings can be added here in the future


class Simulation(models.Model):
    company = models.CharField(max_length=255)
    company_avatar = models.ImageField(upload_to="company_avatars/")
    details = models.TextField()



class CompletedSimulation(models.Model):
    simulation = models.ForeignKey(Simulation, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plus_minus = models.IntegerField() # in rating
    summary = models.TextField()
