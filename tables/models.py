from django.db import models

# Create your models here.
from django.db import models

class Table(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('unavailable', 'Unavailable'),
    )
    
    number = models.IntegerField(unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    capacity = models.IntegerField(default=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Table {self.number}"
