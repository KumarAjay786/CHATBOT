# chat/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """User model with email as primary identifier instead of username."""

    username = None
    email = models.EmailField(_('email address'), unique=True)
    chat_preferences = models.JSONField(
        default=dict,
        help_text="User preferences for chatbot interactions"
    )
    last_chat_activity = models.DateTimeField(
        auto_now=True,
        help_text="Last time user interacted with chatbot"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class Conversation(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200, blank=True)

    def save(self, *args, **kwargs):
        """Auto-generate title from first message if not provided"""
        if not self.title and not self.pk:
            first_message = self.messages.first()
            if first_message:
                self.title = f"{first_message.content[:50]}..."
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Conversation {self.id} - {self.user.email}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        related_name='messages',
        on_delete=models.CASCADE
    )
    content = models.TextField()
    is_user = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(
        default=dict,
        help_text="Additional context about the message"
    )

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
        ]

    def __str__(self):
        prefix = "User" if self.is_user else "AI"
        return f"{prefix}: {self.content[:20]}..."
