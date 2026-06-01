from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import PermissionsMixin, BaseUserManager
from django.db import models
from django.db.models import CharField, Model, TextField, TextChoices, DecimalField, ForeignKey, CASCADE, \
    SET_NULL
from django.db.models.fields import DateTimeField


# Create your models here.

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    username = None
    objects = CustomUserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []


class Category(Model):
    class OperationType(TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    name = CharField(max_length=111, null=False)
    photo_url = CharField(max_length=300)
    operation_type = CharField(max_length=10, choices=OperationType)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Operation(Model):
    class OperationType(TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    user = ForeignKey(User, on_delete=CASCADE)
    type = CharField(choices=OperationType, null=False)
    amount = DecimalField(max_digits=12, decimal_places=2)
    category = ForeignKey('apps.Category', on_delete=SET_NULL, null=True, blank=True)
    date = DateTimeField(auto_now_add=True)
    description = TextField()

    def __str__(self):
        return f"{self.user} - {self.type}"
