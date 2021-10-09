from django.db import models
from django.utils.timezone import now

# Create your models here.


class Property(models.Model):
    title = models.CharField(
        max_length=255,
    )
    address = models.TextField()
    description = models.TextField()
    created_at = models.DateTimeField(default=now())
    updated_at = models.DateTimeField(default=now())
    disabled_at = models.DateTimeField(null=True)
    status = models.CharField(max_length=35, default="Active")

    def __str__(self):
        return f"{self.id}, {self.address}, {self.description}"


class Activity(models.Model):
    property_id = models.ForeignKey(Property, on_delete=models.CASCADE)
    schedule = models.DateTimeField()
    title = models.TextField(max_length=255)
    updated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField()
    status = models.CharField(max_length=35, default="Active")

    def __str__(self):
        return f"{self.id}, {self.property_id}, {self.title}"


class Survery(models.Model):
    activity_id = models.OneToOneField(Activity, on_delete=models.CASCADE)
    answers = models.JSONField()
    created_at = models.DateTimeField()

    def __str__(self):
        return f"{self.id}, {self.activity_id}, {self.answers}"
