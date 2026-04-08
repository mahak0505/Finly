from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '../../db/finly.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── AUTHENTICATION ─────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def login_user(request):
    try:
        data = json.loads(request.body)
        email = data.get('id')
        password = data.get('password')
        conn = get_db()
        user = conn.execute(
            'SELECT user_id, name, email, college FROM users WHERE email = ? AND password = ?',
            [email, password]
        ).fetchone()
        conn.close()
        
        if user:
            return JsonResponse({'success': True, 'user': dict(user)})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid credentials'}, status=401)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


# ─── EXPENSES ───────────────────────────────────────────

@csrf_exempt
@require_http_methods(["GET"])
def get_expenses(request, user_id):
    conn = get_db()
    expenses = conn.execute(
        'SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC', 
        [user_id]
    ).fetchall()
    conn.close()
    return JsonResponse([dict(e) for e in expenses], safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def add_expense(request):
    data = json.loads(request.body)
    conn = get_db()
    conn.execute(
        'INSERT INTO expenses (user_id, name, category, amount, date, note) VALUES (?,?,?,?,?,?)',
        [data['user_id'], data['name'], data['category'], data['amount'], data['date'], data.get('note')]
    )
    conn.commit()
    conn.close()
    return JsonResponse({'message': 'Expense added successfully'})

# ─── INCOME ─────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["GET"])
def get_income(request, user_id):
    conn = get_db()
    income = conn.execute(
        'SELECT * FROM income WHERE user_id = ? ORDER BY date DESC',
        [user_id]
    ).fetchall()
    conn.close()
    return JsonResponse([dict(i) for i in income], safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def add_income(request):
    data = json.loads(request.body)
    conn = get_db()
    conn.execute(
        'INSERT INTO income (user_id, name, category, amount, date) VALUES (?,?,?,?,?)',
        [data['user_id'], data['name'], data['category'], data['amount'], data['date']]
    )
    conn.commit()
    conn.close()
    return JsonResponse({'message': 'Income added successfully'})

# ─── BUDGETS ────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["GET"])
def get_budgets(request, user_id):
    conn = get_db()
    budgets = conn.execute(
        'SELECT * FROM monthly_summary WHERE user_id = ?',
        [user_id]
    ).fetchall()
    conn.close()
    return JsonResponse([dict(b) for b in budgets], safe=False)

# ─── GOALS ──────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["GET"])
def get_goals(request, user_id):
    conn = get_db()
    goals = conn.execute(
        'SELECT *, ROUND((current_amount * 100.0 / target_amount), 1) as progress_pct FROM goals WHERE user_id = ?',
        [user_id]
    ).fetchall()
    conn.close()
    return JsonResponse([dict(g) for g in goals], safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def add_goal(request):
    data = json.loads(request.body)
    conn = get_db()
    conn.execute(
        'INSERT INTO goals (user_id, name, target_amount, current_amount, deadline) VALUES (?,?,?,?,?)',
        [data['user_id'], data['name'], data['target_amount'], 0, data.get('deadline')]
    )
    conn.commit()
    conn.close()
    return JsonResponse({'message': 'Goal added successfully'})

# ─── DASHBOARD ──────────────────────────────────────────

@csrf_exempt
@require_http_methods(["GET"])
def get_dashboard(request, user_id):
    conn = get_db()
    total_income = conn.execute(
        'SELECT COALESCE(SUM(amount), 0) as total FROM income WHERE user_id = ?', 
        [user_id]
    ).fetchone()
    total_expenses = conn.execute(
        'SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE user_id = ?', 
        [user_id]
    ).fetchone()
    warnings = conn.execute(
        'SELECT * FROM budget_warnings WHERE user_id = ? ORDER BY warning_date DESC LIMIT 5',
        [user_id]
    ).fetchall()
    conn.close()
    return JsonResponse({
        'total_income': total_income['total'],
        'total_expenses': total_expenses['total'],
        'balance': total_income['total'] - total_expenses['total'],
        'warnings': [dict(w) for w in warnings]
    })