//total spent per category
SELECT category, SUM(amount) as total_spent
FROM expenses
WHERE user_id = ?
GROUP BY category;

//budget vs actual spending
SELECT b.category, b.monthly_budget, 
       COALESCE(SUM(e.amount), 0) as spent,
       b.monthly_budget - COALESCE(SUM(e.amount), 0) as remaining
FROM budgets b
LEFT JOIN expenses e ON b.category = e.category AND b.user_id = e.user_id
WHERE b.user_id = ?
GROUP BY b.category;

//get goals for any user 
SELECT *, ROUND((current_amount * 100.0 / target_amount), 1) as progress_pct
FROM goals
WHERE user_id = ?;

//total income vs total expenses
SELECT 
    (SELECT SUM(amount) FROM income WHERE user_id = ?) as total_income,
    (SELECT SUM(amount) FROM expenses WHERE user_id = ?) as total_spent,
    (SELECT SUM(amount) FROM income WHERE user_id = ?) - 
    (SELECT SUM(amount) FROM expenses WHERE user_id = ?) as balance;