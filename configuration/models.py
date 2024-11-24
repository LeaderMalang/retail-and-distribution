from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sync_status=models.BooleanField(default=False)

    class Meta:
        abstract = True

class BookingMan(TimeStampMixin):
    name = models.CharField(max_length=255)
    total_sales = models.CharField(max_length=255, null=True)
    sales_commission = models.CharField(max_length=255, null=True)
    sales_target = models.CharField(max_length=255, null=True)
    targeted_month = models.CharField(max_length=255, null=True)

    def __str__(self):
        return self.name

class City(TimeStampMixin):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Area(TimeStampMixin):
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

