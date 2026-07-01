from django.db import models
from django.contrib.auth.models import User

class Asset(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=100)
    available = models.BooleanField(default=True)
    def __str__(self):
        return self.name

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    booking_group = models.CharField(max_length=36, blank=True, default="", db_index=True)
    start_date = models.DateField()
    end_date = models.DateField()
    purpose = models.TextField()

    def __str__(self):
        return f"{self.user.username} - {self.asset.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mark the asset unavailable after a booking is saved.
        self.asset.available = False
        self.asset.save()

class UserMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    email = models.EmailField() 
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username} - {self.subject}"
