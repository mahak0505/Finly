import os
import sys
import django

sys.path.append(r'c:\Users\azamd\OneDrive\Desktop\MINOR PROJECT\files (1)\Finly')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finly_backend.settings')
django.setup()

from django.contrib.auth.models import User
from tracker.models import Expense, Budget, SavingsGoal

print("DELETING old data...")
Expense.objects.all().delete()
Budget.objects.all().delete()
SavingsGoal.objects.all().delete()

print("CREATING admin user...")
try:
    if User.objects.filter(username='admin').exists():
        admin = User.objects.get(username='admin')
        admin.set_password('admin123')
        admin.save()
        print("Admin user updated.")
    else:
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Admin user created.")
except Exception as e:
    print(f"Error creating admin: {e}")

print("Done resetting database!")
