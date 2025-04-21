from django.db import models

# Create your models here.

class Customer(models.Model):
    name = models.CharField("ชื่อลูกค้า", max_length=100)
    phone = models.CharField("เบอร์โทรศัพท์", max_length=20, blank=True, null=True)
    email = models.EmailField("อีเมล", blank=True, null=True)
    visits = models.IntegerField("จำนวนครั้งที่มาใช้บริการ", default=1)
    created_at = models.DateTimeField("วันที่ลงทะเบียน", auto_now_add=True)
    last_visit = models.DateTimeField("เข้าใช้บริการล่าสุด", auto_now=True)
    
    class Meta:
        verbose_name = "ลูกค้า"
        verbose_name_plural = "ลูกค้า"
        ordering = ['-last_visit']
    
    def __str__(self):
        return self.name
