from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError

class BookingMan(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class City(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Area(models.Model):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

