from django.contrib import admin
from .models import Expense, SavingsGoal, Profile,Budget
# Register your models here.

admin.site.register(Expense)
admin.site.register(SavingsGoal)
admin.site.register(Profile)
admin.site.register(Budget)