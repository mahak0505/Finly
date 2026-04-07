# tracker/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Avg
from datetime import datetime, timedelta
import json
from .models import Expense, SavingsGoal, Budget, Profile
from decimal import Decimal,InvalidOperation


# ─────────────────────────────────────────────
#  LANDING PAGE
# ─────────────────────────────────────────────
def landing(request):
    """
    Root page — shows finly-landing.html
    If user is already logged in, skip straight to dashboard
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'finly-landing.html')


# ─────────────────────────────────────────────
#  AUTH — LOGIN / SIGNUP / LOGOUT
# ─────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return render(request, 'finly-landing.html', {'show_login': True})

    return redirect('landing')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username  = request.POST.get('username', '').strip()
        email     = request.POST.get('email', '').strip()
        password  = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if password != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'finly-landing.html', {'show_signup': True})

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'finly-landing.html', {'show_signup': True})

        user = User.objects.create_user(username, email, password)
        login(request, user)
        return redirect('dashboard')

    return redirect('landing')


def logout_view(request):
    logout(request)
    return redirect('landing')


# ─────────────────────────────────────────────
#  DASHBOARD
# ─────────────────────────────────────────────
@login_required(login_url='/')
def dashboard(request):
    user = request.user
    today = timezone.now().date()
    first_day = today.replace(day=1)

    # expenses this month
    monthly_expenses = Expense.objects.filter(
        user=user,
        date__gte=first_day,
        date__lte=today
    )

    # last month for comparison
    last_month_start = (first_day - timedelta(days=1)).replace(day=1)
    last_month_expenses = Expense.objects.filter(
        user=user,
        date__gte=last_month_start,
        date__lt=first_day
    )

    total_spent      = monthly_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    last_month_total = last_month_expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    # savings
    savings_goals = SavingsGoal.objects.filter(user=user)
    total_savings = savings_goals.aggregate(Sum('saved'))['saved__sum'] or 0

    # budget remaining
    budgets = Budget.objects.filter(user=user, month=first_day)
    total_budget = budgets.aggregate(Sum('limit'))['limit__sum'] or 0
    budget_remaining = total_budget - total_spent

    # daily average
    days_passed = (today - first_day).days + 1
    daily_avg = round(total_spent / days_passed, 2) if days_passed else 0

    # spending by category (for pie / bar chart)
    by_category = monthly_expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    # spending trend — last 30 days (for line chart)
    thirty_days_ago = today - timedelta(days=29)
    trend_raw = Expense.objects.filter(
        user=user, date__gte=thirty_days_ago
    ).values('date').annotate(total=Sum('amount')).order_by('date')

    trend_labels = [str(entry['date']) for entry in trend_raw]
    trend_data   = [float(entry['total']) for entry in trend_raw]

    # recent transactions
    recent_transactions = Expense.objects.filter(user=user).order_by('-date', '-id')[:10]

    # % change vs last month
    if last_month_total:
        change_pct = round(((total_spent - last_month_total) / last_month_total) * 100, 1)
    else:
        change_pct = 0

    context = {
        'total_spent'         : total_spent,
        'total_savings'       : total_savings,
        'budget_remaining'    : budget_remaining,
        'daily_avg'           : daily_avg,
        'by_category'         : list(by_category),
        'trend_labels'        : json.dumps(trend_labels),
        'trend_data'          : json.dumps(trend_data),
        'recent_transactions' : recent_transactions,
        'savings_goals'       : savings_goals,
        'change_pct'          : change_pct,
        'days_left'           : (first_day.replace(month=first_day.month % 12 + 1) - today).days,
        'today'               : today,
    }
    return render(request, 'dashboard.html', context)


# ─────────────────────────────────────────────
#  EXPENSES
# ─────────────────────────────────────────────
@login_required(login_url='/')
def expenses_view(request):
    user = request.user

    if request.method == 'POST':
        title    = request.POST.get('title')
        amount   = request.POST.get('amount')
        category = request.POST.get('category')
        date     = request.POST.get('date') or timezone.now().date()
        note     = request.POST.get('note', '')

        Expense.objects.create(
            user=user, title=title, amount=amount,
            category=category, date=date, note=note
        )
        messages.success(request, 'Expense added!')
        return redirect('expenses')

    category_filter = request.GET.get('category', '')
    month_filter    = request.GET.get('month', '')
    search          = request.GET.get('search', '')

    expenses = Expense.objects.filter(user=user).order_by('-date', '-id')

    if category_filter:
        expenses = expenses.filter(category=category_filter)
    if month_filter:
        year, month = month_filter.split('-')
        expenses = expenses.filter(date__year=year, date__month=month)
    if search:
        expenses = expenses.filter(title__icontains=search)

    total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0

    categories = Expense.objects.filter(user=user).values_list(
        'category', flat=True
    ).distinct()

    context = {
        'expenses'        : expenses,
        'total'           : total,
        'categories'      : categories,
        'category_filter' : category_filter,
        'month_filter'    : month_filter,
        'search'          : search,
    }
    return render(request, 'expenses.html', context)


@login_required(login_url='/')
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    expense.delete()
    messages.success(request, 'Expense deleted.')
    return redirect('expenses')


@login_required(login_url='/')
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    if request.method == 'POST':
        expense.title    = request.POST.get('title')
        expense.amount   = request.POST.get('amount')
        expense.category = request.POST.get('category')
        expense.date     = request.POST.get('date')
        expense.note     = request.POST.get('note', '')
        expense.save()
        messages.success(request, 'Expense updated!')
    return redirect('expenses')


# ─────────────────────────────────────────────
#  BUDGET GOALS
# ─────────────────────────────────────────────
@login_required(login_url='/')
def budget_goals_view(request):
    user = request.user
    today = timezone.now().date()
    first_day = today.replace(day=1)

    if request.method == 'POST':
        category = request.POST.get('category')
        limit    = request.POST.get('limit')
        Budget.objects.update_or_create(
            user=user, category=category, month=first_day,
            defaults={'limit': limit}
        )
        messages.success(request, 'Budget saved!')
        return redirect('budget_goals')

    budgets = Budget.objects.filter(user=user, month=first_day)

    budget_data = []
    for b in budgets:
        spent = Expense.objects.filter(
            user=user, category=b.category,
            date__gte=first_day, date__lte=today
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        budget_data.append({
            'budget'  : b,
            'spent'   : spent,
            'percent' : min(round((spent / b.limit) * 100), 100) if b.limit else 0,
            'left'    : max(b.limit - spent, 0),
        })

    context = {
        'budget_data' : budget_data,
        'month'       : first_day,
    }
    return render(request, 'budget-goals.html', context)


@login_required(login_url='/')
def delete_budget(request, budget_id):
    budget = get_object_or_404(Budget, id=budget_id, user=request.user)
    budget.delete()
    messages.success(request, 'Budget deleted.')
    return redirect('budget_goals')


# ─────────────────────────────────────────────
#  SAVINGS
# ─────────────────────────────────────────────
@login_required(login_url='/')
def savings_view(request):
    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            name   = request.POST.get('name')
            target = request.POST.get('target')
            icon   = request.POST.get('icon', '🎯')
            
            # Use Decimal for target to match the model
            try:
                target_val = Decimal(target) if target else Decimal('0')
                SavingsGoal.objects.create(user=user, name=name, target=target_val, icon=icon)
                messages.success(request, 'Goal created!')
            except (InvalidOperation, ValueError):
                messages.error(request, 'Invalid target amount.')

        elif action == 'add_funds':
            goal_id = request.POST.get('goal_id')
            amount_str = request.POST.get('amount', '0')
            
            if goal_id and amount_str:
                goal = get_object_or_404(SavingsGoal, id=goal_id, user=user)
                try:
                    # Convert input string to Decimal instead of float
                    amount = Decimal(amount_str)
                    
                    # Both values are now Decimals, so addition works perfectly
                    goal.saved = min(goal.saved + amount, goal.target)
                    goal.save()
                    messages.success(request, f'₹{amount} added to {goal.name}!')
                except (InvalidOperation, ValueError):
                    messages.error(request, 'Please enter a valid numeric amount.')

        elif action == 'delete':
            goal_id = request.POST.get('goal_id')
            goal = get_object_or_404(SavingsGoal, id=goal_id, user=user)
            goal.delete()
            messages.success(request, 'Goal deleted.')

        return redirect('savings')

    # GET request logic
    goals = SavingsGoal.objects.filter(user=user)
    total_saved  = goals.aggregate(Sum('saved'))['saved__sum'] or Decimal('0')
    total_target = goals.aggregate(Sum('target'))['target__sum'] or Decimal('0')

    goals_data = []
    for g in goals:
        goals_data.append({
            'goal': g,
            # Ensure division uses the same types
             # Convert to float so 500/1000 becomes 0.5 instead of 0
            'percent': min(round((float(g.saved) / float(g.target)) * 100), 100) if g.target else 0
        })

    context = {
        'goals_data': goals_data,
        'total_saved': total_saved,
        'total_target': total_target,
    }
    return render(request, 'savings.html', context)

# ─────────────────────────────────────────────
#  ANALYTICS
# ─────────────────────────────────────────────
@login_required(login_url='/')
def analytics_view(request):
    user = request.user
    today = timezone.now().date()

    monthly_data = []
    for i in range(5, -1, -1):
        month_date = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        total = Expense.objects.filter(
            user=user,
            date__year=month_date.year,
            date__month=month_date.month
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        monthly_data.append({
            'month': month_date.strftime('%b %Y'),
            'total': float(total)
        })

    by_category = Expense.objects.filter(user=user).values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    top_days = Expense.objects.filter(user=user).values('date').annotate(
        total=Sum('amount')
    ).order_by('-total')[:5]

    avg_daily = Expense.objects.filter(user=user).values('date').annotate(
        total=Sum('amount')
    ).aggregate(Avg('total'))['total__avg'] or 0

    context = {
        'monthly_labels' : json.dumps([m['month'] for m in monthly_data]),
        'monthly_data'   : json.dumps([m['total'] for m in monthly_data]),
        'by_category'    : list(by_category),
        'top_days'       : top_days,
        'avg_daily'      : round(avg_daily, 2),
    }
    return render(request, 'analytics.html', context)


# ─────────────────────────────────────────────
#  AI ADVISOR
# ─────────────────────────────────────────────
@login_required(login_url='/')
def ai_advisor_view(request):
    user = request.user
    today = timezone.now().date()
    first_day = today.replace(day=1)

    monthly_expenses = Expense.objects.filter(user=user, date__gte=first_day)
    total_spent = monthly_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    by_category = monthly_expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    context = {
        'total_spent' : total_spent,
        'by_category' : list(by_category),
    }
    return render(request, 'ai-advisor.html', context)


# ─────────────────────────────────────────────
#  INSIGHTS
# ─────────────────────────────────────────────
@login_required(login_url='/')
def insights_view(request):
    user = request.user
    today = timezone.now().date()
    first_day = today.replace(day=1)

    monthly = Expense.objects.filter(user=user, date__gte=first_day)
    top_category = monthly.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total').first()

    this_week_start = today - timedelta(days=today.weekday())
    last_week_start = this_week_start - timedelta(days=7)

    this_week = Expense.objects.filter(
        user=user, date__gte=this_week_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    last_week = Expense.objects.filter(
        user=user, date__gte=last_week_start, date__lt=this_week_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'top_category' : top_category,
        'this_week'    : this_week,
        'last_week'    : last_week,
        'week_change'  : round(this_week - last_week, 2),
    }
    return render(request, 'insights.html', context)


# ─────────────────────────────────────────────
#  PROFILE  ← single merged definition
# ─────────────────────────────────────────────
@login_required(login_url='/')
def profile_view(request):
    user = request.user

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name',  user.last_name)
        user.email      = request.POST.get('email',      user.email)
        user.save()

        # Keep Profile fields in sync
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.college = request.POST.get('college', profile.college)
        profile.address = request.POST.get('address', profile.address)
        profile.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    total_expenses = Expense.objects.filter(user=user).count()
    total_spent    = Expense.objects.filter(user=user).aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    context = {
        'total_expenses' : total_expenses,
        'total_spent'    : total_spent,
    }
    return render(request, 'profile.html', context)


# ─────────────────────────────────────────────
#  SETTINGS  ← single merged definition
# ─────────────────────────────────────────────
@login_required(login_url='/')
def settings_view(request):
    user = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'change_password':
            old_pw  = request.POST.get('old_password')
            new_pw  = request.POST.get('new_password')
            confirm = request.POST.get('confirm_password')
            if not user.check_password(old_pw):
                messages.error(request, 'Old password is incorrect.')
            elif new_pw != confirm:
                messages.error(request, 'New passwords do not match.')
            else:
                user.set_password(new_pw)
                user.save()
                messages.success(request, 'Password changed! Please log in again.')
                return redirect('login')

        elif action == 'delete_account':
            user.delete()
            return redirect('landing')

        elif action == 'update_profile':
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name  = request.POST.get('last_name',  user.last_name)
            user.email      = request.POST.get('email',      user.email)
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.college = request.POST.get('college', profile.college)
            profile.address = request.POST.get('address', profile.address)
            profile.save()

            messages.success(request, 'Settings updated successfully!')

        return redirect('settings')

    return render(request, 'settings.html')


# ─────────────────────────────────────────────
#  STATIC / INFO PAGES  (no login needed)
# ─────────────────────────────────────────────
def features_view(request):
    return render(request, 'features.html')

def pricing_view(request):
    return render(request, 'pricing.html')

def about_view(request):
    return render(request, 'about.html')

def help_view(request):
    return render(request, 'help.html')

def help_center_view(request):
    return render(request, 'help-center.html')

def privacy_view(request):
    return render(request, 'privacy.html')

def security_view(request):
    return render(request, 'security.html')

def terms_view(request):
    return render(request, 'terms.html')

def blog_view(request):
    return render(request, 'blog.html')

def careers_view(request):
    return render(request, 'careers.html')

def changelog_view(request):
    return render(request, 'changelog.html')

def contact_view(request):
    return render(request, 'contact.html')
    