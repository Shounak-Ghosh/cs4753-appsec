import django
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.backends import BaseBackend
from django.utils.encoding import force_str
django.utils.encoding.force_text = force_str
from fernet_fields import EncryptedField
from . import extras
import hashlib

# Create your models here.
class User(AbstractBaseUser):
    username = models.CharField(max_length=30, unique=True)
    password = models.CharField(max_length=97)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['password']

class OurBackend(BaseBackend):
    def authenticate(self, request, username, password):
        assert(None not in [username, password])
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        pwrd_valid = extras.check_password(user, password)
        if pwrd_valid:
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=50, unique=True)
    product_image_path = models.CharField(max_length=100, unique=True)
    recommended_price = models.IntegerField()
    description = models.CharField(max_length=250)

class Card(models.Model):
    id = models.AutoField(primary_key=True)
    # data = models.BinaryField(unique=True)
    data = EncryptedField()
    data_hash = models.CharField(max_length=64, unique=True, blank=True, null=True)
    product = models.ForeignKey('LegacySite.Product', on_delete=models.CASCADE, default=None)
    amount = models.IntegerField()
    fp = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey('LegacySite.User', on_delete=models.CASCADE)
    used = models.BooleanField(default=False)

    # Override default save method to hash data field before saving
    def save(self, *args, **kwargs):
        if self.data and isinstance(self.data, bytes): # Ensure data is bytes for hashing
            self.data_hash = hashlib.sha256(self.data).hexdigest()
        super().save(*args, **kwargs)
