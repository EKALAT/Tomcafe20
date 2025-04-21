from django.db import models

# Create your models here.
from django.db import models

class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    category = models.CharField(max_length=50)
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
