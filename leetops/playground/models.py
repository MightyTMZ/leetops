from django.db import models
from django.conf import settings


class Rating(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=100)
    # additional analytics/ratings can be added here in the future