from django.db import models
from authentication1.models import usertable


class UserAddress(models.Model):
    address_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(usertable, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=100, null=False)
    phone_number = models.CharField(max_length=15, null=False)
    address_line1 = models.CharField(max_length=255, null=False)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, null=False)
    state = models.CharField(max_length=100, null=False)
    postal_code = models.CharField(max_length=20, null=False)
    country = models.CharField(max_length=100, null=False)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.city}, {self.state}, {self.country}"





    