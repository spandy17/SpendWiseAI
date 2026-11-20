
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.database import get_db
from app.models import Expense, Income, Budget
from app.auth import get_current_user_id

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def to_number(value: object) -> float:
    return float(str(value)) if value is not None else 0.0


@router.get("/")
def get_dashboard(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    uid = int(user_id)
    now = datetime.now()

    # Total Income
    total_income = db.query(
        func.coalesce(func.sum(Income.amount), 0)
    ).filter(
        Income.user_id == uid
    ).scalar()

    # Total Expenses
    total_expenses = db.query(
        func.coalesce(func.sum(Expense.amount), 0)
    ).filter(
        Expense.user_id == uid
    ).scalar()

    # Recent Expenses
    recent_expenses = db.query(Expense).filter(
        Expense.user_id == uid
    ).order_by(
        Expense.date.desc()
    ).limit(5).all()

    # Expense Category Summary - All Dates
    category_summary = db.query(
        Expense.category,
        func.sum(Expense.amount).label("total")
    ).filter(
        Expense.user_id == uid
    ).group_by(
        Expense.category
    ).all()

    # Monthly Income and Expense Summary - Last 6 Months
    monthly_summary = []

    for i in range(5, -1, -1):
        month_index = now.month - i
        year = now.year

        while month_index <= 0:
            month_index += 12
            year -= 1

        start_date = datetime(year, month_index, 1)

        if month_index == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month_index + 1, 1)

        income = db.query(
            func.coalesce(func.sum(Income.amount), 0)
        ).filter(
            Income.user_id == uid,
            Income.date >= start_date,
            Income.date < end_date
        ).scalar()

        expense = db.query(
            func.coalesce(func.sum(Expense.amount), 0)
        ).filter(
            Expense.user_id == uid,
            Expense.date >= start_date,
            Expense.date < end_date
        ).scalar()

        monthly_summary.append({
            "month": start_date.strftime("%b %Y"),
            "income": to_number(income),
            "expenses": to_number(expense)
        })

    # Current Month Budget Utilization
    current_budgets = db.query(Budget).filter(
        Budget.user_id == uid,
        Budget.month == now.month,
        Budget.year == now.year
    ).all()

    budget_summary = []

    for budget in current_budgets:
        spent = db.query(
            func.coalesce(func.sum(Expense.amount), 0)
        ).filter(
            Expense.user_id == uid,
            Expense.category == budget.category,
            func.month(Expense.date) == now.month,
            func.year(Expense.date) == now.year
        ).scalar()

        spent_amount = to_number(spent)
        limit_amount = to_number(budget.limit_amount)

        percentage = (
            (spent_amount / limit_amount) * 100
            if limit_amount > 0 else 0
        )

        budget_summary.append({
            "category": budget.category,
            "limit": limit_amount,
            "spent": spent_amount,
            "remaining": limit_amount - spent_amount,
            "percentage": round(percentage, 2),
            "status": (
                "exceeded" if percentage >= 100
                else "warning" if percentage >= 80
                else "safe"
            )
        })

    return {
        "total_income": to_number(total_income),
        "total_expenses": to_number(total_expenses),
        "balance": (
            to_number(total_income) - to_number(total_expenses)
        ),

        "total_transactions": (
            db.query(Expense).filter(
                Expense.user_id == uid
            ).count()
            +
            db.query(Income).filter(
                Income.user_id == uid
            ).count()
        ),

        "recent_expenses": [
            {
                "id": item.id,
                "title": item.title,
                "amount": to_number(item.amount),
                "category": item.category,
                "date": item.date
            }
            for item in recent_expenses
        ],

        "category_summary": [
            {
                "category": category,
                "amount": to_number(amount)
            }
            for category, amount in category_summary
        ],

        "monthly_summary": monthly_summary,

        "budget_summary": budget_summary
    }
