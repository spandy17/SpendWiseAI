
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Expense
from app.auth import get_current_user_id
from app.schemas import ExpenseCreate, ExpenseUpdate

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.post("/")
def create_expense(
    expense: ExpenseCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    new_expense = Expense(
        user_id=int(user_id),
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        payment_method=expense.payment_method,
        date=expense.date,
        description=expense.description
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    return {
        "message": "Expense added successfully",
        "expense_id": new_expense.id
    }


@router.get("/")
def get_expenses(
    search: str = "",
    category: str = "",
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    query = db.query(Expense).filter(
        Expense.user_id == int(user_id)
    )

    if search:
        query = query.filter(Expense.title.ilike(f"%{search}%"))

    if category:
        query = query.filter(Expense.category == category)

    expenses = query.order_by(Expense.date.desc()).all()

    return [
        {
            "id": item.id,
            "title": item.title,
            "amount": item.amount,
            "category": item.category,
            "payment_method": item.payment_method,
            "date": item.date,
            "description": item.description
        }
        for item in expenses
    ]


@router.put("/{expense_id}")
def update_expense(
    expense_id: int,
    expense: ExpenseUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    existing = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == int(user_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Expense not found")

    for key, value in expense.model_dump(exclude_unset=True).items():
        setattr(existing, key, value)

    db.commit()
    db.refresh(existing)

    return {"message": "Expense updated successfully"}


@router.delete("/{expense_id}")
def delete_expense(
    expense_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    existing = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == int(user_id)
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(existing)
    db.commit()

    return {"message": "Expense deleted successfully"}
