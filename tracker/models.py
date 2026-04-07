# tracker/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Expense(models.Model):
    CATEGORIES = [
        ('Food', 'Food'), ('Travel', 'Travel'), ('Books', 'Books'),
        ('Accommodation', 'Accommodation'), ('Entertainment', 'Entertainment'),
        ('Health', 'Health'), ('Shopping', 'Shopping'), ('Other', 'Other'),
    ]
    user     = models.ForeignKey(User, on_delete=models.CASCADE)
    title    = models.CharField(max_length=200)
    amount   = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORIES)
    date     = models.DateField()
    note     = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"


class Budget(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)
    limit    = models.DecimalField(max_digits=10, decimal_places=2)
    month    = models.DateField()   # always store as 1st of the month

    class Meta:
        unique_together = ('user', 'category', 'month')


class SavingsGoal(models.Model):
    user   = models.ForeignKey(User, on_delete=models.CASCADE)
    name   = models.CharField(max_length=100)
    target = models.DecimalField(max_digits=10, decimal_places=2)
    saved  = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    icon   = models.CharField(max_length=10, default='🎯')

    def __str__(self):
        return self.name
    
class Profile(models.Model):
    # Change this line from ForeignKey to OneToOneField
    user = models.OneToOneField(User, on_delete=models.CASCADE) 
    college = models.CharField(max_length=100, default="IET DAVV")
    address = models.CharField(max_length=100, default="Indore")
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Saves the Profile whenever the User is saved, with a safety check."""
    if hasattr(instance, 'profile'):
        instance.profile.save()