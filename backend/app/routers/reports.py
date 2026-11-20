
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Expense, Income
from app.auth import get_current_user_id

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/monthly")
def monthly_report(
    month: int,
    year: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    uid = int(user_id)

    expenses = db.query(Expense).filter(
        Expense.user_id == uid,
        datetime(year, month, 1) <= Expense.date,
        Expense.date < (
            datetime(year + (month // 12), (month % 12) + 1, 1)
        )
    ).all()

    incomes = db.query(Income).filter(
        Income.user_id == uid,
        datetime(year, month, 1) <= Income.date,
        Income.date < (
            datetime(year + (month // 12), (month % 12) + 1, 1)
        )
    ).all()

    total_expenses = sum(item.amount for item in expenses)
    total_income = sum(item.amount for item in incomes)

    return {
        "month": month,
        "year": year,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": total_income - total_expenses,
        "expenses": [
            {
                "title": item.title,
                "amount": item.amount,
                "category": item.category,
                "date": item.date
            }
            for item in expenses
        ]
    }


@router.get("/csv")
def export_csv(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    uid = int(user_id)

    expenses = db.query(Expense).filter(
        Expense.user_id == uid
    ).order_by(Expense.date.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Title", "Amount", "Category",
        "Payment Method", "Date", "Description"
    ])

    for item in expenses:
        writer.writerow([
            item.title,
            item.amount,
            item.category,
            item.payment_method,
            item.date,
            item.description or ""
        ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=Expense AI_report.csv"
        }
    )
