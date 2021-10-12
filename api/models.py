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
    # I needed to add null=True
    property = models.ForeignKey(Property, on_delete=models.CASCADE, null=True)
    schedule = models.DateTimeField(default=now())
    title = models.TextField(max_length=255)
    created_at = models.DateTimeField(default=now())
    updated_at = models.DateTimeField(default=now(), null=True)
    status = models.CharField(max_length=35, default="Active")
    condition = models.CharField(
        max_length=35, default="Pending"
    )  # Pending, Overdue, Done

    def cancel(self):
        self.status = "cancelled"
        self.updated_at = now()
        self.save()

    def __str__(self):
        return f"{self.id}, {self.property_id}, {self.title}"


class Survey(models.Model):
    activity = models.OneToOneField(Activity, on_delete=models.CASCADE)
    answers = models.JSONField()
    created_at = models.DateTimeField(default=now())

    def __str__(self):
        return f"{self.id}, {self.activity_id}, {self.answers}"
