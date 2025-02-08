from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError

class CustomUserManager(BaseUserManager):

    def _create_user(self, username, email, password, **extra_fields):
        """Helper method to create a user"""
        if not email:
            raise ValueError("The Email field must be set")
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, password=None, **extra_fields):
        """Creates a normal user"""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", "user")
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password=None, **extra_fields):
        """Creates a superuser"""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "superadmin")

        if extra_fields.get("role") != "superadmin":
            raise ValueError('Superuser must have role="superadmin".')

        return self._create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
        ('superadmin', 'SuperAdmin')
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    department = models.CharField(max_length=100,blank=True,null=True)

    objects = CustomUserManager()

    def clean(self):
        if self.role == 'superadmin' and not (self.is_superuser and self.is_staff):
            raise ValidationError("SuperAdmin must have both is_superuser=True and is_staff=True.")
        
        if self.role == 'admin' and not self.is_staff:
            raise ValidationError("Admin must have is_staff=True.")
        
        if self.role == 'admin' and self.is_superuser:
            raise ValidationError("Admin cannot have is_superuser=True.")
        
        if self.role == 'user' and (self.is_staff or self.is_superuser):
            raise ValidationError("Regular users cannot have staff or superuser status.")

    def save(self, *args, **kwargs):
        if self.role == 'superadmin':
            self.is_staff = True
            self.is_superuser = True
        elif self.role == 'admin':
            self.is_staff = True
            self.is_superuser = False
        else:
            self.is_staff = False
            self.is_superuser = False

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} - {self.role}"

    @property
    def is_superadmin(self):
        return self.role == 'superadmin'

    @property
    def is_admin(self):
        return self.role in ['admin', 'superadmin']
    
    def has_module_perms(self, app_label):
        if self.is_superadmin:
            return True
        elif self.is_admin:
            return app_label == 'task'
        return False