from django.db import models
from django.db.models import Sum
from django.core.exceptions import ValidationError
from configuration.models import *
from core.models import *

class Websites(models.Model):
    title = models.CharField(max_length=255)
    site_url = models.CharField(max_length=255)
    site_admin_url = models.CharField(max_length=255, blank=True, null=True)
    authorization_key = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    api_secret = models.CharField(max_length=255, blank=True, null=True)
    platform = models.CharField(max_length=255)
    product_synced = models.BooleanField(default=False)

class ProductWebsites(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    website = models.ForeignKey(Websites, on_delete=models.CASCADE)
    website_product_id = models.CharField(max_length=255)
    inventory_item_id = models.CharField(max_length=255, blank=True, null=True)
    website_platform_response = models.TextField(blank=True, null=True)
