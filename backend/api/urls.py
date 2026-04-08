from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_user),

    # Dashboard
    path('dashboard/<int:user_id>/', views.get_dashboard),
    
    # Expenses
    path('expenses/<int:user_id>/', views.get_expenses),
    path('expenses/add/', views.add_expense),
    
    # Income
    path('income/<int:user_id>/', views.get_income),
    path('income/add/', views.add_income),
    
    # Budgets
    path('budgets/<int:user_id>/', views.get_budgets),
    
    # Goals
    path('goals/<int:user_id>/', views.get_goals),
    path('goals/add/', views.add_goal),
]